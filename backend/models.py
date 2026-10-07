"""Pydantic/PydanticAI structured types for the Campus Customs backend."""

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


def _clean_email(value: str) -> str:
    email = value.strip().lower()
    if not EMAIL_PATTERN.match(email):
        raise ValueError("Enter a valid email address.")
    return email


# --- Accounts (Problem 4) ---

class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank.")
        return value

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        return _clean_email(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        if len(value) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        return value


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: str = Field(max_length=128)

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, value: str) -> str:
        if len(value) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"New password must be at least {MIN_PASSWORD_LENGTH} characters.")
        return value


class AccountOut(BaseModel):
    """The My Account page: only real data the store has about the shopper."""

    first_name: str
    last_name: str
    email: str
    member_since: str = Field(description="When the account was created (YYYY-MM-DD).")
    saved_messages: int = Field(description="How many chat messages are saved to the account.")
    last_chat_at: str | None = Field(default=None, description="When they last chatted (YYYY-MM-DD HH:MM), if ever.")


class UserOut(BaseModel):
    """What the front end is allowed to see about a user. Never the password hash."""

    id: int
    first_name: str
    last_name: str
    email: str


# --- Chat (Problem 5) ---

MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY_TURNS = 20


class ChatTurn(BaseModel):
    """One earlier message in the conversation, as the chat widget shows it."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class ChatRequest(BaseModel):
    """What the chat widget sends to POST /api/chat."""

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)
    history: list[ChatTurn] = Field(
        default_factory=list,
        description="Earlier turns in this conversation, oldest first (guests only; for "
        f"logged-in shoppers the saved history is used). Only the last {MAX_HISTORY_TURNS} "
        "are passed to the agent.",
    )
    page: str | None = Field(
        default=None,
        max_length=500,
        description="The page the shopper is on, path + query, e.g. '/products/yale-dad-hoodie'.",
    )

    @field_validator("message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be blank.")
        return value


MAX_CARDS = 8


class ProductCard(BaseModel):
    """A product the website shows as a clickable card (links to /products/<product_id>).
    Every field is read from the database by code; the model never writes these."""

    product_id: str
    name: str
    price: float
    image_url: str = Field(description="URL of the product photo, e.g. /images/basic-hoodie-big-yale.jpg.")
    garment_type: str
    short_description: str = Field(description="First sentence of the catalogue description, shortened.")


class AgentReply(BaseModel):
    """The agent's structured output: its message plus which products to show."""

    reply: str = Field(description="Your message to the shopper, in plain text.")
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=MAX_CARDS,
        description=(
            "product_id values of the products to show the shopper as cards, best match first. "
            "Use exact ids returned by find_products in this conversation. Include them whenever "
            "the shopper is looking for or asking about products; leave empty otherwise."
        ),
    )
    more_label: str = Field(
        default="",
        max_length=30,
        description=(
            "Short plural name for this group of products, used on the button "
            "'See <N> more <more_label>', e.g. 'hoodies', 'Dad styles', 'Branford pieces', "
            "'hockey picks'. 1-3 words ending in a countable plural (not 'gear' or 'merch'). "
            "Lowercase except proper nouns; no numbers or prices. Empty if "
            "you're showing only one product."
        ),
    )
    collection_slug: str | None = Field(
        default=None,
        description=(
            "Set this only when the shopper is asking about a whole collection (e.g. residential "
            "college gear, grad school gear, Yale Athletics, family gifts): the collection's "
            "`slug` from list_collections. The button then opens that whole collection instead "
            "of just the cards you picked. Otherwise leave it null."
        ),
    )


class SeeMore(BaseModel):
    """The button under the chat's best-match card that opens a page with more products."""

    text: str = Field(description="Button text, e.g. 'See 7 more hoodies →'.")
    href: str = Field(description="Site link it opens, e.g. '/products?ids=a,b,c'.")


class ChatReply(BaseModel):
    """What POST /api/chat returns to the chat widget."""

    reply: str = Field(description="The assistant's message to the shopper.")
    products: list[ProductCard] = Field(
        default_factory=list,
        description="Product cards, best match first. Built by code from the database using "
        "the agent's product_ids, so names, prices and images can't be made up.",
    )
    see_more: SeeMore | None = Field(
        default=None,
        description="Button to more products, built by code (counts come from the database). "
        "Null when there's nothing more to show.",
    )


class ChatHistoryMessage(BaseModel):
    """One saved message, as GET /api/chat/history returns it to the chat widget."""

    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    see_more: SeeMore | None = None


# --- Customer memory (Problem 8) ---

class CustomerProfile(BaseModel):
    """Who the agent is talking to. Built by the backend from the login cookie,
    never from anything the browser sends."""

    logged_in: bool = Field(description="False for guests; then the other fields are null.")
    first_name: str | None = Field(default=None, description="Use it to greet the shopper.")
    last_name: str | None = None
    email: str | None = Field(
        default=None, description="The shopper's account email. Only mention it if they ask."
    )


class PageContext(BaseModel):
    """The page the shopper is looking at, resolved by the backend from the database."""

    path: str = Field(description="Page address, e.g. '/products/yale-dad-hoodie'.")
    description: str = Field(description="Plain-language description, e.g. 'the product page for Yale Dad Hoodie'.")
    product_id: str | None = Field(
        default=None, description="Set on a product page: the product shown, usable with get_product_details/check_stock."
    )
    product_name: str | None = None
    collection_name: str | None = Field(default=None, description="Set when browsing one collection.")


# --- Tool results ---

class CollectionInfo(BaseModel):
    """One shopping collection, as returned by the list_collections tool."""

    slug: str = Field(description="Identifier used in links, e.g. 'colleges'.")
    name: str = Field(description="Display name, e.g. 'Residential Colleges'.")
    product_count: int = Field(description="How many products are in this collection.")


