# CMS Backend (Django REST Framework)

This is the backend API for **Civil Master Solution (CMS)** — a dynamic content management system where all data (products, news, projects, partners, customers, etc.) is managed by the **admin panel**.
Public users can view the website, submit request forms, and interact with an AI-powered chatbot for inquiries.

---

## Features

* Built with Django REST Framework (DRF)
* PostgreSQL (Supabase) integration for data storage
* JWT authentication for secure admin access
* CORS enabled for frontend integration
* AI-Powered Chatbot with Gemini API for Q&A (English and Thai support)
* Easy Request Form submission for public users
* Separate Admin API routes for content management
* Security Features: Rate limiting, honeypot detection, input validation, session management, and logging
* Production-Ready: HTTPS support, caching, and scalability options

### 🔧 Admin can manage:
* Partnerships  
* Customerships  
* Products  
* Request Forms (from public users)  
* Project References  
* News 

### 🤖 Chatbot Features:
* Bilingual support (English/Thai detection and responses)
* 50 questions per session limit, 70-word limit per question
* 30-minute session timeout
* Security: Rate limiting (10/min per session, 50/min per IP), honeypot for bot detection, caching for efficiency
* Powered by Google Gemini API with concurrency control

---

## Tech Stack

| Component             | Technology                       |
| --------------------- | ---------------------            |
| Backend Framework     | Django 5.2                       |
| REST API              | Django REST Framework            |
| Authentication        | JWT (SimpleJWT)                  |
| Database              | PostgreSQL (Supabase)            |
| AI Chatbot            | Google Gemini API                |
| Security              | Rate Limiting, Honeypot, Logging |
| Deployment Ready      | ✅ Yes                          |
| Environment Variables | `.env` file                      |
| Virtual Environment   | Python `venv`                    | 

---

## Installation Guide

### 1. Clone the repository

```bash
git clone https://github.com/civilmastersolution-CMS/cms_testing_backend.git
cd cms-backend
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate it

* **Windows**

  ```bash
  venv\Scripts\activate
  ```
* **Mac/Linux**

  ```bash
  source venv/bin/activate
  ```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Setup environment variables

Create a `.env` file in your project root:

```
password = [Your_Password]

DJANGO_SECRET_KEY = [secret_key]
DEBUG = True
ALLOWED_HOSTS = [your_Host]

# supabase connection
DB_NAME = postgres
DB_USER = postgres
DB_PASSWORD = [your_Password]
DB_HOST = [your_database_host]
DB_PORT = [your_port_number]

# Chatbot API
GEMINI_API_KEY = [your_gemini_api_key]
```

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

### 8. Run the development server

```bash
python manage.py runserver
```

---

## Docker Local Testing

1. Duplicate `.env.docker.example` as `.env.docker` and fill in every secret. Copy the values you already have in `.env`, but remember to add the missing keys (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, `REDIS_URL`, `SUPERUSER_*`, `FRONTEND_URL`, `ADMIN_URL`, `EMAIL_*`). If you prefer to reuse Supabase, set `DATABASE_URL=postgresql://<user>:<pass>@<host>:5432/<db>?sslmode=require` instead of the local Compose connection string.
2. Build the image (only needed the first time or after dependency changes):

  ```bash
  docker compose build web
  ```

3. Start the stack and watch the logs (defaults to Supabase/remote DB if `DATABASE_URL` points there):

  ```bash
  docker compose up -d
  docker compose logs -f web
  ```

  The `docker-entrypoint.sh` script automatically runs migrations and the custom `create_superuser` command on boot. Set `SUPERUSER_USERNAME`, `SUPERUSER_EMAIL`, and `SUPERUSER_PASSWORD` in `.env.docker` if you want the admin user to be created automatically; otherwise the command just prints a warning and skips the step.

  Need the bundled Postgres container instead of Supabase? Start it with the `local-db` profile: `docker compose --profile local-db up -d postgres web redis`.

4. Visit `http://localhost:8000/admin/` to confirm the service is up. API routes use the same hostname/port (e.g., `http://localhost:8000/api/products/`).

5. Tear everything down when finished:

  ```bash
  docker compose down
  ```

### Useful variations

* **Rebuild after code changes:** `docker compose up -d --build`
* **Run a one-off Django command:** `docker compose run --rm web python manage.py shell`
* **Connect to the Postgres shell:** `docker compose exec postgres psql -U cms_admin -d cms_backend`

---

## API Endpoints

| Function            | Endpoint                    | Method |
| ------------------- | --------------------------- | ------ |
| Partnerships        | `/api/partnerships/`        | GET    |
| Customerships       | `/api/customerships/`       | GET    |
| Products            | `/api/products/`            | GET    |
| Request Form        | `/api/requestforms/`        | POST   |
| Project References  | `/api/projectreferences/`   | GET    |
| News                | `/api/news/`                | GET    |
| Django Admin Panel  | `/admin/`                   | Web UI |
| Chatbot             | `/api/chatnot`              | POST   |

---

## Example Request Body

### Request Form

```json
{
    "full_name": "John Doe",
    "email_address": "John@gmail.com",
    "contact_number": "09123456789",
    "company_name": "John company",
    "country": "Japan",
    "product_name": "Unknown",
    "comments": "Optional comment here"
}
```

---
### Security Notes
* Rate Limiting: Protects against abuse (10/min per session, 50/min per IP).
* Honeypot: Detects bots via hidden fields.
* Input Validation: Limits word count and sanitizes inputs.
* Session Management: 30-minute timeouts and 50-message limits.
* Logging: Monitors security events in chatbot_security.log.
* Production: Enable HTTPS, use WAF (e.g., Cloudflare), and set budgets in Google Cloud for Gemini API.
* Audit: Regularly update dependencies and scan for vulnerabilities.

##  Author

**Civil Master Solution (CMS)**
Developed by: *Thantwyl*
Repository: [GitHub - cms_testing_backend](https://github.com/civilmastersolution-CMS/cms_testing_backend.git)

---
