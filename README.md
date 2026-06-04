# InvTrack — Inventory & Order Management System

A full-stack production-ready system to manage products, customers, orders, and inventory tracking.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Single-page HTML + React (via CDN) served by Nginx |
| Backend | Python 3.11 + FastAPI |
| Database | PostgreSQL 15 |
| Containerization | Docker + Docker Compose |

---

## Quick Start (Docker)

### 1. Clone the repo
```bash
git clone <your-repo-url>
cd inventory-system
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and set a secure POSTGRES_PASSWORD
```

### 3. Build and run
```bash
docker compose up --build
```

### 4. Open the app
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs

---

## Project Structure

```
inventory-system/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── database.py          # SQLAlchemy engine & session
│   │   ├── models/
│   │   │   └── models.py        # ORM models (Product, Customer, Order, OrderItem)
│   │   ├── schemas/
│   │   │   └── schemas.py       # Pydantic request/response schemas
│   │   └── routes/
│   │       ├── products.py      # CRUD for products
│   │       ├── customers.py     # CRUD for customers
│   │       ├── orders.py        # Order creation with stock deduction
│   │       └── dashboard.py     # Aggregate stats
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── frontend/
│   ├── index.html               # Complete React SPA (no build step)
│   ├── nginx.conf               # Nginx serving config
│   ├── Dockerfile
│   └── .dockerignore
├── docker-compose.yml
├── .env.example
└── .gitignore
```

---

## API Endpoints

### Products
| Method | Endpoint | Description |
|---|---|---|
| POST | /products | Create a product |
| GET | /products | List all products |
| GET | /products/{id} | Get product by ID |
| PUT | /products/{id} | Update product |
| DELETE | /products/{id} | Delete product |

### Customers
| Method | Endpoint | Description |
|---|---|---|
| POST | /customers | Create a customer |
| GET | /customers | List all customers |
| GET | /customers/{id} | Get customer by ID |
| DELETE | /customers/{id} | Delete customer |

### Orders
| Method | Endpoint | Description |
|---|---|---|
| POST | /orders | Create an order (auto-deducts stock) |
| GET | /orders | List all orders |
| GET | /orders/{id} | Get order details |
| DELETE | /orders/{id} | Cancel order (restores stock) |

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| GET | /dashboard | Stats: counts + low-stock products |

---

## Business Logic

- **SKU uniqueness** — Enforced at DB and API level
- **Email uniqueness** — Enforced at DB and API level
- **Stock validation** — Orders rejected if stock is insufficient
- **Automatic stock deduction** — Placing an order reduces inventory
- **Stock restoration** — Cancelling an order restores inventory
- **Total auto-calculation** — Order total calculated server-side from current prices
- **Non-negative quantities** — Validated in Pydantic schemas

---

## Deployment

### Backend — Render / Railway / Fly.io

1. Push code to GitHub
2. Create a new web service pointing to the `backend/` directory
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable: `DATABASE_URL=postgresql://...` (from your hosted DB)

### Frontend — Vercel / Netlify

Since the frontend is a single `index.html` file:

1. Push to GitHub
2. Create a new site pointing to the `frontend/` directory
3. No build step required — publish directory is `frontend/`
4. Update the `API` constant in `index.html` to your live backend URL:
   ```js
   const API = "https://your-backend.onrender.com";
   ```

### Docker Hub (Backend Image)

```bash
docker build -t yourdockerhubuser/inventory-backend:latest ./backend
docker push yourdockerhubuser/inventory-backend:latest
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@db:5432/inventory_db` | Full PostgreSQL connection string |
| `POSTGRES_USER` | `postgres` | DB username (used by docker-compose) |
| `POSTGRES_PASSWORD` | `postgres` | DB password — **change this in production** |
| `POSTGRES_DB` | `inventory_db` | Database name |

---

## Frontend Features

- **Dashboard** — Live stats: total products, customers, orders, low-stock alerts
- **Products** — Add, edit, delete; stock-level badges (green/yellow/red)
- **Customers** — Add, view, delete; email validation
- **Orders** — Create multi-item orders, view details, cancel (with stock restore)
- Responsive design — works on desktop and mobile
- All forms include client-side validation + server error display

---

## Development (Without Docker)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/inventory_db
uvicorn app.main:app --reload
```

### Frontend
Open `frontend/index.html` directly in a browser, or serve with any static server:
```bash
cd frontend
python -m http.server 3000
```
Make sure to update the `API` constant in `index.html` to point to your running backend.
