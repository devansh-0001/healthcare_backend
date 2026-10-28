# Synora Healthcare Backend API

> **Healthcare designed around you**: Secure, multi-specialty clinic platform API connecting patients, doctors, and care coordination teams.

Built with **Django 5**, **Django REST Framework (DRF)**, **PostgreSQL** (with zero-config SQLite development mode), and **SimpleJWT**. Includes an integrated reference UI modeled faithfully after the Synora design specification.

---

## Table of Contents
1. [Core Features](#core-features)
2. [Quickstart (Setup in Under 5 Minutes)](#quickstart-setup-in-under-5-minutes)
3. [Configuration & Environment Variables](#configuration--environment-variables)
4. [API Endpoints Reference](#api-endpoints-reference)
5. [Error Handling Standard](#error-handling-standard)
6. [Testing & Code Coverage](#testing--code-coverage)
7. [Postman Collection](#postman-collection)
8. [Interactive Synora Reference UI](#interactive-synora-reference-ui)
9. [Architecture & Project Structure](#architecture--project-structure)

---

## 1. Core Features

- **Authentication & Security**: Custom User model with email as unique identifier (stored lowercase). JWT authentication with 30-minute access token and 1-day refresh token lifetimes. Password validation with Django security validators (hashed with PBKDF2, never exposed). Throttling enabled on auth endpoints (10 req/min per IP).
- **Patient Management**: Full CRUD for patient demographics (`name`, `age`, `gender`, `phone`, `address`, `medical_history`). Scoped strictly to the creating user. Attempting to access another user's patient returns `404 Not Found` (never `403`) to prevent existence leakage.
- **Doctor Directory**: Shared medical specialist directory readable by all authenticated users. Supports filtering by `?specialization=Cardiology`, full-text search `?search=Dr.+Sarah`, and pagination. Updates and deletions are restricted strictly to the physician's creator (`403 Forbidden` for other users).
- **Patient-Doctor Care Mappings**: Assign doctors to patients with database uniqueness constraints (`unique_together`). Prevents duplicate doctor assignments (`400 Bad Request`). Deleting an assignment preserves the doctor and patient records. Deleting a patient cascades and removes all associated mappings.
- **Performance Optimizations**: Database indexing on `Patient.created_by`, `Doctor.specialization`, `Doctor.email`, and `Mapping.patient`. List endpoints paginated (page size 10). Mappings use `select_related('patient', 'doctor')` to eliminate N+1 queries. Atomic database transactions (`transaction.atomic`) on multi-model write operations.
- **Standardized Error Responses**: All API errors conform to a consistent JSON format with actionable error codes, messages, and field-level validation details.

---

## 2. Quickstart (Setup in Under 5 Minutes)

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Optional: PostgreSQL (SQLite is enabled by default for zero-configuration testing)

### Step 1: Clone the repository & enter directory
```bash
git clone <repository-url>
cd HealthCare_Backend
```

### Step 2: Create and activate virtual environment
**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```
**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment setup
Copy the provided `.env.example` file to `.env`:
```bash
cp .env.example .env
```
*(On Windows PowerShell: `Copy-Item .env.example .env`)*

### Step 5: Apply migrations & seed demo data
```bash
python manage.py migrate
python manage.py seed_data
```

The `seed_data` command creates:
- **Demo User**: `dev@example.com` / `StrongPass#123`
- **6 Specialists**: Cardiology, Neurology, Internal Medicine, Orthopedics, Pediatrics, Dermatology
- **3 Patients**: Eleanor Vance, Marcus Sterling, Aria Montgomery
- **Initial Care Team Mappings**

### Step 6: Start the development server
```bash
python manage.py runserver
```
Visit **`http://127.0.0.1:8000/`** to interact with the platform UI or test endpoints directly.

---

## 3. Configuration & Environment Variables

All settings are configured via `.env` (git-ignored, template in `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `django-insecure-...` | Django cryptographic signing key |
| `DEBUG` | `True` | Debug flag (`False` in production) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated list of permitted hosts |
| `DB_ENGINE` | `sqlite3` | `sqlite3` or `postgresql` |
| `DB_NAME` | `synora_db` | PostgreSQL database name |
| `DB_USER` | `postgres` | PostgreSQL username |
| `DB_PASSWORD` | `postgres` | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host (leave blank for SQLite) |
| `DB_PORT` | `5432` | PostgreSQL port |
| `JWT_ACCESS_MINUTES` | `30` | Access token lifespan in minutes |
| `JWT_REFRESH_DAYS` | `1` | Refresh token lifespan in days |
| `CORS_ALLOWED_ORIGINS`| `http://localhost:3000,...` | Whitelisted cross-origin domains |

---

## 4. API Endpoints Reference

### 4.1 Authentication (Public)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Register new user | No |
| `POST` | `/api/auth/login/` | Sign in, receive JWT access & refresh tokens | No |
| `POST` | `/api/auth/token/refresh/` | Obtain new access token via refresh token | No |

#### Register Request
```json
POST /api/auth/register/
{
  "name": "Devansh",
  "email": "dev@example.com",
  "password": "StrongPass#123"
}
```
**Response (201 Created):**
```json
{
  "id": 1,
  "name": "Devansh",
  "email": "dev@example.com"
}
```

#### Login Request
```json
POST /api/auth/login/
{
  "email": "dev@example.com",
  "password": "StrongPass#123"
}
```
**Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "name": "Devansh",
    "email": "dev@example.com"
  }
}
```

---

### 4.2 Patient Management (Protected — Owner Only)

*Headers required: `Authorization: Bearer <access_token>`*

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `POST` | `/api/patients/` | Create patient (owner set to request.user) | `201 Created` |
| `GET` | `/api/patients/` | List only requesting user's patients (page size 10) | `200 OK` |
| `GET` | `/api/patients/{id}/` | Retrieve patient by ID (404 for non-owners) | `200 OK` / `404` |
| `PUT` | `/api/patients/{id}/` | Update patient record (404 for non-owners) | `200 OK` / `404` |
| `DELETE`| `/api/patients/{id}/` | Delete patient & cascade mappings (404 for non-owners) | `204 No Content` / `404` |

#### Create Patient Request
```json
POST /api/patients/
{
  "name": "Eleanor Vance",
  "age": 42,
  "gender": "female",
  "phone": "+15551234567",
  "address": "742 Evergreen Terrace, Springfield",
  "medical_history": "Stage 1 Hypertension, seasonal pollen allergies"
}
```

---

### 4.3 Doctor Management (Protected — Shared Directory)

*Headers required: `Authorization: Bearer <access_token>`*

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `POST` | `/api/doctors/` | Register new doctor (creator recorded) | `201 Created` |
| `GET` | `/api/doctors/` | List all doctors (supports `?specialization=` and `?search=`) | `200 OK` |
| `GET` | `/api/doctors/{id}/` | Retrieve doctor details | `200 OK` |
| `PUT` | `/api/doctors/{id}/` | Update doctor (creator only; 403 for others) | `200 OK` / `403` |
| `DELETE`| `/api/doctors/{id}/` | Delete doctor (creator only; 403 for others) | `204 No Content` / `403` |

#### Create Doctor Request
```json
POST /api/doctors/
{
  "name": "Sarah Jenkins",
  "specialization": "Cardiology",
  "email": "sarah.jenkins@synora.clinic",
  "phone": "+15551112233",
  "experience_years": 15,
  "hospital": "Synora Heart Institute",
  "is_available": true
}
```

---

### 4.4 Patient-Doctor Care Mappings (Protected)

*Headers required: `Authorization: Bearer <access_token>`*

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `POST` | `/api/mappings/` | Assign doctor to user's patient | `201 Created` |
| `GET` | `/api/mappings/` | List all mappings for user's patients | `200 OK` |
| `GET` | `/api/mappings/{patient_id}/` | List all doctors assigned to patient (404 for non-owners) | `200 OK` / `404` |
| `DELETE`| `/api/mappings/{id}/` | Remove assignment by mapping ID (404 for non-owners) | `204 No Content` / `404` |

#### Assign Doctor Request
```json
POST /api/mappings/
{
  "patient": 1,
  "doctor": 2
}
```

**Rules:**
- Patient must belong to the requesting user (`404` if not found or unauthorized).
- Duplicate assignment of the same doctor to the same patient is rejected with `400 Bad Request`.
- Deleting a mapping removes only the assignment. Deleting a patient cascades mappings.

---

### 4.5 Platform Overview & Stats (Public)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/stats/` | Returns platform counts for patients, doctors, departments, and satisfaction rating |

---

## 5. Error Handling Standard

Every error returned by the API follows the uniform contract:
```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid input",
    "details": {
      "email": ["Enter a valid email address."]
    }
  }
}
```

### HTTP Status Code Mapping
- **`400 Bad Request`**: Validation failure or duplicate doctor assignment (`code: "validation_error"`).
- **`401 Unauthorized`**: Missing, invalid, or expired JWT bearer token (`code: "authentication_failed"`).
- **`403 Forbidden`**: Authenticated user attempting to modify another user's doctor record (`code: "permission_denied"`).
- **`404 Not Found`**: Resource does not exist or patient record belongs to another user (`code: "not_found"`).
- **`409 Conflict`**: Unique conflict such as duplicate email during registration or doctor creation (`code: "conflict"`).
- **`429 Too Many Requests`**: Throttling limit exceeded (`code: "throttled"`).
- **`500 Internal Server Error`**: Generic error message; server-side trace logged only (`code: "server_error"`).

---

## 6. Testing & Code Coverage

The project contains a thorough test suite verifying authentication, permission boundaries, 404 security containment, cascade deletions, search/filtering, and edge-case validations.

### Run Tests
```bash
python manage.py test
```

### Run Coverage Analysis
```bash
coverage run --source='apps' manage.py test
coverage report
```

### Coverage Report Summary
```
Name                       Stmts   Miss  Cover
----------------------------------------------
apps\doctors\...              56      1    98%
apps\mappings\...             60      1    98%
apps\patients\...             62      1    98%
apps\users\...                79      2    97%
----------------------------------------------
TOTAL (apps)                 686     30    96%
```
*Total test coverage across apps: **96%** (exceeds the 80% requirement).*

---

## 7. Postman Collection

The repository includes a ready-to-import Postman collection: **`postman_collection.json`**.

### How to Use:
1. Open Postman -> Click **Import** -> Select `postman_collection.json`.
2. The collection includes preconfigured collection variables:
   - `baseUrl`: defaults to `http://127.0.0.1:8000`.
   - `accessToken`: automatically set upon executing the **Login** request.
   - `patientId`, `doctorId`, `mappingId`: automatically captured by creation requests.
3. Execute **Login (Get JWT)** under `1. Authentication` — subsequent requests will automatically inherit the Bearer token.

---

## 8. Interactive Synora Reference UI

The application includes a lightweight reference UI at **`http://127.0.0.1:8000/`** designed in harmony with the Synora brand guide:
- **Visuals**: Floating pill navigation bar with frosted glass effect, soft blurred pastel gradients (teal, blush pink, peach), and 20–28px rounded cards.
- **Hero & Live Stats**: Dynamic metrics for patients served, board-certified specialists, and medical departments pulled live from `/api/stats/`.
- **Feature Carousel**: Photographic cards for Comprehensive Care, Collaborative Doctors, Modern Diagnostics, and Convenient Scheduling.
- **Specialty Grid**: 6 interactive specialty cards (Cardiology, Neurology, Internal Medicine, Orthopedics, Pediatrics, Dermatology) with 1-click filtering.
- **Authenticated Care Portal**:
  - Interactive JWT Login & Registration modals.
  - Patient management table (Add, Edit, Delete).
  - Doctor directory with live search and specialty filter.
  - Doctor Assignment modal with duplicate prevention.
  - Patient Care Team drawer with one-click doctor removal.
  - Toast notifications and inline error validation alerts.

---

## 9. Architecture & Project Structure

```
HealthCare_Backend/
├── config/
│   ├── settings.py           # Base, DB, JWT, CORS, REST Framework settings
│   ├── urls.py               # Main URL routing (APIs + Reference UI)
│   ├── wsgi.py               # WSGI application entrypoint
│   └── __init__.py
├── apps/
│   ├── users/                # Custom User model, auth views, serializers, seed command
│   ├── patients/             # Patient model, owner-scoped viewset, validations
│   ├── doctors/              # Doctor model, filters, search, creator-only permissions
│   ├── mappings/             # PatientDoctorMapping model, atomic assignments, care team lookup
│   └── __init__.py
├── common/
│   ├── exceptions.py         # Standardized exception handler ({error: {code, message, details}})
│   ├── pagination.py         # StandardResultsSetPagination (10 per page)
│   ├── permissions.py        # IsCreatorOrReadOnly, IsOwnerOnly
│   ├── views.py              # StatsView, IndexView (UI template)
│   └── __init__.py
├── templates/
│   └── index.html            # Synora reference UI template
├── static/                   # Static assets
├── requirements.txt          # Python dependencies
├── .env.example              # Example environment configuration
├── postman_collection.json   # Full Postman API test collection
└── README.md                 # Project documentation
```
