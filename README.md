# Study Vault Backend

Study Vault is an academic organization system designed for university and college students. It provides a structured, hierarchical model for organizing academic coursework, continuous assessment tests (CATs), assignments, notes, and deadlines, along with an intelligent reminder and offline notification synchronization engine.

---

## Academic Hierarchy & Core Limits

The backend strictly enforces the following academic organization tree:

```text
User
 └── Academic Year (Max 6 per user)
       └── Semester (Max 3 per Academic Year)
             └── Unit (Max 10 per Semester)
                   ├── Notes
                   ├── CATs (Continuous Assessment Tests)
                   └── Assignments
                         └── Reminders (1 automatic default + max 2 additional = max 3 per assessment)
```

### Hierarchy Rules

1. **Academic Years**: A user can create a maximum of **6 Academic Years**. Creation of a 7th is rejected.
2. **Semesters**: Each Academic Year can contain a maximum of **3 Semesters**. Creation of a 4th is rejected.
3. **Units**: Each Semester can contain a maximum of **10 Units**. Creation of an 11th is rejected.
4. **Reminders**: Every CAT and Assignment automatically receives **1 default reminder** named `Unit Name - Deadline` (e.g. `Programming for Internet - 2026-10-20`). The user may add up to **2 additional manual reminders**, capping total reminders at **3 per CAT or Assignment**. Modifying the deadline updates the automatic reminder consistently without duplicate creations.
5. **Strict Data Ownership**: Users can only access, modify, or delete their own data. Cross-user access is blocked at the database query level.

---

## Technology Stack

- **Language**: Python 3.12
- **Framework**: Django 5.2 / 6.1 (Latest compatible)
- **API Framework**: Django REST Framework (DRF)
- **Authentication**: JSON Web Tokens (SimpleJWT with token blacklisting)
- **Database**: PostgreSQL (Strict production database; tested via isolated in-memory runner)
- **CORS**: django-cors-headers
- **Configuration**: python-dotenv, dj-database-url

---

## Project Structure

```text
studyvault-be/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── config/                     # Core Django project settings & routing
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── accounts/                   # Custom User model & JWT authentication
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── exceptions.py           # Consistent {"detail": "..."} error formatter
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── academics/                  # AcademicYear, Semester, and Unit models
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── notes/                      # Academic unit notes
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── assessments/                # CATs and Assignments
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
└── reminders/                  # Reminder system & mobile sync engine
    ├── migrations/
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── serializers.py
    ├── signals.py              # Automatic default reminder sync handlers
    ├── tests.py
    ├── urls.py
    └── views.py
```

---

## Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configurable variables in `.env`:

| Variable | Description | Default |
| --- | --- | --- |
| `SECRET_KEY` | Django cryptographic signing key | (Set your own secret string) |
| `DEBUG` | Development mode toggle (`True` or `False`) | `True` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames | `localhost,127.0.0.1,0.0.0.0` |
| `DB_NAME` | PostgreSQL database name | `studyvault_db` |
| `DB_USER` | PostgreSQL user | `postgres` |
| `DB_PASSWORD` | PostgreSQL user password | (Your password) |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DATABASE_URL` | Full PostgreSQL connection URL (optional) | `postgres://user:pass@host:5432/dbname` |
| `CORS_ALLOWED_ORIGINS` | Permitted origins for mobile/web apps | `http://localhost:3000,http://127.0.0.1:3000` |
| `ACCESS_TOKEN_LIFETIME_MINUTES`| Lifetime for JWT access token | `60` |
| `REFRESH_TOKEN_LIFETIME_DAYS`  | Lifetime for JWT refresh token | `7` |

---

## Setup & Installation Instructions

Follow these step-by-step instructions to get the backend running locally.

### 1. Create and Activate a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure PostgreSQL Database

Create the PostgreSQL database using `psql` or pgAdmin:

```sql
CREATE DATABASE studyvault_db;
CREATE USER studyvault_user WITH PASSWORD 'your_secure_password';
ALTER ROLE studyvault_user SET client_encoding TO 'utf8';
ALTER ROLE studyvault_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE studyvault_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE studyvault_db TO studyvault_user;
```

