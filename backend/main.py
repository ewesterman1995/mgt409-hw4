"""Campus Customs backend.

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000

Problem 3: read-only product API + product images.
Problem 4: create account / log in / log out.
Problem 5: POST /api/chat, answered by the PydanticAI agent in agent.py.
Problem 8: saved chat history for logged-in shoppers; customer + page context for the agent.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sqlite3
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR.parent / ".env")

import agent  # noqa: E402  (after load_dotenv so the agent sees the API key)
from models import (  # noqa: E402
    MAX_HISTORY_TURNS,
    AccountOut,
    ChangePasswordRequest,
    ChatHistoryMessage,
    ChatReply,
    ChatRequest,
    ChatTurn,
    CustomerProfile,
    LoginRequest,
    ProductCard,
    RegisterRequest,
    SeeMore,
    UserOut,
)
from tools import (  # noqa: E402
    GARMENT_CATEGORIES,
    ChatDeps,
    garment_category,
    load_product_cards,
    resolve_page,
)

logger = logging.getLogger("campus_customs")

DATA_DIR = BACKEND_DIR.parent / "data"
DB_PATH = Path(os.getenv("CAMPUS_DB_PATH", DATA_DIR / "campus_customs.db"))
IMAGES_DIR = DATA_DIR / "products"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# ---------------------------------------------------------------------------
# Collections and featured products
# ---------------------------------------------------------------------------
# These live in the database (tables `collections`, `product_collections`,
# `featured_products`). The seed database doesn't have them, so on startup we
# create the tables and fill them from the rules below if they are empty.
# That way the site works with any fresh copy of the data pack.

# Collections in display order. `keywords` match whole words in the product
# name; rules are checked in MATCH_ORDER and anything unmatched is "classic".
COLLECTIONS = [
    {"slug": "classic", "name": "Classic Yale", "keywords": []},
    {
        "slug": "colleges",
        "name": "Residential Colleges",
        "keywords": [
            "benjamin franklin", "berkeley", "branford", "davenport", "ezra stiles",
            "grace hopper", "jonathan edwards", "morse", "pauli murray", "pierson",
            "saybrook", "silliman", "timothy dwight", "trumbull",
        ],
    },
    {
        "slug": "schools",
        "name": "Graduate & Professional Schools",
        "keywords": ["school of", "law school", "divinity school", "forest school"],
    },
    {
        "slug": "athletics",
        "name": "Yale Athletics",
        "keywords": [
            "baseball", "basketball", "diving", "fencing", "football", "golf",
            "hockey", "lacrosse", "sailing", "soccer", "squash", "swimming",
            "tennis", "track", "volleyball", "yale vs harvard", "yale bowl",
        ],
    },
    {
        "slug": "family",
        "name": "Yale Family",
        "keywords": [
            "mom", "dad", "aunt", "uncle", "grandma", "grandpa",
            "brother", "sister", "cousin",
        ],
    },
]
MATCH_ORDER = ["colleges", "schools", "family", "athletics"]

# Hand-picked for the home page carousel. The database has no sales data,
# so these are featured picks, not best sellers.
FEATURED_IDS = [
    "basic-hoodie-big-yale",
    "2025-yale-vs-harvard-t-shirt",
    "champion-reverse-weave-crewneck",
    "district-vit-hoodie-vintage-bulldog",
    "super-heavyweight-crewneck-arched-yale-crest",
    "yale-mom-hoodie",
    "brooks-brothers-bomber-jacket-yale",
    "boola-boola-t-shirt",
]


def get_db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def guess_collection(name: str) -> str:
    """Pick a collection slug by matching whole words in the product name."""
    lowered = name.lower()
    keywords = {c["slug"]: c["keywords"] for c in COLLECTIONS}
    for slug in MATCH_ORDER:
        for keyword in keywords[slug]:
            if re.search(rf"\b{re.escape(keyword)}\b", lowered):
                return slug
    return "classic"


def init_db() -> None:
    """Create and seed the collection/featured tables if they are missing, and add the
    see_more_json column to chat_messages (Problem 8)."""
    with get_db() as con:
        chat_columns = {r["name"] for r in con.execute("PRAGMA table_info(chat_messages)")}
        if "see_more_json" not in chat_columns:
            con.execute("ALTER TABLE chat_messages ADD COLUMN see_more_json TEXT")
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS collections (
                slug TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                display_order INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS product_collections (
                product_id TEXT PRIMARY KEY REFERENCES catalogue(product_id),
                collection_slug TEXT NOT NULL REFERENCES collections(slug)
            );
            CREATE TABLE IF NOT EXISTS featured_products (
                product_id TEXT PRIMARY KEY REFERENCES catalogue(product_id),
                position INTEGER NOT NULL
            );
            """
        )
        con.executemany(
            "INSERT OR IGNORE INTO collections (slug, name, display_order) VALUES (?, ?, ?)",
            [(c["slug"], c["name"], i) for i, c in enumerate(COLLECTIONS)],
        )
        # Any product without a collection yet (e.g. newly added) gets one.
        unassigned = con.execute(
            """SELECT product_id, name FROM catalogue
               WHERE product_id NOT IN (SELECT product_id FROM product_collections)"""
        ).fetchall()
        con.executemany(
            "INSERT INTO product_collections (product_id, collection_slug) VALUES (?, ?)",
            [(r["product_id"], guess_collection(r["name"])) for r in unassigned],
        )
        if con.execute("SELECT COUNT(*) FROM featured_products").fetchone()[0] == 0:
            con.executemany(
                """INSERT INTO featured_products (product_id, position)
                   SELECT ?, ? WHERE EXISTS (SELECT 1 FROM catalogue WHERE product_id = ?)""",
                [(pid, i, pid) for i, pid in enumerate(FEATURED_IDS)],
            )


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------
# Passwords are never stored. We store a salted PBKDF2-SHA256 hash:
#   pbkdf2_sha256$<iterations>$<salt hex>$<hash hex>
# The seed accounts use an older 3-part format without the iteration count:
#   pbkdf2_sha256$<salt hex>$<hash hex>

