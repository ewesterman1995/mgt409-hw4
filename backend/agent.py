"""Campus Customs chat agent: entry point and wiring.

The agent is built from three pieces:
  - prompts/prompt.md  - the system prompt (voice + rules)
  - tools.py           - the tools it can call (AGENT_TOOLS)
  - the model          - the course model through Portkey, configured in .env

main.py calls run_chat() for every message from the chat widget. Every step of the
agent loop is appended to output/audit_trail.json (Problem 12).
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")  # keep the server log readable

from openai import AsyncOpenAI  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from pydantic_ai import Agent, ModelRetry, NativeOutput, RunContext, UsageLimits  # noqa: E402
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded  # noqa: E402
from pydantic_ai.messages import (  # noqa: E402
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIChatModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402

import tools  # noqa: E402
from models import (  # noqa: E402
    MAX_HISTORY_TURNS,
    AgentReply,
    AuditEntry,
    AuditEvent,
    ChatReply,
    ChatTurn,
    ProductCard,
    SeeMore,
)

BACKEND_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"

DEFAULT_BASE_URL = "https://api.portkey.ai/v1"
DEFAULT_MODEL = "gpt-5.6-luna"

# Hard limits per chat message, so a runaway loop or a "write me an essay" request
# can't burn tokens. Normal messages use 1-2 model calls and about 7-10k tokens.
USAGE_LIMITS = UsageLimits(request_limit=4, tool_calls_limit=6, total_tokens_limit=40_000)
MAX_REPLY_TOKENS = 800  # normal replies are about 100-200 tokens
TOO_BIG_REPLY = (
    "Sorry, that request was too big for me to handle in one go. Could you ask about "
    "one product or kind of item at a time?"
)


# ---------------------------------------------------------------------------
# Audit trail: output/audit_trail.json (Problem 12)
# ---------------------------------------------------------------------------
# Append-only: every step of every chat message is added to the end of a JSON list.
# Records are never edited or removed; if the file can't be read it is set aside
# under a new name instead of being overwritten.

AUDIT_PATH = BACKEND_DIR.parent / "output" / "audit_trail.json"
AUDIT_TIMEZONE = ZoneInfo("America/New_York")
_audit_lock = threading.Lock()


def _short(text: Any, limit: int = 160) -> str | None:
    if text is None:
        return None
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _append_audit(entry: AuditEntry) -> None:
    with _audit_lock:
        records: list[Any] = []
        if AUDIT_PATH.exists():
            try:
                records = json.loads(AUDIT_PATH.read_text(encoding="utf-8") or "[]")
                if not isinstance(records, list):
                    raise ValueError("audit file is not a JSON list")
            except ValueError:
                stamp = datetime.now(AUDIT_TIMEZONE).strftime("%Y%m%d-%H%M%S")
                AUDIT_PATH.rename(AUDIT_PATH.with_name(f"audit_trail.unreadable-{stamp}.json"))
                records = []
        records.append(entry.model_dump())
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        temp = AUDIT_PATH.with_suffix(".tmp")
        temp.write_text(json.dumps(records, indent=1, ensure_ascii=False), encoding="utf-8")
        temp.replace(AUDIT_PATH)


class AuditRun:
    """Audit records for one chat message."""

    def __init__(self, shopper: str) -> None:
        self.run_id = uuid.uuid4().hex[:12]
        self.shopper = shopper
        self.seq = 0

    def record(self, event: AuditEvent, **fields: Any) -> None:
        self.seq += 1
        try:
            _append_audit(AuditEntry(
                run_id=self.run_id,
                seq=self.seq,
                time=datetime.now(AUDIT_TIMEZONE).isoformat(timespec="seconds"),
                event=event,
                shopper=self.shopper,
                **fields,
            ))
        except OSError:
            pass  # never let a logging problem break the chat


def summarize_result(value: Any) -> str | None:
    """A short, readable summary of what a tool returned."""
    if isinstance(value, list):
        names = [getattr(v, "name", None) for v in value]
        named = [n for n in names if n]
        return _short(f"{len(value)} result(s)" + (": " + ", ".join(named[:4]) if named else ""))
    if isinstance(value, BaseModel):
        data = value.model_dump()
        if "overall" in data:  # catalogue_summary
            o = data["overall"]
            return _short(f"{o['product_count']} products, ${o['min_price']:.2f}-${o['max_price']:.2f}")
        if "sizes" in data:  # check_stock
            sizes = ", ".join(f"{s['size']} {s['status']}" for s in data["sizes"])
            return _short(f"{data['name']}: {sizes}")
        if "price" in data:  # get_product_details
            return _short(f"{data['name']}: ${data['price']:.2f}")
        return _short(json.dumps(data))
    return _short(value)


class AgentNotConfigured(RuntimeError):
    """Raised when the API key is missing, so main.py can explain instead of crashing."""


def build_model() -> OpenAIChatModel:
    """The course model, reached through Portkey's OpenAI-compatible API."""
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise AgentNotConfigured("PORTKEY_API_KEY is not set in .env")
    client = AsyncOpenAI(api_key=api_key, base_url=os.getenv("PORTKEY_BASE_URL", DEFAULT_BASE_URL))
    model_name = os.getenv("PORTKEY_MODEL", DEFAULT_MODEL)
    return OpenAIChatModel(model_name, provider=OpenAIProvider(openai_client=client))