Update your `.env` file with these credentials.

### 4. Run Database Migrations

Apply the migration files to the database:

```bash
python manage.py migrate
```

### 5. Create a Superuser (Admin)

```bash
python manage.py createsuperuser
```

### 6. Start the Development Server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.  
The Django Admin interface is at `http://127.0.0.1:8000/admin/`.

---

## Running the Automated Test Suite

To run the complete test suite:

```bash
python manage.py test
```

The test runner utilizes an in-memory SQLite database and fast password hashing, completing the entire suite in ~1 second without modifying or needing access to your production PostgreSQL database.

---

## API Documentation & Endpoints

All protected endpoints require the following header:
```text
Authorization: Bearer <access_token>
```

### 1. Authentication (`/api/auth/`)

| Method | Endpoint | Description | Auth Required |
| --- | --- | --- | --- |
| `POST` | `/api/auth/register/` | Register student, returns user profile + JWT tokens | No |
| `POST` | `/api/auth/login/` | Log in with credentials, returns JWT tokens | No |
| `POST` | `/api/auth/logout/` | Blacklists refresh token | Yes |
| `POST` | `/api/auth/token/refresh/` | Obtain a new access token using refresh token | No |
| `GET` | `/api/auth/me/` | Retrieve authenticated user profile | Yes |
| `PATCH` | `/api/auth/me/` | Update authenticated user profile | Yes |

#### Registration Request Body
```json
{
  "username": "johndoe",
  "email": "johndoe@university.edu",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

---

### 2. Academic Years (`/api/academic-years/`)

Enforces maximum **6** academic years per user.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/academic-years/` | List all academic years for user |
| `POST` | `/api/academic-years/` | Create a new academic year (max 6) |
| `GET` | `/api/academic-years/{id}/` | Retrieve an academic year |
| `PUT`/`PATCH` | `/api/academic-years/{id}/` | Update an academic year |
| `DELETE` | `/api/academic-years/{id}/` | Delete academic year (Cascades) |

#### Create Academic Year
```json
{
  "name": "Year 1 (2025/2026)",
  "start_date": "2025-09-01",
  "end_date": "2026-06-30"
}
```

---

### 3. Semesters (`/api/semesters/`)

Enforces maximum **3** semesters per academic year.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/semesters/` | List semesters (supports `?academic_year={id}`) |
| `POST` | `/api/semesters/` | Create a new semester (max 3 per year) |
| `GET` | `/api/semesters/{id}/` | Retrieve a semester |
| `PUT`/`PATCH` | `/api/semesters/{id}/` | Update a semester |
| `DELETE` | `/api/semesters/{id}/` | Delete a semester (Cascades) |

#### Create Semester
```json
{
  "academic_year": 1,
  "name": "Semester 1"
}
```

---

### 4. Units (`/api/units/`)

Enforces maximum **10** units per semester.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/units/` | List units (supports `?semester={id}`) |
| `POST` | `/api/units/` | Create a new unit (max 10 per semester) |
| `GET` | `/api/units/{id}/` | Retrieve a unit |
| `PUT`/`PATCH` | `/api/units/{id}/` | Update a unit |
| `DELETE` | `/api/units/{id}/` | Delete a unit (Cascades) |

#### Create Unit
```json
{
  "semester": 1,
  "name": "Programming for Internet",
  "code": "CS101",
  "description": "Full-stack web application development"
}
```

---