PBKDF2_ITERATIONS = 600_000  # OWASP 2023 recommendation for PBKDF2-SHA256

# Settings for the seed accounts' 3-part hashes (confirmed against the test user).
LEGACY_ITERATIONS = 120_000
LEGACY_SALT_IS_HEX_TEXT = True  # salt passed to PBKDF2 as its text, not decoded


def _pbkdf2(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = _pbkdf2(password, salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if parts[0] != "pbkdf2_sha256":
        return False
    if len(parts) == 4:
        _, iterations, salt_hex, hash_hex = parts
        digest = _pbkdf2(password, bytes.fromhex(salt_hex), int(iterations))
    elif len(parts) == 3:
        _, salt_hex, hash_hex = parts
        salt = salt_hex.encode() if LEGACY_SALT_IS_HEX_TEXT else bytes.fromhex(salt_hex)
        digest = _pbkdf2(password, salt, LEGACY_ITERATIONS)
    else:
        return False
    # Constant-time comparison so response timing doesn't leak how close a guess was.
    return hmac.compare_digest(digest.hex(), hash_hex)


# Used to spend the same time on unknown emails as on real ones.
_DUMMY_HASH = hash_password(secrets.token_hex(16))


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
# After login the browser gets an HttpOnly cookie holding "<user_id>.<expiry>"
# plus an HMAC signature, so it can't be read by page scripts or forged.

SESSION_COOKIE = "cc_session"
SESSION_SECONDS = 7 * 24 * 3600
SESSION_SECRET = os.getenv("SESSION_SECRET") or secrets.token_hex(32)
if not os.getenv("SESSION_SECRET"):
    print("SESSION_SECRET not set in .env: using a random one (logins reset on restart).")


def _sign(payload: str) -> str:
    sig = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode().rstrip("=")


def make_session_token(user_id: int) -> str:
    payload = f"{user_id}.{int(time.time()) + SESSION_SECONDS}"
    return f"{payload}.{_sign(payload)}"


def read_session_token(token: str | None) -> int | None:
    """Return the user id if the token is genuine and not expired."""
    if not token or token.count(".") != 2:
        return None
    user_id, expires, sig = token.split(".")
    if not hmac.compare_digest(sig, _sign(f"{user_id}.{expires}")):
        return None
    if not expires.isdigit() or int(expires) < time.time():
        return None
    return int(user_id)


def set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        make_session_token(user_id),
        max_age=SESSION_SECONDS,
        httponly=True,
        samesite="lax",
    )


def user_out(row: sqlite3.Row) -> UserOut:
    first, last = row["first_name"], row["last_name"]
    if not first:  # older rows may only have the full `name`
        first, _, last = row["name"].partition(" ")
    return UserOut(id=row["id"], first_name=first, last_name=last or "", email=row["email"])


def current_user(request: Request) -> sqlite3.Row | None:
    user_id = read_session_token(request.cookies.get(SESSION_COOKIE))
    if user_id is None:
        return None
    with get_db() as con:
        return con.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Campus Customs API", lifespan=lifespan)

# The Vite dev server runs on port 5173.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Product photos: /images/<file>.jpg
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")


PRODUCT_SELECT = """
    SELECT c.*, pc.collection_slug
    FROM catalogue c
    LEFT JOIN product_collections pc ON pc.product_id = c.product_id
"""


def product_from_row(row: sqlite3.Row) -> dict:
    """Turn a catalogue row into JSON the front end can use."""
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "price": row["price"],
        # image_file_path is "products/<file>.jpg"; serve it from /images/<file>.jpg
        "image_url": "/images/" + Path(row["image_file_path"]).name,
        "collection": row["collection_slug"] or "classic",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/collections")
def list_collections():
    """Each collection with its product count and a cover image."""
    with get_db() as con:
        collections = con.execute(
            """SELECT co.slug, co.name, COUNT(pc.product_id) AS count,
                      (SELECT c.image_file_path FROM catalogue c
                       JOIN product_collections p ON p.product_id = c.product_id
                       WHERE p.collection_slug = co.slug ORDER BY c.name LIMIT 1) AS image
               FROM collections co
               LEFT JOIN product_collections pc ON pc.collection_slug = co.slug
               GROUP BY co.slug ORDER BY co.display_order"""
        ).fetchall()
    return [
        {
            "slug": c["slug"],
            "name": c["name"],
            "count": c["count"],
            "image_url": "/images/" + Path(c["image"]).name if c["image"] else None,
        }
        for c in collections
    ]


@app.get("/api/featured")
def list_featured():
    with get_db() as con:
        rows = con.execute(
            PRODUCT_SELECT
            + " JOIN featured_products f ON f.product_id = c.product_id ORDER BY f.position"
        ).fetchall()
    return [product_from_row(r) for r in rows]


def category_slug(name: str) -> str:
    """'Jackets & fleece' -> 'jackets-fleece', for links like /products?type=jackets-fleece."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@app.get("/api/categories")
def list_categories():
    """Kinds of garment (Hoodies, T-shirts, ...) with live product counts, for the
    Products menu. Same grouping as the agent's catalogue_summary tool."""
    with get_db() as con:
        types = [r[0] for r in con.execute("SELECT garment_type FROM catalogue")]
    counts: dict[str, int] = {}
    for t in types:
        name = garment_category(t)
        counts[name] = counts.get(name, 0) + 1
    order = [name for name, _ in GARMENT_CATEGORIES] + ["Other"]
    return [
        {"slug": category_slug(name), "name": name, "count": counts[name]}
        for name in order if name in counts
    ]


@app.get("/api/products")
def list_products(collection: str | None = None, ids: str | None = None, type: str | None = None):
    """All products, one collection (?collection=colleges), one kind of garment
    (?type=hoodies), or specific products in a given order (?ids=a,b,c), which is used
    for "See more" from the chat."""
    if type:
        with get_db() as con:
            rows = con.execute(PRODUCT_SELECT + " ORDER BY c.name").fetchall()
        return [
            product_from_row(r) for r in rows
            if category_slug(garment_category(r["garment_type"])) == type
        ]
    with get_db() as con:
        if ids:
            wanted = [i for i in ids.split(",") if i][:50]
            rows = con.execute(
                PRODUCT_SELECT + f" WHERE c.product_id IN ({','.join('?' * len(wanted))})", wanted
            ).fetchall()
            by_id = {r["product_id"]: r for r in rows}
            return [product_from_row(by_id[i]) for i in dict.fromkeys(wanted) if i in by_id]
        if collection:
            rows = con.execute(
                PRODUCT_SELECT + " WHERE pc.collection_slug = ? ORDER BY c.name", (collection,)
            ).fetchall()
        else:
            rows = con.execute(PRODUCT_SELECT + " ORDER BY c.name").fetchall()
    return [product_from_row(r) for r in rows]


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    with get_db() as con:
        row = con.execute(PRODUCT_SELECT + " WHERE c.product_id = ?", (product_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        stock = con.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()

    product = product_from_row(row)
    product["search_tags"] = json.loads(row["search_tags"])
    product["sizes"] = sorted(
        ({"size": s["size"], "quantity": s["quantity"]} for s in stock),
        key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99,
    )
    return product


# --- Accounts ---

@app.post("/api/auth/register", response_model=UserOut, status_code=201)
def register(body: RegisterRequest, response: Response):
    with get_db() as con:
        if con.execute("SELECT 1 FROM users WHERE email = ?", (body.email,)).fetchone():
            raise HTTPException(status_code=409, detail="An account with that email already exists.")
        cur = con.execute(
            """INSERT INTO users (name, email, password_hash, first_name, last_name)
               VALUES (?, ?, ?, ?, ?)""",
            (
                f"{body.first_name} {body.last_name}",
                body.email,
                hash_password(body.password),
                body.first_name,
                body.last_name,
            ),
        )
        row = con.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    set_session_cookie(response, row["id"])
    return user_out(row)


@app.post("/api/auth/login", response_model=UserOut)
def login(body: LoginRequest, response: Response):
    with get_db() as con:
        row = con.execute("SELECT * FROM users WHERE lower(email) = ?", (body.email,)).fetchone()
    if row is None:
        verify_password(body.password, _DUMMY_HASH)  # same work as a real check
        ok = False
    else:
        ok = verify_password(body.password, row["password_hash"])
    if not ok:
        # Same message either way, so attackers can't learn which emails exist.
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    set_session_cookie(response, row["id"])
    return user_out(row)


@app.post("/api/auth/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)


def require_user(request: Request) -> sqlite3.Row:
    row = current_user(request)
    if row is None:
        raise HTTPException(status_code=401, detail="Please log in to see your account.")
    return row


@app.get("/api/account", response_model=AccountOut)
def account(request: Request):
    """The logged-in shopper's account summary. There's no orders table, so no orders
    are returned; the page says the account has no orders."""
    row = require_user(request)
    with get_db() as con:
        count, last = con.execute(
            "SELECT COUNT(*), MAX(created_at) FROM chat_messages WHERE user_id = ?", (row["id"],)
        ).fetchone()
    user = user_out(row)
    return AccountOut(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        member_since=(row["created_at"] or "")[:10],
        saved_messages=count,
        last_chat_at=last[:16] if last else None,
    )


@app.post("/api/auth/change-password", status_code=204)
def change_password(body: ChangePasswordRequest, request: Request):
    """Check the current password, then store a fresh hash of the new one."""
    row = require_user(request)
    if not verify_password(body.current_password, row["password_hash"]):
        raise HTTPException(status_code=400, detail="Your current password is incorrect.")
    with get_db() as con:
        con.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(body.new_password), row["id"]),
        )


@app.get("/api/auth/me", response_model=UserOut | None)
def me(request: Request):
    row = current_user(request)
    return user_out(row) if row else None


# --- Chat ---

HISTORY_DISPLAY_LIMIT = 50  # messages reloaded into the chat widget


def customer_profile(row: sqlite3.Row) -> CustomerProfile:
    """The only customer fields the agent sees: name and email (never the id or password hash)."""
    user = user_out(row)
    return CustomerProfile(
        logged_in=True, first_name=user.first_name, last_name=user.last_name, email=user.email
    )


def load_saved_messages(user_id: int, limit: int) -> list[sqlite3.Row]:
    """The user's most recent saved messages, oldest first."""
    with get_db() as con:
        rows = con.execute(
            "SELECT * FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
        ).fetchall()
    return rows[::-1]


def clean_content(text: str) -> str:
    # Some seed messages contain markdown bold markers the widget doesn't render.
    return text.replace("**", "")


def save_exchange(user_id: int, message: str, reply: ChatReply) -> None:
    """Store the shopper's message and the assistant's reply (with its cards)."""
    with get_db() as con:
        con.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)",
            (user_id, message),
        )
        con.execute(
            """INSERT INTO chat_messages (user_id, role, content, products_json, see_more_json)
               VALUES (?, 'assistant', ?, ?, ?)""",
            (
                user_id,
                reply.reply,
                json.dumps([p.model_dump() for p in reply.products]),
                reply.see_more.model_dump_json() if reply.see_more else None,
            ),
        )