class ProductRef(BaseModel):
    """A product named in a catalogue summary."""

    product_id: str
    name: str
    price: float


class CategorySummary(BaseModel):
    """Totals for one kind of garment (or the whole shop), computed by Python from the
    live database, never estimated."""

    category: str = Field(description="e.g. 'Hoodies', or 'All products' for the whole shop.")
    product_count: int = Field(description="Exact number of products of this kind in the catalogue.")
    in_stock_count: int = Field(description="How many of them have at least one size in stock right now.")
    min_price: float = Field(description="Lowest price of this kind.")
    max_price: float = Field(description="Highest price of this kind.")
    cheapest: list[ProductRef] = Field(description="Products at the lowest price (up to 3 listed).")
    cheapest_count: int = Field(description="How many products share the lowest price.")
    most_expensive: list[ProductRef] = Field(description="Products at the highest price (up to 3 listed).")
    most_expensive_count: int = Field(description="How many products share the highest price.")


class CatalogueSummary(BaseModel):
    """Whole-catalogue facts from catalogue_summary, computed from the live database."""

    overall: CategorySummary = Field(description="The whole shop.")
    by_category: list[CategorySummary] = Field(description="One entry per kind of garment.")


class ProductMatch(BaseModel):
    """One search hit from find_products, read live from the database. Includes price and
    which sizes are in stock so common questions need no second lookup (Problem 9)."""

    product_id: str = Field(description="Exact id to pass to get_product_details or check_stock.")
    name: str = Field(description="Product name to show the shopper.")
    garment_type: str = Field(description="Kind of garment, e.g. 'pullover hoodie'.")
    colors: list[str] = Field(description="Colors that appear on this one design (not color options).")
    price: float = Field(description="Price in US dollars from the catalogue. Quote it exactly.")
    stock_by_size: dict[str, str] = Field(
        description="What to tell the shopper about each size, XS to XXL: 'in stock', 'only N left' "
        "(5 or fewer) or 'out of stock'. Use these words."
    )
    exact_counts: dict[str, int] = Field(
        description="Exact units per size. Only use these if the shopper asks how many are left."
    )
    available_sizes: list[str] = Field(description="Sizes with at least 1 in stock right now.")
    sold_out_sizes: list[str] = Field(description="Sizes with 0 in stock right now. Say clearly they're out of stock.")
    low_stock: list[str] = Field(
        description="Sizes running low (5 or fewer left), ready to say, e.g. 'only 2 left in S'. "
        "You must mention every one of these when you talk about this product's stock or sizes."
    )


class ProductDetails(BaseModel):
    """Full catalogue record for one product, from get_product_details."""

    product_id: str = Field(description="Exact catalogue id.")
    name: str = Field(description="Product name.")
    garment_type: str = Field(description="Kind of garment.")
    description: str = Field(description="Catalogue description. Quote or paraphrase it; don't add details.")
    colors: list[str] = Field(description="Colors that appear on this one design (not color options).")
    price: float = Field(description="Price in US dollars, exactly as stored. Quote it as-is.")
    collection: str = Field(description="Which shop collection it belongs to, e.g. 'Residential Colleges'.")


class SizeStock(BaseModel):
    """Units on hand for one size."""

    size: str = Field(description="One of XS, S, M, L, XL, XXL.")
    status: str = Field(
        description="What to tell the shopper: 'in stock', 'only N left' (5 or fewer) or 'out of stock'. Use these words."
    )
    quantity: int = Field(description="Exact units. Only use this if the shopper asks how many are left.")
    in_stock: bool = Field(description="False when quantity is 0. Say clearly that this size is out of stock.")


class StockReport(BaseModel):
    """Live stock for one product, from check_stock."""

    product_id: str = Field(description="Exact catalogue id.")
    name: str = Field(description="Product name.")
    sizes: list[SizeStock] = Field(
        description="Stock per size, smallest to largest. Only the requested size if one was asked for."
    )
    sold_out_sizes: list[str] = Field(description="Sizes with 0 in stock (across all sizes).")
    available_sizes: list[str] = Field(description="Sizes with at least 1 in stock (across all sizes).")
    low_stock: list[str] = Field(
        description="Sizes running low (5 or fewer left), ready to say, e.g. 'only 2 left in S'. "
        "You must mention every one of these when you talk about this product's stock or sizes."
    )


# --- Audit trail (Problem 12) ---

AuditEvent = Literal[
    "run_started", "presearch", "model_call", "tool_result", "validation_retry", "run_finished", "error",
]


class AuditEntry(BaseModel):
    """One step of the agent loop, appended to output/audit_trail.json. Every record has
    every field; fields that don't apply to an event are null."""

    run_id: str = Field(description="Shared by every record from one chat message.")
    seq: int = Field(description="Order of this record within its run, starting at 1.")
    time: str = Field(description="When the step finished (ISO 8601, New York time).")
    event: AuditEvent = Field(description="Which step of the loop this record is.")
    shopper: str = Field(description="'guest' or 'user:<id>'. Never a name, email or password.")
    tool_name: str | None = Field(default=None, description="Tool called (or 'presearch').")
    args: str | None = Field(default=None, description="Short tool arguments or message preview.")
    result: str | None = Field(default=None, description="Short result summary, not the full output.")
    stop_reason: str | None = Field(default=None, description="Why this step or the run ended.")
    duration_ms: int | None = Field(default=None, description="How long the step or run took.")
    input_tokens: int | None = Field(default=None, description="Model input tokens (model calls / run total).")
    output_tokens: int | None = Field(default=None, description="Model output tokens (model calls / run total).")
