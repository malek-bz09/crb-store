# CRB Store

A store for Chabab Riadhi Belouizdad supporters. React + Vite (with React Compiler) storefront, with a Python FastAPI backend in `app/api/`.

## Run it

Needs Docker (for PostgreSQL), [uv](https://docs.astral.sh/uv/) and pnpm.

First time only:

```sh
docker compose up -d                 # PostgreSQL on localhost:5432 (user/password/db: shop)
cd app/api
cp .env.example .env                 # then set JWT_SECRET_KEY (the file says how)
uv run alembic upgrade head          # create the tables
uv run python -m app.cli seed        # add the sample products
uv run python -m app.cli seed --replace   # swap whatever products are there for the sample ones
uv run python -m app.cli create-admin --email you@shop.dz --name "Your Name"
```

Then, from the project folder:

```sh
pnpm install     # first time only
pnpm dev         # backend (http://localhost:8000) + frontend (http://localhost:5173), via Turborepo
```

`pnpm api` or `pnpm web` starts just one of them.

Vite forwards every `/api/...` request to the backend, so both must be running.
To point it at another backend: `API_URL=http://localhost:9000 pnpm dev`.
API docs (try requests in the browser): http://localhost:8000/docs

## Tests

```sh
pnpm test                # backend tests: need PostgreSQL running; use (and wipe) the shop_test database
pnpm lint                # ruff (backend) + eslint (frontend)
pnpm build               # frontend
```

## How a sale works

Placing an order sets its items aside straight away, so two customers can never
buy the same last item. Open an order in **Admin → Orders** to move it along:

```
pending ─► confirmed ─► processing ─► shipped ─► delivered
   │           │             │            │           │
   └───────────┴─────────────┴─► cancelled └─► returned ◄┘
```

- **Cancelled** and **returned** orders put their items back in stock.
- **Revenue** on the dashboard counts delivered orders only (cash on delivery).

## Products

Add, edit and delete products in **Admin → Products**, including uploading a photo
(saved in `app/api/data/uploads/`). The shop loads products from the backend, so
changes show up straight away. Deleting hides a product but keeps it in old orders.

## CRB Analytics and match tickets

The **/club** page shows CRB's next match, fixtures and results, the Ligue 1 table
and season numbers. The data comes from [TheSportsDB](https://www.thesportsdb.com)
with its free public key, so there's nothing to set up.

The free key allows about 30 requests a minute, so pages never call it: while the
backend runs, a background job saves the data in the database and refreshes it
every few minutes, one request every 2.5 seconds, only for what's out of date
(finished rounds are kept a week). The first time, filling the whole season takes
a couple of minutes; until then the page says the data is still loading.

What the free data doesn't have: the league table stops at the top 5, and CAF and
cup matches only show up when they're CRB's next or latest match. A paid key
(`SPORTSDB_API_KEY` in `app/api/.env`) gives the full table.

**Tickets:** in **Admin → Matches**, paste each upcoming match's Digiticket page.
The CRB page then shows a **Buy tickets** button that opens it. Only admins can
change the links; staff can see them.

## Admin accounts

Sign in at **/admin** with your email. There is no sign-up and no default account;
accounts are created on the server:

```sh
cd app/api
uv run python -m app.cli create-admin --email you@shop.dz --name "Your Name"              # admin
uv run python -m app.cli create-admin --email helper@shop.dz --name "Helper" --role staff # orders only
```

It asks for the password. Running it again for an existing email resets that
account's name, role and password (and signs it out everywhere).

## Data

Everything is stored in PostgreSQL. The connection comes from `DATABASE_URL` in
`app/api/.env`. After pulling changes that touch `app/api/alembic/versions/`, run
`uv run alembic upgrade head` again.

To start over: `docker compose down -v` (deletes the data), `docker compose up -d`,
then repeat the first-time steps above.
