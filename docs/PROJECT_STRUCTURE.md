# Creator Control Center - Project Structure

## Overview

Creator Control Center is a comprehensive marketing analytics platform built with:
- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Jinja2 Templates with modern CSS
- **Database**: SQLModel/SQLAlchemy (supports SQLite/PostgreSQL/Supabase)
- **Email**: Resend API integration
- **Authentication**: JWT + OAuth 2.0 (Google, Facebook, Apple, Twitter, TikTok)

---

## Directory Structure

```
marketing_analystics/
├── app/                          # Backend application (FastAPI)
│   ├── locales/                  # Internationalization (i18n)
│   │   ├── ko.json              # Korean translations
│   │   ├── en.json              # English translations
│   │   └── ja.json              # Japanese translations
│   ├── middleware/               # HTTP middleware
│   │   ├── security.py          # CORS, rate limiting
│   │   └── security_headers.py  # Security headers (CSP, HSTS)
│   ├── routers/                  # API route handlers
│   │   ├── admin.py             # Admin panel endpoints
│   │   ├── ai_pd.py             # AI product description generator
│   │   ├── auth.py              # Authentication (login, signup, OAuth)
│   │   ├── channels.py          # Channel management
│   │   ├── dashboard.py         # Dashboard endpoints
│   │   └── subscriptions.py     # Subscription management
│   ├── seo/                      # SEO utilities
│   │   ├── seo_service.py       # Meta tags, OG tags, schemas
│   │   └── sitemap_generator.py # XML sitemap generation
│   ├── services/                 # Business logic layer
│   │   ├── account_recovery.py  # Password reset, username reminder
│   │   ├── ai_pd_service.py     # AI product description service
│   │   ├── ai_recommendations.py # AI-based recommendations
│   │   ├── channel_connectors.py # Social media API connectors
│   │   ├── config_status.py     # Configuration status checker
│   │   ├── crypto.py            # Encryption utilities
│   │   ├── email_verification.py # Email verification codes
│   │   ├── gemini_ai.py         # Google Gemini AI integration
│   │   ├── gmail_service.py     # Gmail API service
│   │   ├── localization.py      # Translation loader
│   │   ├── login_throttle.py    # Brute force protection
│   │   ├── pdf_generator.py     # PDF report generation
│   │   ├── resend_email.py      # Resend email service
│   │   ├── social_auth.py       # Social authentication helpers
│   │   ├── social_fetcher.py    # Social media data fetcher
│   │   ├── social_oauth.py      # OAuth 2.0 implementation
│   │   └── super_admin_email.py # Admin notification emails
│   ├── auth.py                   # Authentication manager
│   ├── cache.py                  # Caching utilities
│   ├── config.py                 # Application settings
│   ├── database.py               # Database connection
│   ├── dependencies.py           # FastAPI dependencies
│   ├── main.py                   # Application entry point
│   ├── models.py                 # SQLModel database models
│   ├── schemas.py                # Pydantic schemas
│   └── validators.py             # Input validators
│
├── ui/                           # Frontend templates and assets
│   ├── components/               # Reusable HTML components
│   │   ├── _alert_messages.html # Alert/notification component
│   │   ├── _auth_social_buttons.html # Social login buttons
│   │   └── _pricing_card.html   # Pricing plan card
│   ├── layouts/                  # Base layout templates
│   │   ├── auth_layout.html     # Authentication pages layout
│   │   ├── base.html            # Main base layout
│   │   └── dashboard_layout.html # Dashboard layout
│   ├── pages/                    # Page-specific templates
│   │   ├── admin/               # Admin pages
│   │   │   ├── creator_detail.html
│   │   │   ├── inquiries.html
│   │   │   └── super_admin.html
│   │   ├── auth/                # Authentication pages
│   │   │   ├── login.html
│   │   │   ├── recovery.html
│   │   │   └── signup.html
│   │   ├── dashboard/           # Dashboard pages
│   │   │   ├── channels.html
│   │   │   ├── creator.html
│   │   │   ├── manager.html
│   │   │   └── profile.html
│   │   └── public/              # Public pages
│   │       ├── business.html
│   │       ├── landing.html
│   │       ├── personal.html
│   │       ├── services.html
│   │       └── support.html
│   ├── static/                   # Static assets
│   │   ├── css/
│   │   │   ├── style.css        # Base styles
│   │   │   └── style-modern.css # Modern design enhancements
│   │   └── js/
│   │       ├── slider.js        # Slider component
│   │       └── theme.js         # Theme toggle (dark/light)
│   └── templates/                # Main template files
│       ├── 404.html             # Not found page
│       ├── 500.html             # Server error page
│       ├── base.html            # Base template with header/footer
│       ├── business.html        # Business plan page
│       ├── channels_manage.html # Channel management
│       ├── contact.html         # Contact form
│       ├── creator_detail.html  # Creator detail view
│       ├── landing.html         # Landing page
│       ├── login.html           # Login page
│       ├── manager_dashboard.html # Manager dashboard
│       ├── manager_inquiries.html # Inquiries management
│       ├── personal.html        # Personal plan page
│       ├── privacy.html         # Privacy policy
│       ├── profile.html         # User profile
│       ├── recovery.html        # Password recovery
│       ├── services.html        # Services overview
│       ├── signup.html          # Signup page
│       ├── super_admin.html     # Super admin panel
│       ├── support.html         # Support/FAQ page
│       └── terms.html           # Terms of service
│
├── scripts/                      # Utility scripts
│   └── add_legal_translations.py # Legal page translations
│
├── docs/                         # Documentation
│   ├── updates/                  # Update logs
│   │   └── 2025-12-23.md        # Daily update log
│   └── PROJECT_STRUCTURE.md     # This file
│
├── .env                          # Environment variables (not in git)
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
└── README.md                     # Project README

```

