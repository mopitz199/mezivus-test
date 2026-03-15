# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run development server
python manage.py runserver

# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Run tests
python manage.py test

# Run tests for a specific app
python manage.py test tracker

# Open Django shell
python manage.py shell

# Create superuser for admin access
python manage.py createsuperuser
```

## Architecture

This is a **Django 6.0.2** package tracking web application with a single app (`tracker`).

- `mezivus/` — Project-level configuration: settings, root URL routing (`/admin/` only currently), WSGI/ASGI entry points
- `tracker/` — The main app: models, views (empty), admin, migrations

### Core model

`tracker/models.py` defines a single `Package` model with fields: `name`, `tracking_code` (unique), `company`, `created_at`, `updated_at`.

### Development state

This is an early-stage project. Views and URL patterns for the `tracker` app have not yet been implemented. The database schema is migrated and the Django admin is active.