def history_message(row: sqlite3.Row, deps: ChatDeps) -> ChatHistoryMessage:
    """Rebuild a saved message for display. Cards are rebuilt from the product ids,
    so they show today's names and prices (and work for older seed rows too)."""
    ids = [p["product_id"] for p in json.loads(row["products_json"] or "[]") if "product_id" in p]
    cards = load_product_cards(deps, ids)
    if row["see_more_json"]:
        see_more = SeeMore.model_validate_json(row["see_more_json"])
    elif len(cards) > 1:  # older rows saved before the button existed
        see_more = SeeMore(
            text=f"See {len(cards) - 1} more styles →",
            href="/products?ids=" + ",".join(c.product_id for c in cards),
        )
    else:
        see_more = None
    return ChatHistoryMessage(
        role=row["role"], content=clean_content(row["content"]), products=cards, see_more=see_more
    )


@app.get("/api/chat/history", response_model=list[ChatHistoryMessage])
def chat_history(request: Request):
    """The logged-in shopper's saved conversation (empty for guests)."""
    row = current_user(request)
    if row is None:
        return []
    deps = ChatDeps(db_path=DB_PATH)
    return [history_message(m, deps) for m in load_saved_messages(row["id"], HISTORY_DISPLAY_LIMIT)]


@app.delete("/api/chat/history", status_code=204)
def clear_chat_history(request: Request):
    """Delete the logged-in shopper's saved conversation."""
    row = current_user(request)
    if row is None:
        raise HTTPException(status_code=401, detail="Log in to manage your chat history.")
    with get_db() as con:
        con.execute("DELETE FROM chat_messages WHERE user_id = ?", (row["id"],))


