# SkillLink

An on-demand home services / local skilled-worker booking marketplace, built with Django 5,
SQLite, Bootstrap 5, and vanilla JavaScript. Built as a final-year B.Sc. Information
Technology project.

Three roles share one platform:

- **Customers** browse service categories, raise booking requests, track status, and leave reviews.
- **Providers** register under a category, manage incoming and active jobs, and build a rating history.
- **Admins** oversee categories, users, providers, and platform-wide booking statistics.

---

## 1. Tech Stack

- Python 3.12+, Django 5.1
- SQLite (default; swappable for PostgreSQL/MySQL in production settings)
- Bootstrap 5 + Bootstrap Icons (vendored locally — no CDN dependency)
- Vanilla JavaScript (Bootstrap bundle, form validation, lightweight status polling)
- Django Template Engine

## 2. Architecture

- **Modular Django apps**, one per module, each owning its own models/forms/views/urls/admin/templates/tests:
  `accounts`, `categories`, `customers`, `providers`, `bookings`, `reviews`, `dashboard`, plus a shared `core` app.
- **Service layer**: `apps/bookings/services.py` centralises the booking status state machine
  (create → accept → in_progress → completed, plus cancel) so every entry point — views today,
  an API tomorrow — enforces the same transition rules and writes the same audit trail.
- **Split settings**: `config/settings/base.py`, `development.py`, `production.py` — switch
  environments via `DJANGO_SETTINGS_MODULE` only.
- **Custom authentication backend** (`apps/accounts/backends.py`): login by username *or* email.
- **Role-based access control**: `RoleRequiredMixin` (class-based views) and `role_required`
  (function-based views) in `apps/core`.
- **Reusable components**: custom middleware (request logging, login rate limiting), a context
  processor (role + notification count on every page), and a `status_badge` template filter.

## 3. Folder Structure

```
service_provided_webapp/
├── manage.py
├── requirements.txt
├── .env.example
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/            # middleware, mixins, decorators, template tags, seed command
│   ├── accounts/        # auth, registration, OTP password reset, profile
│   ├── categories/      # ServiceCategory CRUD (admin) + public browsing
│   ├── customers/       # CustomerProfile + customer dashboard
│   ├── providers/       # ProviderProfile + provider dashboard/profile setup
│   ├── bookings/        # Booking, BookingStatusLog, state-machine service layer
│   ├── reviews/         # Review model, submission, provider review listing
│   └── dashboard/       # Admin dashboard, user/provider management
├── templates/
│   ├── layouts/           # base.html, admin_base.html (sidebar shell), auth_base.html
│   ├── components/        # navbar, sidebar, footer, cards, modal, alerts, pagination,
│   │                       # breadcrumbs, searchbar, statistics, empty_state, loading, form_fields
│   ├── errors/             # 404.html, 403.html, 500.html
│   └── home.html, about.html, contact.html
├── static/
│   ├── css/               # variables, base, typography, layout, navbar, sidebar, footer,
│   │                       # cards, buttons, forms, tables, dashboard, animations,
│   │                       # responsive, admin, components (16 files, design-token driven)
│   ├── js/                # app, navbar, dashboard, booking, animation, toast (6 files)
│   └── vendor/             # Bootstrap, Bootstrap Icons, Poppins (all local, no CDN)
└── media/                # provider_profile_photos/
```

### 3.1 Frontend Architecture

The UI layer is a **premium SaaS-style design system** (Stripe/Linear/Vercel-inspired):
glassmorphism navbar, gradient-glow buttons, floating background shapes, CSS-only 3D
hover-tilt cards, animated counters, and scroll-reveal micro-interactions — all built with
plain CSS custom properties (`static/css/variables.css`) and vanilla JS, no build step.

Every app template extends one of three layouts:
- `layouts/base.html` — public pages + customer/provider dashboards (navbar + footer)
- `layouts/admin_base.html` — admin panel (adds the sidebar shell from `components/sidebar.html`)
- `layouts/auth_base.html` — login/register/password-reset (centered glass card, no navbar)

This was a **frontend-only reorganization**: no changes to models, migrations, URLs,
views' business logic, authentication, or permissions — every context variable name a view
passes to its template stayed exactly the same, so all 48 automated tests still pass unchanged.

## 4. Installation Steps

### 4.1 Virtual Environment Setup

```bash
cd service_provided_webapp
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 4.2 Dependency Installation

```bash
pip install -r requirements.txt
```

### 4.3 Environment File

```bash
cp .env.example .env
# Edit .env if needed — the defaults work out of the box for local development.
```

### 4.4 Database Migration Commands

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4.5 Create Superuser Command

```bash
python manage.py createsuperuser
```

### 4.6 Seed Demo Data Command

```bash
python manage.py seed_demo_data
```

This creates 7 service categories, 3 demo customers, 5 demo providers (one per category),
and 6 bookings covering every status (pending/accepted/in_progress/completed/cancelled) plus
reviews on completed bookings.

### 4.7 Run Server Command

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/**.

### 4.8 Run Tests

```bash
python manage.py test
```

48 tests across all 7 apps — registration/login/OTP reset, role-based access control, the full
booking state machine (including invalid-transition and permission edge cases), reviews, and
admin management actions.

---

## 5. Default Demo Accounts

Password for every seeded account: **`DemoPass123`**

| Role | Username | Category |
|---|---|---|
| Customer | `meena_h` | — |
| Customer | `arjun_r` | — |
| Customer | `divya_k` | — |
| Provider | `suresh_p` | Plumbing |
| Provider | `ravi_e` | Electrical |
| Provider | `lakshmi_c` | Cleaning |
| Provider | `mani_p` | Painting |
| Provider | `kumar_s` | AC Repair |

The admin account is whatever you created with `createsuperuser` in step 4.5.

---

## 6. Security Features

- CSRF protection on every form (Django's built-in middleware + `{% csrf_token %}`)
- XSS protection via Django's auto-escaping templates
- SQL injection protection via the Django ORM (no raw SQL anywhere)
- Password hashing via Django's PBKDF2 hasher (default)
- Login rate limiting: 5 failed attempts per IP locks further attempts for 5 minutes
  (`apps/core/middleware.py`)
- OTP-based password reset with a 10-minute expiry window
- Server-side input validation on every form (`apps/*/forms.py`)
- File upload validation for provider profile photos: JPEG/PNG only, max 2MB

## 7. Booking Status Flow

```
Pending → Accepted → In Progress → Completed
   ↓          ↓
Cancelled  Cancelled
```

Enforced centrally in `apps/bookings/services.py`:
- Only a provider whose category matches the booking may accept it (first-come, first-served,
  row-locked to prevent a race between two providers).
- Only the assigned provider may advance a booking's status, and only forward, one step at a time.
- Only the owning customer may cancel, and only while the booking is Pending or Accepted.
- Every transition is written to `BookingStatusLog` for a full audit trail.

## 8. Production Notes

Switch to production settings with:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
```

`config/settings/production.py` requires `DJANGO_SECRET_KEY` to be set via environment
variable, enables HTTPS-only cookies and HSTS, and reads database/email credentials from
environment variables (see `.env.example`). Swap the `DATABASES` block to PostgreSQL or MySQL
by setting `DB_ENGINE`/`DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT`.

Run `python manage.py collectstatic` before deploying behind Nginx/Gunicorn.