def build_agent(model=None) -> Agent[tools.ChatDeps, AgentReply]:
    agent = Agent(
        model or build_model(),
        deps_type=tools.ChatDeps,
        # Structured output: the reply text plus the product_ids to show as cards.
        # NativeOutput = the model answers in JSON mode instead of calling a "final_result"
        # tool. With the tool version this model always made an extra tool call first, so
        # even "where is your store?" took two model calls; now it takes one (Problem 9).
        output_type=NativeOutput(AgentReply),
        # `instructions` (not `system_prompt`) so the prompt is sent on every turn;
        # PydanticAI skips `system_prompt` whenever message history is passed in.
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        tools=tools.AGENT_TOOLS,
        retries=2,
    )

    @agent.output_validator
    def check_ids(ctx: RunContext[tools.ChatDeps], output: AgentReply) -> AgentReply:
        """Reject product ids or a collection slug that don't exist, so the model has to fix them."""
        unknown = tools.unknown_product_ids(ctx.deps, output.product_ids)
        if unknown:
            raise ModelRetry(
                f"These product_ids don't exist: {unknown}. Use exact ids from find_products results."
            )
        if output.collection_slug and tools.get_collection(ctx.deps, output.collection_slug) is None:
            raise ModelRetry(
                f"No collection has slug {output.collection_slug!r}. Use a slug from list_collections, or null."
            )
        missing = tools.missing_low_stock_notes(ctx.deps, output.product_ids, output.reply)
        if missing:
            raise ModelRetry(
                "Your reply talks about stock but leaves out sizes that are running low. "
                f"Mention these too, in these words: {missing}."
            )
        return output

    @agent.instructions
    def shopper_context(ctx: RunContext[tools.ChatDeps]) -> str:
        """Added to the prompt on every message: who the shopper is and what page they're on."""
        return describe_shopper_context(ctx.deps)

    return agent


def describe_shopper_context(deps: tools.ChatDeps) -> str:
    customer = deps.customer
    if customer and customer.logged_in:
        who = (
            f"The shopper is logged in as {customer.first_name} {customer.last_name} "
            f"({customer.email}). Your conversation with them is saved to their account."
        )
    else:
        who = "The shopper is a guest (not logged in). You don't know their name; don't ask for personal details."

    page = deps.page
    if page is None:
        where = "You don't know which page they're on."
    elif page.product_id:
        where = (
            f"They are on {page.description} (product_id: {page.product_id}). If they say "
            '"this", "it" or "this one" without naming a product, they mean this product: '
            "use this product_id directly with get_product_details or check_stock, no search needed."
        )
    else:
        where = f"They are on {page.description}."
    context = f"## Current shopper and page\n\n{who}\n\n{where}"

    if deps.presearch:
        found = "\n".join(m.model_dump_json() for m in deps.presearch)
        context += (
            "\n\n## Already looked up for this message\n\n"
            "These products were just read from the live database (same data find_products "
            "returns) because they match this message or the page the shopper is on. If they "
            "answer the question, reply directly and do not call find_products again. If they "
            "don't fit what the shopper asked, search with find_products as usual.\n\n" + found
        )
    return context