### 5. Notes (`/api/notes/`)

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/notes/` | List notes (supports `?unit={id}`) |
| `POST` | `/api/notes/` | Create a note for a unit |
| `GET` | `/api/notes/{id}/` | Retrieve a note |
| `PUT`/`PATCH` | `/api/notes/{id}/` | Update a note |
| `DELETE` | `/api/notes/{id}/` | Delete a note |

#### Create Note
```json
{
  "unit": 1,
  "title": "Django ORM and Serializers",
  "content": "Key takeaways on select_related and validation..."
}
```

---

### 6. CATs (Continuous Assessment Tests) (`/api/cats/`)

Creating a CAT automatically schedules 1 default reminder: `Unit Name - Deadline`.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/cats/` | List CATs (supports `?unit={id}`) |
| `POST` | `/api/cats/` | Create a new CAT |
| `GET` | `/api/cats/{id}/` | Retrieve a CAT |
| `PUT`/`PATCH` | `/api/cats/{id}/` | Update a CAT (updates default reminder) |
| `DELETE` | `/api/cats/{id}/` | Delete a CAT (Cascades reminders) |

#### Create CAT
```json
{
  "unit": 1,
  "title": "Mid-Semester CAT",
  "description": "Covers chapters 1 to 5",
  "cat_date": "2026-10-20",
  "deadline": "2026-10-20T10:00:00Z"
}
```

---

### 7. Assignments (`/api/assignments/`)

Creating an Assignment automatically schedules 1 default reminder: `Unit Name - Deadline`.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/assignments/` | List assignments (supports `?unit={id}&status={status}`) |
| `POST` | `/api/assignments/` | Create a new assignment |
| `GET` | `/api/assignments/{id}/` | Retrieve an assignment |
| `PUT`/`PATCH` | `/api/assignments/{id}/` | Update assignment (updates default reminder) |
| `DELETE` | `/api/assignments/{id}/` | Delete assignment (Cascades reminders) |

#### Create Assignment
```json
{
  "unit": 1,
  "title": "REST API Coursework",
  "description": "Build an authenticated REST backend",
  "deadline": "2026-11-15T23:59:59Z",
  "status": "PENDING"
}
```

---

### 8. Reminders & Mobile Synchronization (`/api/reminders/`)

Enforces maximum **3** reminders per CAT or Assignment (1 automatic + max 2 manual).

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/reminders/` | List user reminders (supports `?cat={id}`, `?assignment={id}`) |
| `POST` | `/api/reminders/` | Create a manual reminder (max 2 manual) |
| `GET` | `/api/reminders/{id}/` | Retrieve a reminder |
| `PATCH` | `/api/reminders/{id}/` | Mark completed (`is_completed`) or read (`is_read`) |
| `DELETE` | `/api/reminders/{id}/` | Delete a reminder |
| `GET` | `/api/reminders/sync/` | Mobile synchronization endpoint |

#### Create Manual Reminder
```json
{
  "assignment": 1,
  "title": "Submit draft to instructor",
  "reminder_datetime": "2026-11-10T14:00:00Z"
}
```

#### Mobile Offline Sync Endpoint (`/api/reminders/sync/`)
The Flutter mobile application queries this endpoint (optionally passing `?updated_since=2026-10-01T00:00:00Z`) to receive all reminders to schedule as local Android/iOS notifications on the device:

```json
{
  "server_time": "2026-10-03T07:15:00.000000Z",
  "count": 2,
  "reminders": [
    {
      "id": 1,
      "cat_id": null,
      "assignment_id": 1,
      "assessment_type": "ASSIGNMENT",
      "assessment_id": 1,
      "unit_name": "Programming for Internet",
      "unit_code": "CS101",
      "title": "Programming for Internet - 2026-11-15",
      "reminder_datetime": "2026-11-15T23:59:59Z",
      "reminder_type": "AUTOMATIC",
      "is_completed": false,
      "is_read": false,
      "updated_at": "2026-10-03T07:10:00.000000Z"
    }
  ]
}
```

---

## Consistent Error Responses

All validation and business constraint violations return consistent JSON objects with a `"detail"` message:

```json
{
  "detail": "You can have a maximum of 6 academic years."
}
```
```json
{
  "detail": "An academic year can contain a maximum of 3 semesters."
}
```
```json
{
  "detail": "A semester can contain a maximum of 10 units."
}
```
```json
{
  "detail": "A CAT or Assignment can have a maximum of 3 reminders."
}
```
