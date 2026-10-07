"""Tools the Campus Customs agent can call.

Each tool reads the shop database through ChatDeps (see agent.py), so answers
come from real data rather than the model's memory. The database is opened
read-only: the chatbot can look things up but never change anything.

Problem 5: list_collections.
Problem 6: find_products, get_product_details, check_stock.
Problem 7: load_product_cards / unknown_product_ids turn the agent's chosen
product_ids into database-backed product cards (not agent tools; agent.py calls them).
Problem 8: ChatDeps carries the logged-in customer and the current page;
get_customer_profile tool; resolve_page builds the page context.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from pydantic_ai import ModelRetry, RunContext

from models import (
    MAX_CARDS,
    CatalogueSummary,
    CategorySummary,
    CollectionInfo,
    CustomerProfile,
    PageContext,
    ProductCard,
    ProductDetails,
    ProductMatch,
    ProductRef,
    SizeStock,
    StockReport,
)

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# Ways shoppers say sizes -> the size codes stored in the inventory table.
SIZE_ALIASES = {
    "xs": "XS", "extra small": "XS", "x small": "XS", "xsmall": "XS",
    "s": "S", "small": "S", "sm": "S",
    "m": "M", "medium": "M", "med": "M",
    "l": "L", "large": "L", "lg": "L",
    "xl": "XL", "extra large": "XL", "x large": "XL", "xlarge": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx large": "XXL", "double xl": "XXL", "2x": "XXL",
}

# Words that appear in nearly every product or carry no meaning for search.
STOPWORDS = {
    "a", "an", "and", "the", "for", "of", "in", "with", "do", "you", "have", "any",
    "is", "it", "my", "me", "i", "your", "some", "yale", "shirt", "please",
    # Generic shopping words: they match "college apparel"-style tags on random
    # products and narrow the results to the wrong ones.
    "apparel", "clothing", "clothes", "adult", "gear", "merch", "merchandise", "item",
    "items", "something", "stuff", "options", "gift", "gifts", "university",
}

# Shopper wording -> wording used in the catalogue.
SYNONYMS = {
    "tee": "t", "tees": "t", "tshirt": "t", "hoody": "hoodie", "hoodies": "hoodie",
    "sweatshirts": "sweatshirt", "crewnecks": "crewneck", "jackets": "jacket",
    "quarter": "1 4", "quarterzip": "1 4 zip", "grey": "gray",
}

MAX_SEARCH_RESULTS = MAX_CARDS

# Same cutoff as the product page: exact counts are only shown when stock is low.
LOW_STOCK = 5


def stock_status(quantity: int) -> str:
    """How to describe one size's stock to a shopper."""
    if quantity == 0:
        return "out of stock"
    if quantity <= LOW_STOCK:
        return f"only {quantity} left"
    return "in stock"


def low_stock_notes(counts) -> list[str]:
    """Ready-to-say notes for sizes running low, e.g. 'only 2 left in S'. Python picks them
    so the bot can't forget a low size or recite a big count."""
    return [f"only {q} left in {size}" for size, q in counts if 0 < q <= LOW_STOCK]


STOCK_WORDS = ("stock", "sold out", "available", "sizes")
# Longer lists of cards are browsing answers; don't force a size rundown for every one.
LOW_STOCK_CHECK_MAX = 2


def missing_low_stock_notes(deps: "ChatDeps", product_ids: list[str], reply: str) -> list[str]:
    """Low-stock notes the reply should have mentioned but didn't. Only checked when the reply
    talks about stock, so a plain price answer isn't forced to list sizes. A backstop for
    prompt rule "only N left: always say it" (Problem 12)."""
    text = reply.lower()
    if not product_ids or len(product_ids) > LOW_STOCK_CHECK_MAX:
        return []
    if not any(word in text for word in STOCK_WORDS):
        return []
    missing = []
    for match in _product_matches(deps, product_ids):
        for note in match.low_stock:
            count = note.split()[1]
            if f"only {count}" not in text:
                missing.append(f"{match.name}: {note}")
    return missing


SHORT_DESCRIPTION_LENGTH = 90