NOT_CONFIGURED = (503, "The chat assistant isn't set up yet (missing API key). Please try again later.")
AGENT_FAILED = (502, "Sorry, the assistant ran into a problem. Please try again in a moment.")

# Rate limit (Problem 12): each shopper (account, or browser address for guests) gets
# at most CHAT_RATE_LIMIT messages per CHAT_RATE_WINDOW seconds, so nobody can spam
# the chat and run up model costs.
CHAT_RATE_LIMIT = 15
CHAT_RATE_WINDOW = 60
_recent_messages: dict[str, list[float]] = {}


def check_rate_limit(key: str) -> None:
    now = time.time()
    recent = [t for t in _recent_messages.get(key, []) if now - t < CHAT_RATE_WINDOW]
    if len(recent) >= CHAT_RATE_LIMIT:
        _recent_messages[key] = recent
        raise HTTPException(
            status_code=429,
            detail="You're sending messages very quickly. Please wait a minute and try again.",
        )
    recent.append(now)
    _recent_messages[key] = recent


async def answer_chat(
    body: ChatRequest,
    request: Request,
    on_status: Callable[[str], None] | None = None,
    on_preview: Callable[[list[ProductCard]], None] | None = None,
) -> ChatReply:
    """One chat turn: who's asking, what page they're on, their history, the agent's
    reply, and saving it for logged-in shoppers. Raises HTTPException on failure."""
    user = current_user(request)
    shopper = f"user:{user['id']}" if user else "guest"
    check_rate_limit(shopper if user else f"ip:{request.client.host if request.client else 'unknown'}")
    deps = ChatDeps(db_path=DB_PATH, customer=customer_profile(user) if user else None)
    deps.page = resolve_page(deps, body.page)

    if user:
        # Logged in: the conversation so far comes from the database, not the browser.
        history = [
            ChatTurn(role=m["role"], content=clean_content(m["content"]))
            for m in load_saved_messages(user["id"], MAX_HISTORY_TURNS)
        ]
    else:
        history = body.history

    try:
        reply = await agent.run_chat(body.message, history, deps, on_status, on_preview, shopper=shopper)
    except agent.AgentNotConfigured:
        raise HTTPException(status_code=NOT_CONFIGURED[0], detail=NOT_CONFIGURED[1])
    except Exception:
        logger.exception("Chat agent failed")
        raise HTTPException(status_code=AGENT_FAILED[0], detail=AGENT_FAILED[1])

    if user:
        save_exchange(user["id"], body.message, reply)
    return reply


