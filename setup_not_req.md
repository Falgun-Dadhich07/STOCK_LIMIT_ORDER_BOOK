Here is a **clean, professional `README.md`** you can directly copy and use in your project.
It matches **your current file structure**, **Docker setup**, and the official documentation .

---

## ✅ **README.md — Interactive Limit Order Book System**

```md
# Interactive Limit Order Book System

This project is a Django-based interactive trading simulator developed by IIT Kanpur (Team FAC).  
It supports Market, Limit, Iceberg, IOC, and Stop-Loss orders with real-time updates using WebSockets.

The system uses:
- Django + Django Channels
- PostgreSQL
- Redis
- Docker & Docker Compose

---

## 🚀 Features

- Real-time Order Book (WebSockets)
- Multiple Order Types
- Admin Dashboard
- Bulk User Upload/Delete
- PostgreSQL Data Storage
- CSV Export
- Redis-backed Channels
- Scalable Architecture

---

## 📁 Project Structure

```

.
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
├── trading_system/
│   ├── manage.py
│   ├── students/
│   ├── trading/
│   └── trading_system/
│       ├── settings.py
│       ├── asgi.py
│       └── urls.py

````

Django root directory: `trading_system/`

---

## 🛠 System Requirements

- Ubuntu 20.04+ / Linux Server
- Docker
- Docker Compose
- Minimum 4GB RAM

---

## 🔧 Step 1: Install Docker & Docker Compose

Run on server:

```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo systemctl enable docker
````

Add user to Docker group:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## 🔧 Step 2: Clone Repository

```bash
git clone <your-repo-url>
cd <project-folder>
```

Or upload manually using SCP.

---

## 🔧 Step 3: Create Environment File

Create `.env` in project root:

```bash
nano .env
```

Add:

```env
DEBUG=0
SECRET_KEY=change-this-secret

DB_NAME=trading_platform
DB_USER=trading_user
DB_PASSWORD=trading_pass
DB_HOST=db
DB_PORT=5432

REDIS_HOST=redis
```

Save and exit.

---

## 🔧 Step 4: Configure Database & Redis (settings.py)

Edit:

```bash
nano trading_system/trading_system/settings.py
```

### Database Configuration

```python
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("DB_NAME"),
        'USER': os.getenv("DB_USER"),
        'PASSWORD': os.getenv("DB_PASSWORD"),
        'HOST': os.getenv("DB_HOST"),
        'PORT': os.getenv("DB_PORT"),
    }
}
```

### Channels Configuration

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.getenv("REDIS_HOST"), 6379)],
        },
    },
}
```

### Allowed Hosts

```python
ALLOWED_HOSTS = ["*"]
```

---

## 🔧 Step 5: Build Docker Containers

```bash
docker-compose build
```

---

## ▶️ Step 6: Start Application

```bash
docker-compose up -d
```

Check status:

```bash
docker ps
```

---

## 🗄 Step 7: Setup Database (Migrations)

Run:

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

This will create all database tables automatically.

---

## 👤 Step 8: Create Admin User

```bash
docker-compose exec web python manage.py createsuperuser
```

Enter username, email, and password.

---

## 🌐 Step 9: Access Application

Open browser:

```
http://SERVER_IP:8000
```

Admin Panel:

```
http://SERVER_IP:8000/admin
```

---

## 🔐 Firewall Configuration (If Enabled)

```bash
sudo ufw allow 8000
sudo ufw reload
```

---

## 📊 Database & Redis Setup

PostgreSQL and Redis are automatically configured using Docker.

No manual installation is required.

Services:

| Service    | Container     |
| ---------- | ------------- |
| Django App | trading_web   |
| PostgreSQL | trading_db    |
| Redis      | trading_redis |

Database data is stored persistently using Docker volumes.

---

## 🔄 Common Commands

### Restart Services

```bash
docker-compose restart
```

### Stop Services

```bash
docker-compose down
```

### View Logs

```bash
docker-compose logs web
```

### Enter Django Shell

```bash
docker-compose exec web python manage.py shell
```

---

## 📧 Email Configuration (Optional)

For bulk user email, configure in `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_password'
```

---

## 📦 Backup Database

```bash
docker-compose exec db pg_dump -U trading_user trading_platform > backup.sql
```

---

## ♻ Restore Database

```bash
docker-compose exec -T db psql -U trading_user trading_platform < backup.sql
```

---

## 🚨 Troubleshooting

### Check Logs

```bash
docker-compose logs -f web
```

### Restart Everything

```bash
docker-compose down -v
docker-compose build
docker-compose up -d
```

---

## 📞 Support

For queries, contact:
Finance and Analytics Club, IIT Kanpur
📧 [fac_snt@iitk.ac.in](mailto:fac_snt@iitk.ac.in)

---

## ✅ Deployment Status

Once all steps are completed:

✔ Application running
✔ Database connected
✔ Redis active
✔ WebSockets enabled
✔ Admin configured
