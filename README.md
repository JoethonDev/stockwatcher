# 📈 StockWatcher API

StockWatcher is a Django-powered backend application that lets users monitor selected stock prices and receive alerts when specific conditions are met — without relying on paid APIs or services. It supports threshold and duration-based alerting and is built to scale using Docker, Celery, and Redis.

---

## 🚀 Features

- **✅ JWT Authentication**
  - Secure user registration & login via access/refresh token system.
- **📊 Real-Time Stock Tracking**
  - Monitors 10 predefined companies using a free stock API (e.g., Financial Modeling Prep).
- **⚠️ Smart Alerting**
  - **Threshold Alert**: Alert when price crosses a set value.
  - **Duration Alert**: Alert if price stays above/below a value for X minutes/hours.
- **📧 Notifications**
  - Email alerts via Gmail SMTP or logged to the console (dev mode).
- **📆 Scheduled Checks**
  - Celery Beat runs background tasks to evaluate alerts in real-time.
- **🔧 API-First Architecture**
  - DRF with fully documented Swagger UI.
- **📦 Dockerized**
  - Easily deployable with Docker Compose.
- **🌐 Azure VPS Deployment**
  - Configured and tested to run on a 1 GB Azure VPS using Docker.

---

## 🛠️ Tech Stack

| Layer         | Technology                       |
|---------------|----------------------------------|
| Backend       | Django, Django REST Framework    |
| Auth          | JWT (Custom DRF Authentication)  |
| Tasks         | Celery + Redis                   |
| Database      | PostgreSQL                       |
| Deployment    | Docker, Azure VPS                |
| Docs          | drf-spectacular (Swagger/OpenAPI)|
| Alerts Engine | Custom logic inside Celery tasks |

---

## 📚 API Overview

All API endpoints are prefixed with `/api/`

### 🔐 Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/users/register/`       | Register a new user |
| POST   | `/users/login/`          | Get access & refresh JWTs |
| POST   | `/users/token/refresh/`  | Refresh access token |
| GET    | `/users/me/`             | Get current user & their alerts |

---

### 🏢 Companies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/alerts/companies/` | List all predefined stock symbols |

---

### 🚨 Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/alerts/`                     | List user alerts (filter by `is_active`) |
| POST   | `/alerts/`                     | Create a new alert (threshold or duration) |
| GET    | `/alerts/<id>/`               | Retrieve specific alert |
| DELETE | `/alerts/<id>/`               | Delete alert |
| PATCH  | `/alerts/<id>/reactivate/`    | Reactivate a previously triggered alert |
| GET    | `/alerts/triggered/`          | View alert history |

---

## ⚙️ Local Development

### 1. Clone the Repository

```bash
git clone https://github.com/joethondev/stockwatcher.git
cd stockwatcher
```

---

### 2. Create `.env` File

Use `.env.example` as a template:

```env
# Django
DJANGO_SECRET_KEY=your-secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DB_NAME=stockwatcher
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Redis
CELERY_BROKER_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret

# Email (Console / SMTP)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password

# Stock API
FMP_API_KEY=your-fmp-api-key
```

---

### 3. Build & Run via Docker Compose

```bash
docker-compose up --build
```

---

### 4. Seed Initial Data

Once the containers are running, seed predefined companies and any default data:
```bash
docker-compose exec web python manage.py seed_all_data
```

---

### 5. Run Tests

To run the full Django test suite inside the container:

```bash
docker-compose exec web python manage.py test
```

---

### 6. Access the App

- **API Base**: [http://localhost:8000/api/](http://localhost:8000/api/)
- **Docs**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

---

## ☁️ Azure VPS Deployment

### 1. Launch Ubuntu VPS

- Use a basic 1GB RAM VPS from Azure.
- Allow inbound ports: `22` (SSH), `80` (HTTP), and optionally `443` (HTTPS).

---

### 2. SSH Into Server

```bash
ssh -i /path/to/key.pem your-user@your-server-ip
```

---

### 3. Install Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker ${USER}
```

Log out and log back in for Docker group changes to take effect.

---

### 4. Clone Repo & Set `.env`

```bash
git clone https://github.com/joethondev/stockwatcher.git
cd stockwatcher
nano .env
# (paste your production env config)
```

Set:

- `DEBUG=False`
- `ALLOWED_HOSTS=your_server_ip,your_domain`

---

### 5. Start the App

```bash
docker-compose up --build -d
```

---

### 6. (Optional) Nginx

For production hardening:

- Set up **Nginx** as a reverse proxy
```bash
export NGROK_AUTHTOKEN=$NGROK_AUTHTOKEN
docker run --net=host -it -e NGROK_AUTHTOKEN=${NGROK_AUTHTOKEN} ngrok/ngrok:latest http 8000
```

---

## 🧪 Testing Tips

- Trigger test alerts with mock API data or override price fetch task.
- Use Django Admin to inspect alert statuses if needed.

---

## 🧾 License

This project is open-source and licensed under the MIT License.

---

## 👨‍💻 Author

Built with ❤️ by George Zakhary  
Backend Developer | Django | Azure | Automation  
[LinkedIn](https://www.linkedin.com/) • [GitHub](https://github.com/)