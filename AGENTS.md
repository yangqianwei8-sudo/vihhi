# AGENTS.md

## Cursor Cloud specific instructions

### Architecture Overview
This is **维海科技信息化管理平台** (Weihai Tech ERP), a monolithic Django 4.2 backend with a pre-built Vue 3 + Element Plus frontend. The backend serves both HTML pages and REST APIs. The frontend `dist/` is pre-built and served via Django's static files system (WhiteNoise).

### Services

| Service | Required | How to start |
|---------|----------|--------------|
| PostgreSQL 13 | Yes | `sudo docker start postgres-dev` (container already created) |
| Django dev server | Yes | `source venv/bin/activate && python manage.py runserver 0.0.0.0:8000` |
| Redis | No | Falls back to `LocMemCache` if `REDIS_URL` is unset |
| Celery | No | Not configured in `settings.py` |

### Key Gotchas

- **Migration history is complex**: The codebase has migration files with circular dependencies between `customer_management` and `production_management` apps. The squashed migration has been moved to `_squashed_backup.py` and individual migrations are used instead. For fresh database setup, use `migrate --fake` then create tables from models (see setup approach in git history).
- **Static files**: The frontend build artifacts from `frontend/dist/` must be copied to `backend/staticfiles/` for the login page and dashboard to render properly. Run `python manage.py collectstatic --noinput` after setup.
- **Database config**: By default in DEBUG mode, settings.py falls back to a remote Sealos database (which may be unreachable). The `.env` file overrides this with `DATABASE_URL` pointing to a local Docker PostgreSQL instance.
- **Docker required**: PostgreSQL runs in Docker. The Docker daemon must be started manually: `sudo dockerd &>/tmp/dockerd.log &`. Use `sudo docker start postgres-dev` to start the existing container.
- **No automated tests**: The codebase has no unit/integration test files.
- **Heavy OCR dependencies**: `paddleocr` and `paddlepaddle` (~200MB) are installed from `requirements.txt`. They are only needed for invoice OCR features.
- **Admin credentials**: Default superuser is `admin` / `admin123`.
- **Lint**: No flake8/ruff config. Run `flake8 backend/ --max-line-length=120 --select=E9,F63,F7,F82` for critical errors only. Pre-existing errors exist in example/docs files.

### Common Commands
- **Dev server**: `source venv/bin/activate && python manage.py runserver 0.0.0.0:8000`
- **System check**: `source venv/bin/activate && python manage.py check`
- **Collect static**: `source venv/bin/activate && python manage.py collectstatic --noinput`
- **Create superuser**: `source venv/bin/activate && DJANGO_SUPERUSER_PASSWORD=admin123 python manage.py createsuperuser --username admin --email admin@example.com --noinput`
