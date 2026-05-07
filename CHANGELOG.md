# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-05-07

### Added
- Initial production deployment
- PostgreSQL database migration from SQLite
- Docker containerization (Django, PostgreSQL, Nginx)
- HTTPS/SSL with Let's Encrypt
- GitHub Actions CI/CD (tests on all branches, deploy on main)
- Unit tests for core models
- Environment-based configuration (dev with DEBUG=True, prod with DEBUG=False)

### Changed
- Django 6.0.4 → 5.2.13 (actual stable version)
- email_verification_token max_length 32 → 255 (JWT token compatibility)
- Email field max_length handling for production

### Fixed
- CSRF token validation in production
- Django DEFAULT_AUTO_FIELD configuration
