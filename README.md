# Campus Customs + Chatbot (MGT 409, Homework 4)

A storefront website for **Campus Customs**, a New Haven shop selling officially licensed Yale apparel, with an AI shopping assistant that answers questions about products, prices and stock from the shop's live database.

- **Front end:** Vite + React + TypeScript (`frontend/`)
- **Back end:** FastAPI (`backend/main.py`)
- **Agent:** PydanticAI, made of four files: `backend/prompts/prompt.md`, `backend/agent.py`, `backend/tools.py`, `backend/models.py`
- **Model:** `gpt-5.6-luna` through Portkey

How it all works (models, tools, safety rules, limits and the audit trail) is explained in [`output/harness.md`](output/harness.md).

## Folder layout

```
hw4/
├── AI_prompts.md         # log of my prompts, one section per problem
├── requirements.txt      # Python packages for the backend
├── .env.example          # settings template (placeholders only)
├── .gitignore
├── README.md
├── frontend/             # Vite React TypeScript app
├── backend/
│   ├── main.py           # FastAPI app
│   ├── agent.py
│   ├── models.py
│   ├── tools.py
│   └── prompts/
│       └── prompt.md
├── output/
│   ├── harness.md
│   ├── design.md
│   ├── usability.md
│   ├── app_check.html
│   ├── app_check_images/ # screenshots linked from app_check.html
│   └── audit_trail.json
└── data/                 # NOT in the repo: add the data pack here (see below)
```

## What you need

- Python 3.12 or newer
- Node.js 20 or newer
- A Portkey API key
- The Campus Customs **data pack** (not in this repo)

## 1. Place the data pack

The database and product photos are kept out of GitHub. Put the data pack in the repo root so it looks like this:

```
data/
├── campus_customs.db
└── products/   # product images referenced by the catalogue
```

## 2. Create `.env`

Copy `.env.example` to `.env` in the repo root and fill it in:

```
PORTKEY_API_KEY=your-portkey-api-key
SESSION_SECRET=any-long-random-string
```

`.env` is ignored by git. Never commit it.

## 3. Run the back end (terminal 1)

From the repo root:

```bash
python -m venv .venv
```

Activate it: `.venv\Scripts\activate` on Windows, or `source .venv/bin/activate` on Mac/Linux. Then:

```bash
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

The API runs at http://localhost:8000. On first start it adds the tables it needs (collections, featured items, saved chat cards) to the database if they're missing.

## 4. Run the front end (terminal 2)

From the repo root:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The front end sends `/api` and `/images` requests to the back end on port 8000, so keep both running.

## Using the site

- Browse **Products** by collection or by garment type, and open any product for prices and stock by size.
- **Create an account** or browse as a guest. Logged-in shoppers get their chat history saved and a **My Account** page.
- Click the chat bubble (or **Ask our assistant** on a product page) to ask about products, sizes, prices and stock. The assistant only states facts it looked up in the database.
- There is no checkout: purchases happen at the store, 57 Broadway, New Haven.

## Troubleshooting

- **Chat says "The chat assistant isn't set up yet":** check `PORTKEY_API_KEY` in `.env` and restart the back end.
- **No products or images:** make sure `data/campus_customs.db` and `data/products/` are in place.
- **"database disk image is malformed" on a shared or network drive:** copy the database to a local disk and point `CAMPUS_DB_PATH` in `.env` at it.
- **Logged out after every restart:** set `SESSION_SECRET` in `.env`.