@app.post("/api/chat", response_model=ChatReply)
async def chat(body: ChatRequest, request: Request):
    return await answer_chat(body, request)


@app.post("/api/chat/stream")
async def chat_stream(body: ChatRequest, request: Request):
    """Same as /api/chat, but streams progress while the agent works, one JSON object
    per line (Problem 9):
        {"type": "preview", "products": [card]}              (instantly, if the message names a product)
        {"type": "status", "text": "Checking live stock…"}   (zero or more)
        {"type": "reply", "reply": ..., "products": [...], "see_more": ...}
     or {"type": "error", "detail": "..."}
    """
    queue: asyncio.Queue[dict | None] = asyncio.Queue()

    async def work() -> None:
        try:
            reply = await answer_chat(
                body,
                request,
                on_status=lambda text: queue.put_nowait({"type": "status", "text": text}),
                on_preview=lambda cards: queue.put_nowait(
                    {"type": "preview", "products": [c.model_dump() for c in cards]}
                ),
            )
            queue.put_nowait({"type": "reply", **reply.model_dump()})
        except HTTPException as error:
            queue.put_nowait({"type": "error", "detail": error.detail})
        finally:
            queue.put_nowait(None)

    task = asyncio.create_task(work())

    async def lines():
        try:
            while (item := await queue.get()) is not None:
                yield json.dumps(item) + "\n"
        finally:
            if not task.done():  # the shopper closed the page mid-reply
                task.cancel()

    return StreamingResponse(
        lines(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