# Built on the first chat message rather than at import, so the rest of the site
# still runs when the API key hasn't been added yet.
_agent: Agent[tools.ChatDeps, AgentReply] | None = None


def get_agent() -> Agent[tools.ChatDeps, AgentReply]:
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


def to_message_history(history: list[ChatTurn]) -> list[ModelMessage]:
    """Convert the widget's earlier turns into PydanticAI's message format."""
    messages: list[ModelMessage] = []
    for turn in history[-MAX_HISTORY_TURNS:]:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


FILTERED_REPLY = (
    "Sorry, I can't help with that. I'm here to help you find Campus Customs gear. "
    "Ask me about our collections, or browse the Products page."
)


def is_content_filtered(error: Exception) -> bool:
    """True when the model provider's safety filter blocked the request."""
    body = getattr(error, "body", None)
    return isinstance(body, dict) and body.get("code") == "content_filter"


# What the chat shows while the agent works (Problem 9: live progress).
# Database lookups take milliseconds; the waiting is in the model calls before and
# after them, so the step after a lookup says what was found.
TOOL_STATUS = {
    "find_products": ("Searching our products…", "Found matching products."),
    "get_product_details": ("Looking up product details…", "Got the product details."),
    "check_stock": ("Checking live stock…", "Checked live stock."),
    "list_collections": ("Browsing our collections…", "Looked up our collections."),
    "get_customer_profile": ("Checking your account…", "Checked your account."),
    "catalogue_summary": ("Counting our whole catalogue…", "Counted the whole catalogue."),
}


def _ms(start: float) -> int:
    return round((time.perf_counter() - start) * 1000)