@dataclass
class ChatDeps:
    """The agent's "deps": per-message context that main.py fills in and PydanticAI
    hands to every tool call and to agent.py's dynamic instructions."""

    db_path: Path
    # From the login cookie, so the browser can't claim to be someone else. None for guests.
    customer: CustomerProfile | None = None
    # The page the shopper is on, looked up in the database. None if unknown.
    page: PageContext | None = None
    # Products looked up before the model runs (Problem 9 pre-search), with live price/stock.
    presearch: list[ProductMatch] = field(default_factory=list)


def _connect(deps: ChatDeps) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{deps.db_path.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _search_terms(query: str) -> list[str]:
    terms: list[str] = []
    for word in _words(query):
        if word in STOPWORDS:
            continue
        terms.extend(SYNONYMS.get(word, word).split())
    return terms


def _normalize_size(size: str) -> str | None:
    key = " ".join(_words(size))
    return SIZE_ALIASES.get(key) or (size.strip().upper() if size.strip().upper() in SIZE_ORDER else None)


def _require_product(con: sqlite3.Connection, product_id: str) -> sqlite3.Row:
    row = con.execute(
        """SELECT c.*, co.name AS collection_name
           FROM catalogue c
           LEFT JOIN product_collections pc ON pc.product_id = c.product_id
           LEFT JOIN collections co ON co.slug = pc.collection_slug
           WHERE c.product_id = ?""",
        (product_id,),
    ).fetchone()
    if row is None:
        # Sends the error back to the model so it can correct itself.
        raise ModelRetry(
            f"No product has id {product_id!r}. Call find_products first and use an exact "
            "product_id from its results."
        )
    return row


# --- Tools ---

def list_collections(ctx: RunContext[ChatDeps]) -> list[CollectionInfo]:
    """List the shop's collections (e.g. Residential Colleges, Yale Athletics) and
    how many products each has. Use this when a shopper asks what we sell or how
    the shop is organized."""
    with _connect(ctx.deps) as con:
        rows = con.execute(
            """SELECT co.slug, co.name, COUNT(pc.product_id) AS product_count
               FROM collections co
               LEFT JOIN product_collections pc ON pc.collection_slug = co.slug
               GROUP BY co.slug ORDER BY co.display_order"""
        ).fetchall()
    return [CollectionInfo(**dict(r)) for r in rows]


def _search(deps: ChatDeps, terms: list[str]) -> tuple[list[str], bool]:
    """Product ids best matching the search terms (up to 8), and whether every term
    matched those products (a confident match)."""
    if not terms:
        return [], False
    with _connect(deps) as con:
        rows = con.execute("SELECT * FROM catalogue").fetchall()

    scored: list[tuple[int, int, sqlite3.Row]] = []
    for row in rows:
        name = set(_words(row["name"]))
        tags = set(_words(" ".join(json.loads(row["search_tags"]))))
        other = set(_words(f'{row["garment_type"]} {" ".join(json.loads(row["colors"]))} {row["description"]}'))
        matched = sum(t in name | tags | other for t in terms)
        # Name matches count most, then search tags, then everything else.
        weight = sum(3 if t in name else 2 if t in tags else 1 if t in other else 0 for t in terms)
        if matched:
            scored.append((matched, weight, row))
    if not scored:
        return [], False

    # Keep only products matching the most search words, so "branford hoodie" doesn't
    # return every hoodie, while a stray word like "gift" doesn't wipe out all results.
    best = max(matched for matched, _, _ in scored)
    scored = [s for s in scored if s[0] == best]
    scored.sort(key=lambda s: (-s[1], s[2]["name"]))
    return [row["product_id"] for _, _, row in scored[:MAX_SEARCH_RESULTS]], best == len(terms)


def _product_matches(deps: ChatDeps, ids: list[str]) -> list[ProductMatch]:
    """ProductMatch records (with live price and stock) for these ids, in order."""
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    with _connect(deps) as con:
        rows = {r["product_id"]: r for r in con.execute(f"SELECT * FROM catalogue WHERE product_id IN ({marks})", ids)}
        stock = con.execute(f"SELECT product_id, size, quantity FROM inventory WHERE product_id IN ({marks})", ids).fetchall()
    sizes: dict[str, list[tuple[str, int]]] = {}
    for s in stock:
        sizes.setdefault(s["product_id"], []).append((s["size"], s["quantity"]))
    order = lambda size: SIZE_ORDER.index(size) if size in SIZE_ORDER else len(SIZE_ORDER)  # noqa: E731

    matches = []
    for pid in ids:
        row = rows.get(pid)
        if row is None:
            continue
        counts = sorted(sizes.get(pid, []), key=lambda s: order(s[0]))
        matches.append(ProductMatch(
            product_id=pid,
            name=row["name"],
            garment_type=row["garment_type"],
            colors=json.loads(row["colors"]),
            price=row["price"],
            stock_by_size={sz: stock_status(q) for sz, q in counts},
            exact_counts=dict(counts),
            available_sizes=[sz for sz, q in counts if q > 0],
            sold_out_sizes=[sz for sz, q in counts if q == 0],
            low_stock=low_stock_notes(counts),
        ))
    return matches


def find_products(ctx: RunContext[ChatDeps], query: str) -> list[ProductMatch]:
    """Find catalogue products matching a shopper's description. Use a few key words,
    e.g. "big yale hoodie", "branford quarter zip", "gray crewneck" or "dad".
    Returns up to 8 best matches, each with its product_id, price and which sizes are
    in stock or sold out right now, all read from the database. That's enough to answer
    most price and "do you have it in M?" questions directly. An empty list means we
    don't carry anything matching."""
    ids, _confident = _search(ctx.deps, _search_terms(query))
    return _product_matches(ctx.deps, ids)


# --- Catalogue summary (Problem 9: whole-catalogue facts) ---

# Garment types are spelled inconsistently in the catalogue ("short-sleeve T-shirt",
# "t-shirt", ...), so they're grouped by keyword. Checked in this order.
GARMENT_CATEGORIES = [
    ("Quarter-zips", ("quarter", "1/4")),
    ("Hoodies", ("hood",)),
    ("Jackets & fleece", ("jacket", "fleece", "bomber")),
    ("Long-sleeve shirts", ("long-sleeve", "long sleeve")),
    ("T-shirts", ("t-shirt", "tee")),
    ("Crewnecks & sweatshirts", ("crewneck", "sweatshirt", "mockneck")),
]


def garment_category(garment_type: str) -> str:
    lowered = garment_type.lower()
    for category, keywords in GARMENT_CATEGORIES:
        if any(k in lowered for k in keywords):
            return category
    return "Other"


def _summarize(category: str, rows: list[sqlite3.Row], stocked: set[str]) -> CategorySummary:
    low = min(r["price"] for r in rows)
    high = max(r["price"] for r in rows)
    cheapest = sorted((r for r in rows if r["price"] == low), key=lambda r: r["name"])
    priciest = sorted((r for r in rows if r["price"] == high), key=lambda r: r["name"])
    ref = lambda r: ProductRef(product_id=r["product_id"], name=r["name"], price=r["price"])  # noqa: E731
    return CategorySummary(
        category=category,
        product_count=len(rows),
        in_stock_count=sum(r["product_id"] in stocked for r in rows),
        min_price=low,
        max_price=high,
        cheapest=[ref(r) for r in cheapest[:3]],
        cheapest_count=len(cheapest),
        most_expensive=[ref(r) for r in priciest[:3]],
        most_expensive_count=len(priciest),
    )


def catalogue_summary(ctx: RunContext[ChatDeps]) -> CatalogueSummary:
    """Exact whole-catalogue facts, computed from the live database: how many products
    there are overall and of each kind (hoodies, T-shirts, quarter-zips...), how many
    are in stock, price ranges, and the cheapest and most expensive items. Use it for
    "what's your cheapest...?", "how many hoodies do you have?", "do all X cost the
    same?" or "what's your price range?"."""
    with _connect(ctx.deps) as con:
        rows = con.execute("SELECT product_id, name, garment_type, price FROM catalogue").fetchall()
        stocked = {r[0] for r in con.execute("SELECT DISTINCT product_id FROM inventory WHERE quantity > 0")}
    groups: dict[str, list[sqlite3.Row]] = {}
    for r in rows:
        groups.setdefault(garment_category(r["garment_type"]), []).append(r)
    order = [c for c, _ in GARMENT_CATEGORIES] + ["Other"]
    return CatalogueSummary(
        overall=_summarize("All products", rows, stocked),
        by_category=[_summarize(c, groups[c], stocked) for c in order if c in groups],
    )


# --- Pre-search (Problem 9: speed) ---

# Words in a shopper's message that say what they want to know, not which product.
QUESTION_WORDS = {
    "where", "what", "which", "how", "much", "many", "does", "can", "could", "would", "are",
    "there", "this", "that", "these", "those", "one", "ones", "still", "left", "available",
    "stock", "price", "cost", "costs", "sell", "carry", "show", "see", "want", "need",
    "looking", "get", "buy", "find", "got", "size", "sizes", "store", "shop", "hi", "hello",
    "thanks", "thank", "s", "m", "l", "xs", "xl", "xxl", "2xl", "small", "medium", "large",
    "extra", "we", "us", "to", "on", "at", "be", "or", "if", "all", "about", "tell",
}


def presearch(deps: ChatDeps, message: str) -> list[ProductMatch]:
    """Products the shopper is probably asking about, looked up before the model runs
    so it can often answer in one call instead of two. Only confident matches: the
    product page they're on, and products matching every product word in the message."""
    ids: list[str] = []
    if deps.page and deps.page.product_id:
        ids.append(deps.page.product_id)
    terms = [t for t in _search_terms(message) if t not in QUESTION_WORDS]
    found, confident = _search(deps, terms)
    if confident:
        ids += [pid for pid in found if pid not in ids]
    return _product_matches(deps, ids[:MAX_SEARCH_RESULTS])


def get_product_details(ctx: RunContext[ChatDeps], product_id: str) -> ProductDetails:
    """Get one product's full description, colors and collection (and price) from the
    catalogue. Use it when the shopper asks what a product looks like or is made of.
    product_id must come from find_products or the product page the shopper is on."""
    with _connect(ctx.deps) as con:
        row = _require_product(con, product_id)
    return ProductDetails(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        price=row["price"],
        collection=row["collection_name"] or "Classic Yale",
    )


def check_stock(ctx: RunContext[ChatDeps], product_id: str, size: str | None = None) -> StockReport:
    """Get exact live stock counts for a product, by size. Pass `size` (e.g. "L", "large",
    "XXL") when the shopper asks about one size; leave it out to get every size. Use it
    when the shopper asks how many are left, or about a product you already identified
    earlier in the conversation. product_id must come from find_products or the product
    page the shopper is on."""
    wanted = None
    if size:
        wanted = _normalize_size(size)
        if wanted is None:
            raise ModelRetry(f"Unknown size {size!r}. Use one of: {', '.join(SIZE_ORDER)}.")

    with _connect(ctx.deps) as con:
        row = _require_product(con, product_id)
        stock = con.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()

    all_sizes = sorted(
        (
            SizeStock(
                size=s["size"],
                status=stock_status(s["quantity"]),
                quantity=s["quantity"],
                in_stock=s["quantity"] > 0,
            )
            for s in stock
        ),
        key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else len(SIZE_ORDER),
    )
    shown = [s for s in all_sizes if s.size == wanted] if wanted else all_sizes
    return StockReport(
        product_id=row["product_id"],
        name=row["name"],
        sizes=shown,
        sold_out_sizes=[s.size for s in all_sizes if not s.in_stock],
        available_sizes=[s.size for s in all_sizes if s.in_stock],
        low_stock=low_stock_notes((s.size, s.quantity) for s in all_sizes),
    )


def get_customer_profile(ctx: RunContext[ChatDeps]) -> CustomerProfile:
    """Who you're chatting with: first name, last name and email if they're logged in,
    or logged_in=false for a guest. Use it when the shopper asks about their account
    or whether you know who they are."""
    return ctx.deps.customer or CustomerProfile(logged_in=False)


# --- Page context (Problem 8) ---

PAGE_NAMES = {
    "/": "the home page",
    "/products": "the Products page (all products)",
    "/about": "the About Us page",
    "/login": "the Log In page",
    "/create-account": "the Create Account page",
}


def resolve_page(deps: ChatDeps, page: str | None) -> PageContext | None:
    """Turn the page address the chat widget sent into a PageContext. Product and
    collection names are looked up in the database, never taken from the browser."""
    if not page or not page.startswith("/"):
        return None
    parts = urlsplit(page)
    path = parts.path.rstrip("/") or "/"
    query = parse_qs(parts.query)

    if path.startswith("/products/"):
        product_id = unquote(path.removeprefix("/products/"))
        with _connect(deps) as con:
            row = con.execute(
                "SELECT product_id, name FROM catalogue WHERE product_id = ?", (product_id,)
            ).fetchone()
        if row is None:
            return PageContext(path=page, description="a product page for a product that doesn't exist")
        return PageContext(
            path=page,
            description=f"the product page for {row['name']}",
            product_id=row["product_id"],
            product_name=row["name"],
        )
    if path == "/products" and "collection" in query:
        collection = get_collection(deps, query["collection"][0])
        if collection:
            return PageContext(
                path=page,
                description=f"the {collection.name} collection ({collection.product_count} products)",
                collection_name=collection.name,
            )
    if path == "/products" and "ids" in query:
        return PageContext(path=page, description="the 'Matches from your chat' page of products you suggested")
    return PageContext(path=page, description=PAGE_NAMES.get(path, "a page on the Campus Customs site"))


# --- Product cards (Problem 7) ---

def get_collection(deps: ChatDeps, slug: str) -> CollectionInfo | None:
    """One collection with its live product count, or None if the slug doesn't exist."""
    with _connect(deps) as con:
        row = con.execute(
            """SELECT co.slug, co.name, COUNT(pc.product_id) AS product_count
               FROM collections co
               LEFT JOIN product_collections pc ON pc.collection_slug = co.slug
               WHERE co.slug = ? GROUP BY co.slug""",
            (slug,),
        ).fetchone()
    return CollectionInfo(**dict(row)) if row else None


def unknown_product_ids(deps: ChatDeps, product_ids: list[str]) -> list[str]:
    """Ids the agent chose that aren't in the catalogue."""
    if not product_ids:
        return []
    with _connect(deps) as con:
        found = {
            r["product_id"]
            for r in con.execute(
                f"SELECT product_id FROM catalogue WHERE product_id IN ({','.join('?' * len(product_ids))})",
                product_ids,
            )
        }
    return [pid for pid in product_ids if pid not in found]


def _short_description(text: str) -> str:
    first = re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0]
    if len(first) <= SHORT_DESCRIPTION_LENGTH:
        return first
    return first[: SHORT_DESCRIPTION_LENGTH - 1].rsplit(" ", 1)[0] + "…"


def load_product_cards(deps: ChatDeps, product_ids: list[str]) -> list[ProductCard]:
    """Build cards for the agent's chosen products, in its order, straight from the
    database. Unknown ids and duplicates are dropped."""
    ids = list(dict.fromkeys(product_ids))[:MAX_CARDS]
    if not ids:
        return []
    with _connect(deps) as con:
        rows = {
            r["product_id"]: r
            for r in con.execute(
                f"SELECT * FROM catalogue WHERE product_id IN ({','.join('?' * len(ids))})", ids
            )
        }
    return [
        ProductCard(
            product_id=row["product_id"],
            name=row["name"],
            price=row["price"],
            # Same URL scheme as the product API in main.py: /images/<file>.jpg
            image_url="/images/" + Path(row["image_file_path"]).name,
            garment_type=row["garment_type"],
            short_description=_short_description(row["description"]),
        )
        for pid in ids
        if (row := rows.get(pid)) is not None
    ]


# Every function here that the agent may call. agent.py registers this list.
AGENT_TOOLS = [
    list_collections,
    find_products,
    get_product_details,
    check_stock,
    get_customer_profile,
    catalogue_summary,
]
