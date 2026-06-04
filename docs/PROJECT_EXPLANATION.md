# Project Explanation — InvTrack Inventory & Order Management System

## 1. Overview

InvTrack is a full-stack Inventory & Order Management System built to the exact specifications in the technical assessment. It allows businesses to manage products, customers, and orders, with automatic inventory tracking.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   Frontend  │    │   Backend   │    │  PostgreSQL  │ │
│  │  (Nginx)    │───▶│  (FastAPI)  │───▶│  Database   │ │
│  │  Port 3000  │    │  Port 8000  │    │  Port 5432  │ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
│                                               │         │
│                                        named volume:    │
│                                      postgres_data      │
└─────────────────────────────────────────────────────────┘
```

**Three Docker services:**

1. **db** — PostgreSQL 15 (alpine) with a named volume for data persistence. Exposes no external port for security.
2. **backend** — Python/FastAPI application. Waits for `db` to be healthy before starting (healthcheck). Exposes port 8000.
3. **frontend** — Nginx serving a single `index.html` React SPA. Exposes port 3000.

---

## 3. Request Flow

```
Browser (port 3000)
       │
       ▼
  Nginx (frontend container)
       │
       │  Direct JS API calls to backend:8000
       ▼
  FastAPI (backend container)
       │
       ├── Validate request (Pydantic)
       │
       ├── Business logic checks
       │     - SKU/email uniqueness
       │     - Stock availability
       │
       ├── SQLAlchemy ORM query
       │
       ▼
  PostgreSQL (db container)
       │
       ▼
  JSON Response → Browser
```

---

## 4. Data Model

```
products                    customers
─────────────────────       ─────────────────────
id          PK  INT         id          PK  INT
name            TEXT        full_name       TEXT
sku         UK  TEXT        email       UK  TEXT
price           FLOAT       phone           TEXT
quantity        INT         created_at      TIMESTAMP
created_at      TIMESTAMP
updated_at      TIMESTAMP

orders                      order_items
─────────────────────       ─────────────────────
id          PK  INT         id          PK  INT
customer_id FK  INT ──┐     order_id    FK  INT ──┐
total_amount    FLOAT  │     product_id  FK  INT   │
status          TEXT   │     quantity        INT   │
created_at      TIMESTAMP    unit_price      FLOAT │
                       │                          │
                 customers.id            orders.id / products.id
```

**Relationships:**
- A `Customer` can have many `Orders`
- An `Order` belongs to one `Customer`
- An `Order` has many `OrderItems`
- An `OrderItem` references one `Product`

---

## 5. Backend Code Structure

```
backend/
└── app/
    ├── main.py          FastAPI app: registers routers, CORS, creates tables
    ├── database.py      SQLAlchemy engine, session factory, get_db() dependency
    ├── models/
    │   └── models.py    ORM table definitions (Product, Customer, Order, OrderItem)
    ├── schemas/
    │   └── schemas.py   Pydantic models for request validation + response serialization
    └── routes/
        ├── products.py  POST/GET/PUT/DELETE /products
        ├── customers.py POST/GET/DELETE /customers
        ├── orders.py    POST/GET/DELETE /orders (business logic here)
        └── dashboard.py GET /dashboard (aggregated stats)
```

### Key design decisions:

**Pydantic v2 validation** — All input is validated before it reaches the database. Price and quantity cannot be negative. Validators use `@field_validator`.

**SQLAlchemy relationships** — ORM relationships (`back_populates`) allow Pydantic to serialize nested objects (e.g. an order includes its customer and items automatically).

**Table auto-creation** — `Base.metadata.create_all(bind=engine)` runs on startup, creating all tables if they don't exist. No migration tool needed for this project.

---

## 6. Business Logic Implementation

All business rules are implemented in `routes/orders.py`:

```
POST /orders flow:
  1. Verify customer exists → 404 if not
  2. Verify at least one item → 400 if empty
  3. For each item:
      a. Verify product exists → 404 if not
      b. Check product.quantity >= requested quantity → 400 if insufficient
      c. Calculate line total (price × qty)
  4. Create Order record with calculated total_amount
  5. Create OrderItem records
  6. Deduct quantity from each Product
  7. Commit transaction
  8. Return full order with nested customer + items

