# IIM-A-Project-FAC — Stock Limit Order Book

A web-based trading system that simulates a stock limit order book. Users can place, modify, and cancel buy/sell orders with real-time updates. Includes an automated **Market Maker** feature for regular users.

## Features

- User registration, login, and password reset
- Place buy, sell, limit, market, IOC, and stop-loss orders
- Market Maker — auto-place layered buy/sell orders around a reference price
- Modify or cancel existing orders
- Real-time order book and trade updates via WebSockets (Redis)
- Bulk user creation and deletion via CSV (admin only)
- Download trades as CSV
- Interactive price chart and tabbed dashboard

---

## 🚀 Deploy to Railway (Recommended)

Railway handles PostgreSQL and Redis automatically. Deploy in under 5 minutes:

### Step 1 — Fork & connect to Railway

1. Fork this repository.
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → select your fork.

### Step 2 — Add services

In your Railway project, click **+ New** to add:

- **PostgreSQL** — Railway automatically injects `DATABASE_URL`
- **Redis** — Railway automatically injects `REDIS_URL`

### Step 3 — Set environment variables

In your Railway project → **Variables**, add:

| Variable | Value |
|---|---|
| `SECRET_KEY` | A long random string (generate at [djecrety.ir](https://djecrety.ir)) |
| `DEBUG` | `0` |
| `ALLOWED_HOSTS` | `*` |
| `CSRF_TRUSTED_ORIGINS` | `https://yourapp.up.railway.app` (your Railway URL) |

> **Note:** `DATABASE_URL` and `REDIS_URL` are set automatically by Railway plugins — do **not** add them manually.

### Step 4 — Deploy

Railway will:
1. Install dependencies from `requirements.txt`
2. Run `collectstatic`
3. Run `migrate`
4. Start the Daphne ASGI server

Your app will be live at `https://yourapp.up.railway.app`.

### Step 5 — Create an admin account

Open the Railway shell (or use the **Railway CLI**):

```sh
railway run --service web -- sh -c "cd trading_system && python manage.py createsuperuser"
```

Or visit `/admin/` and follow the prompts after Railway auto-creates the default admin (`admin` / `admin123`).

---

## 🐳 Docker Setup (Local)

```sh
docker-compose up --build
```

App available at `http://localhost:8000`.

Create admin:
```sh
docker-compose exec web python manage.py createsuperuser
```

Stop:
```sh
docker-compose down
```

---

## 🛠 Manual Local Setup

```sh
# 1. Clone
git clone <repository-url>
cd STOCK_LIMIT_ORDER_BOOK

# 2. Virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start Redis
sudo apt install redis-server && redis-server --daemonize yes

# 5. Configure environment
cp trading_system/.env.example trading_system/.env
# Edit .env with your settings

# 6. Database
cd trading_system
python manage.py migrate
python manage.py createsuperuser

# 7. Run
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

---

## Usage

- Register or log in to access the trading dashboard.
- Place **limit / market / IOC / stop-loss** orders.
- Use **Market Maker** to automatically quote bid/ask prices.
- Admin users can open/close the market, bulk-upload users, and download trade data.

## Contributing

1. Fork the repository
2. Create a branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push and open a pull request

## License

MIT License — see [LICENSE](LICENSE) for details.