---

## Core Features

### 1. Authentication System
- **Location**: `app/routers/auth.py`, `app/auth.py`
- Email/password authentication with bcrypt hashing
- OAuth 2.0 (Google, Facebook, Apple, Twitter, TikTok)
- Email verification with secure codes
- Password reset via Resend email
- Login throttling (brute force protection)
- JWT token-based sessions

### 2. User Management
- **Location**: `app/models.py`, `app/routers/admin.py`
- Role-based access control (Creator, Manager, Admin, Super Admin)
- Profile management with social account linking
- Subscription tiers (Free, Personal, Business)

### 3. Channel Analytics
- **Location**: `app/routers/channels.py`, `app/services/channel_connectors.py`
- YouTube, Instagram, TikTok, Facebook, Threads integration
- Automated metrics fetching
- Performance tracking and reporting

### 4. AI Features
- **Location**: `app/services/gemini_ai.py`, `app/services/ai_recommendations.py`
- Google Gemini AI integration
- Content recommendations
- AI-powered product descriptions

### 5. Email Services
- **Location**: `app/services/resend_email.py`
- Verification code emails
- Password reset emails
- Welcome emails
- Purchase confirmations
- Admin notifications

### 6. Internationalization
- **Location**: `app/locales/`, `app/services/localization.py`
- Korean (ko), English (en), Japanese (ja)
- Full translation coverage for UI

### 7. SEO Optimization
- **Location**: `app/seo/`
- Dynamic meta tags
- OpenGraph tags
- Twitter cards
- JSON-LD schemas
- XML sitemap generation

---

## API Endpoints

### Public Routes
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Landing page |
| GET | `/services` | Services overview |
| GET | `/personal` | Personal plan page |
| GET | `/business` | Business plan page |
| GET | `/support` | Support/FAQ page |
| GET | `/terms` | Terms of service |
| GET | `/privacy` | Privacy policy |
| GET | `/contact` | Contact form |
| POST | `/contact` | Submit contact form |

### Authentication Routes
| Method | Path | Description |
|--------|------|-------------|
| GET | `/login` | Login page |
| POST | `/login` | Process login |
| GET | `/signup` | Signup page |
| POST | `/signup` | Process signup |
| POST | `/logout` | Logout user |
| GET | `/recover` | Password recovery page |
| POST | `/recover/request` | Request password reset |
| POST | `/recover/reset` | Reset password |
| GET | `/oauth/{provider}` | Initiate OAuth flow |
| GET | `/oauth/{provider}/callback` | OAuth callback |

### Dashboard Routes (Authenticated)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard` | Main dashboard |
| GET | `/profile` | User profile |
| POST | `/profile/password` | Update password |
| GET | `/channels/manage` | Channel management |

### Admin Routes (Admin/Super Admin only)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin` | Admin dashboard |
| GET | `/admin/users` | User management |
| GET | `/admin/inquiries` | Inquiry management |

---

## Environment Variables

Required environment variables (see `.env.example`):

```env
# Security
SECRET_KEY=your-secret-key
SUPER_ADMIN_ACCESS_TOKEN=your-admin-token

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Supabase (optional)
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# OAuth Providers
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
APPLE_CLIENT_ID=
APPLE_TEAM_ID=
APPLE_KEY_ID=
APPLE_PRIVATE_KEY=
TWITTER_CLIENT_ID=
TWITTER_CLIENT_SECRET=
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=

# Email (Resend)
RESEND_API_KEY=
RESEND_FROM_EMAIL=noreply@yourdomain.com
RESEND_FROM_NAME=Creator Control Center

# AI
GEMINI_API_KEY=

# Environment
ENVIRONMENT=development  # or production
```

---

## Running the Application

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
# Run with production settings
ENVIRONMENT=production uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Security Features

1. **Password Security**: bcrypt hashing with salt
2. **CSRF Protection**: State tokens for OAuth
3. **XSS Prevention**: Template auto-escaping
4. **SQL Injection Prevention**: SQLModel ORM
5. **Rate Limiting**: Login throttling (5 attempts/15 minutes)
6. **Secure Headers**: CSP, HSTS, X-Frame-Options
7. **HTTPS Enforcement**: Production-only HTTPS redirect
8. **Token Hashing**: SHA-256 for reset tokens
9. **Input Validation**: Pydantic schemas

---

## Last Updated
December 23, 2024