async def run_chat(
    message: str,
    history: list[ChatTurn],
    deps: tools.ChatDeps,
    on_status: Callable[[str], None] | None = None,
    on_preview: Callable[[list[ProductCard]], None] | None = None,
    shopper: str = "guest",
) -> ChatReply:
    """Run one chat turn, recording every step in the audit trail.

    - `on_status` (optional) is called with a short progress message each time the
      agent starts a step, e.g. "Checking live stock…".
    - `on_preview` (optional) is called right away, before the model runs, with the
      best pre-searched product's card, so the chat can show it instantly.
    - `shopper` is "guest" or "user:<id>" for the audit trail.
    """
    status = on_status or (lambda _text: None)
    audit = AuditRun(shopper)
    run_start = time.perf_counter()
    audit.record(
        "run_started",
        args=_short(message, 120),
        result=f"page: {deps.page.path}" if deps.page else None,
    )

    # Pre-search (milliseconds): products this message is clearly about, with live
    # price and stock, so the model can usually answer in one call instead of two.
    step_start = time.perf_counter()
    deps.presearch = tools.presearch(deps, message)
    audit.record(
        "presearch",
        tool_name="presearch",
        result=summarize_result(deps.presearch),
        duration_ms=_ms(step_start),
    )
    if deps.presearch and on_preview:
        on_preview(tools.load_product_cards(deps, [deps.presearch[0].product_id]))

    try:
        done = ""  # what the last lookup did, e.g. "Checked live stock."
        if deps.presearch:
            status("Found matching products. Writing your answer…")
        else:
            status("Reading your message…")
        async with get_agent().iter(
            message,
            deps=deps,
            message_history=to_message_history(history),
            usage_limits=USAGE_LIMITS,
            model_settings={"max_tokens": MAX_REPLY_TOKENS},
        ) as run:
            async for node in run:
                if Agent.is_model_request_node(node):
                    # Results of the tools from the previous step, and validator rejections.
                    for part in node.request.parts:
                        if isinstance(part, ToolReturnPart):
                            audit.record("tool_result", tool_name=part.tool_name,
                                         result=summarize_result(part.content), stop_reason="returned")
                        elif isinstance(part, RetryPromptPart):
                            audit.record("validation_retry", tool_name=part.tool_name,
                                         result=_short(part.model_response()),
                                         stop_reason="sent back to the model to fix")
                    if done:
                        # Back to the model with the lookup results: the longest wait.
                        status(f"{done} Writing your answer…")
                    step_start = time.perf_counter()
                elif Agent.is_call_tools_node(node):
                    response = node.model_response
                    calls = [p for p in response.parts if isinstance(p, ToolCallPart)]
                    for call in calls:
                        audit.record("model_call", tool_name=call.tool_name,
                                     args=_short(json.dumps(call.args_as_dict())),
                                     stop_reason="tool call", duration_ms=_ms(step_start),
                                     input_tokens=response.usage.input_tokens,
                                     output_tokens=response.usage.output_tokens)
                    if not calls:
                        audit.record("model_call", result="final answer",
                                     stop_reason=response.finish_reason or "stop",
                                     duration_ms=_ms(step_start),
                                     input_tokens=response.usage.input_tokens,
                                     output_tokens=response.usage.output_tokens)
                    tools_called = [c.tool_name for c in calls if c.tool_name in TOOL_STATUS]
                    for name in tools_called:
                        status(TOOL_STATUS[name][0])
                    if tools_called:
                        done = TOOL_STATUS[tools_called[-1]][1]
        result = run.result
    except UsageLimitExceeded as error:
        audit.record("run_finished", result=TOO_BIG_REPLY, stop_reason=f"usage limit: {_short(error, 120)}",
                     duration_ms=_ms(run_start))
        return ChatReply(reply=TOO_BIG_REPLY)
    except ModelHTTPError as error:
        # The provider's filter blocks things like jailbreak attempts before the
        # model sees them. Treat that as a polite refusal, not a server error.
        if is_content_filtered(error):
            audit.record("run_finished", result=FILTERED_REPLY, stop_reason="blocked by content filter",
                         duration_ms=_ms(run_start))
            return ChatReply(reply=FILTERED_REPLY)
        audit.record("error", result=_short(error), stop_reason="model call failed", duration_ms=_ms(run_start))
        raise
    except Exception as error:
        audit.record("error", result=_short(error), stop_reason="run failed", duration_ms=_ms(run_start))
        raise

    # The model only chose which products to show; every card field comes from the database.
    output = result.output
    cards = tools.load_product_cards(deps, output.product_ids)
    usage = result.usage() if callable(result.usage) else result.usage
    audit.record(
        "run_finished",
        result=_short(f"{output.reply} [{len(cards)} card(s)]"),
        stop_reason="completed",
        duration_ms=_ms(run_start),
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
    )
    return ChatReply(reply=output.reply, products=cards, see_more=build_see_more(deps, output, cards))


def build_see_more(deps: tools.ChatDeps, output: AgentReply, cards: list[ProductCard]) -> SeeMore | None:
    """The button under the chat's best-match card. Counts come from the database.

    - Whole-collection question: "Shop all 19 in Residential Colleges →", opening the collection.
    - Otherwise, when there's more than the best match: "See 7 more hoodies →", opening
      a page with exactly the products the agent picked.
    """
    if output.collection_slug and cards:
        collection = tools.get_collection(deps, output.collection_slug)
        if collection and collection.product_count > 1:
            return SeeMore(
                text=f"Shop all {collection.product_count} in {collection.name} →",
                href=f"/products?collection={collection.slug}",
            )
    more = len(cards) - 1
    if more < 1:
        return None
    label = output.more_label.strip() or "styles"
    if more == 1:
        label = label.removesuffix("s")  # "Architecture pieces" -> "Architecture piece"
    return SeeMore(
        text=f"See {more} more {label} →",
        href="/products?ids=" + ",".join(quote(c.product_id) for c in cards),
    )