DELETE /orders flow:
  1. Verify order exists → 404 if not
  2. For each OrderItem, restore product.quantity
  3. Delete order (cascade deletes OrderItems)
  4. Commit transaction
```

This is done inside a single SQLAlchemy transaction — either everything succeeds or nothing changes.

---

## 7. Frontend Structure

The frontend is a **single `index.html` file** that includes:

- React 18 and ReactDOM via unpkg CDN
- Babel standalone for JSX transpilation in-browser
- Axios for API calls
- All CSS inline in a `<style>` block
- All React components in a single `<script type="text/babel">` block

**Why single file?** No build step, no `npm install`, works immediately with Nginx, trivially deployable to Vercel/Netlify as a static file.

### Component tree:
```
App
├── Sidebar (navigation buttons)
├── Dashboard
│     └── Low-stock table
├── Products
│     └── ProductModal (add/edit)
├── Customers
│     └── CustomerModal (add)
└── Orders
      ├── OrderModal (create, with dynamic item rows)
      └── OrderDetail (view)
```

**Shared components:** `Alert`, `ConfirmModal`

### State management:
No Redux or external state library. Each page manages its own state with `useState` and `useEffect`. Data is re-fetched from the API after every mutation (create/delete). This is simple, correct, and appropriate for this scale.

---

## 8. Docker Setup

### docker-compose.yml services:

**db:**
- Image: `postgres:15-alpine` (lightweight)
- Named volume `postgres_data` ensures data survives container restarts
- Healthcheck using `pg_isready` before backend starts
- Credentials from environment variables (never hardcoded)

**backend:**
- Built from `backend/Dockerfile` using `python:3.11-slim`
- `depends_on` with `condition: service_healthy` ensures DB is ready
- `DATABASE_URL` injected as environment variable
- No credentials hardcoded anywhere

**frontend:**
- Built from `frontend/Dockerfile` using `nginx:alpine`
- Copies `index.html` and `nginx.conf` into the image
- Minimal — only 2 files in the image

### Environment variables:
All sensitive values (`POSTGRES_PASSWORD`) come from a `.env` file that is never committed to git. The `.env.example` file documents what's needed.

---

## 9. Deployment Guide

### Backend on Render (free tier):

1. Push to GitHub
2. New → Web Service → connect repo → set root to `/backend`
3. Runtime: Python 3
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add env var: `DATABASE_URL` = your PostgreSQL connection string
   (Render provides a free PostgreSQL add-on, or use Supabase/Neon)

### Frontend on Vercel:

1. Push to GitHub
2. New Project → Import repo
3. Set root directory to `frontend/`
4. Framework: **Other** (it's just a static HTML file)
5. No build command needed
6. Output directory: `.` (or `frontend/`)
7. Before deploying: update the `API` constant in `index.html`:
   ```js
   const API = "https://your-app.onrender.com";
   ```

### Docker Hub:

```bash
docker build -t yourusername/inventory-backend:latest ./backend
docker push yourusername/inventory-backend:latest
```

---

## 10. API Error Handling

All routes follow consistent HTTP status codes:

| Scenario | Status Code |
|---|---|
| Created successfully | 201 Created |
| Successful read | 200 OK |
| Successful delete | 204 No Content |
| Validation error (Pydantic) | 422 Unprocessable Entity |
| Business rule violation | 400 Bad Request |
| Resource not found | 404 Not Found |

Error responses follow FastAPI's default format:
```json
{ "detail": "Human-readable error message" }
```

The frontend reads `error.response.data.detail` and displays it in a red alert box.

---

## 11. What Was Kept Simple (By Design)

- **No JWT auth** — Not in the requirements; adding it would complicate the setup unnecessarily
- **No Alembic migrations** — `create_all()` on startup is sufficient for a fresh deployment
- **No Redux** — Local state per page is clean and maintainable
- **Single HTML file frontend** — Avoids npm complexity while still being a real React SPA
- **No TypeScript** — Plain JS keeps the frontend fast to read and modify
