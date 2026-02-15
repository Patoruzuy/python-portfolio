# Configuration Management with Doppler Support

This application uses a centralized configuration system in `config.py` that supports multiple configuration sources:

## Configuration Priority

1. **Doppler** (if configured via `doppler run`)
2. **System Environment Variables**
3. **.env File**
4. **Default Values**

## Quick Start

### Local Development (.env file)

```bash
# Copy example and configure
cp .env.example .env

# Edit .env with your values
nano .env

# Run the application
python app.py
```

### Production with Doppler

```bash
# Install Doppler CLI
# https://docs.doppler.com/docs/install-cli

# Login and setup
doppler login
doppler setup

# Run with Doppler (no .env needed)
doppler run -- python app.py

# Or with Gunicorn
doppler run -- gunicorn app:app
```

## Configuration Classes

### Development
- Debug mode enabled
- SQLite database
- Insecure cookies (for localhost)
- Verbose logging

### Production
- Debug mode disabled
- Secure cookies required
- HSTS enabled
- Redis caching recommended

### Testing
- In-memory SQLite
- CSRF disabled
- Synchronous Celery tasks

### Doppler
- Automatically detected when `DOPPLER_ENVIRONMENT` is set
- All secrets injected via environment variables
- No .env file required

## Key Features

### 🔐 Security
- All sensitive data from environment variables
- CSRF protection
- Secure session cookies
- HSTS headers
- Content Security Policy

### 📧 Email Configuration
- Supports Gmail, SendGrid, SES, etc.
- Falls back gracefully if not configured
- Database overrides for admin settings

### 🚀 Deployment Ready
- Gunicorn configuration included
- Redis support for caching & Celery
- Docker-friendly
- Health check endpoints

### 🎯 Feature Flags
- Enable/disable newsletter
- Enable/disable contact form
- Enable/disable blog comments
- Enable/disable e-commerce

## Environment Variables

See `.env.example` for all available configuration options.

### Required Variables
- `SECRET_KEY` - Flask secret key (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
- `MAIL_USERNAME` - Email account for sending
- `MAIL_PASSWORD` - Email password or app-specific password

### Optional but Recommended
- `DATABASE_URL` - PostgreSQL connection string for production
- `REDIS_URL` - Redis connection for caching and Celery
- `SENTRY_DSN` - Error tracking
- `ADMIN_PASSWORD_HASH` - Hashed admin password

## Validating Configuration

```python
from config import Config

# Check if all required config is present
is_valid, missing = Config.validate_required_config()
if not is_valid:
    print(f"Missing configuration: {missing}")

# Get all non-sensitive config
all_config = Config.get_all_config()
print(all_config)
```

## Doppler Integration

### Why Doppler?

- ✅ **No .env files in production** - Secrets never touch disk
- ✅ **Team synchronization** - Everyone gets the right secrets
- ✅ **Audit logging** - Know who accessed what and when
- ✅ **Easy rotation** - Update secrets without redeploying
- ✅ **Multiple environments** - dev, staging, prod configs

### Setup with Doppler

1. **Create Project**
   ```bash
   doppler projects create portfolio-app
   ```

2. **Setup Environments**
   ```bash
   doppler configs create dev
   doppler configs create staging
   doppler configs create prod
   ```

3. **Add Secrets**
   ```bash
   doppler secrets set SECRET_KEY="your-secret-key"
   doppler secrets set MAIL_USERNAME="email@example.com"
   doppler secrets set MAIL_PASSWORD="password"
   # ... add all required secrets
   ```

4. **Run Application**
   ```bash
   # Development
   doppler run --config dev -- python app.py
   
   # Production
   doppler run --config prod -- gunicorn app:app
   ```

### Docker with Doppler

```dockerfile
# Install Doppler in your Dockerfile
RUN apt-get update && apt-get install -y apt-transport-https ca-certificates curl gnupg && \
    curl -sLf --retry 3 --tlsv1.2 --proto "=https" 'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | apt-key add - && \
    echo "deb https://packages.doppler.com/public/cli/deb/debian any-version main" | tee /etc/apt/sources.list.d/doppler-cli.list && \
    apt-get update && apt-get install doppler

# Use Doppler to inject secrets at runtime
CMD ["doppler", "run", "--", "gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
```

### GitHub Actions with Doppler

```yaml
- name: Install Doppler CLI
  uses: dopplerhq/cli-action@v1

- name: Run tests with Doppler
  run: doppler run --config ci -- pytest
  env:
    DOPPLER_TOKEN: ${{ secrets.DOPPLER_TOKEN }}
```

## Migration from .env to Doppler

1. **Export current .env**
   ```bash
   doppler secrets upload .env
   ```

2. **Verify secrets uploaded**
   ```bash
   doppler secrets
   ```

3. **Test with Doppler**
   ```bash
   doppler run -- python app.py
   ```

4. **Remove .env file** (add to .gitignore)
   ```bash
   rm .env
   echo ".env" >> .gitignore
   ```

## Troubleshooting

### Check Configuration Source
The application logs which configuration source it's using on startup:
- `🔐 Configuration loaded from Doppler: {info}` - Using Doppler
- `📁 Configuration loaded from .env file` - Using .env

### Debug Mode
```bash
# Enable debug mode
export FLASK_ENV=development
python app.py
```

### Validate Doppler Connection
```bash
# Check Doppler status
doppler whoami

# List secrets (without values)
doppler secrets --only-names

# Test run
doppler run -- python -c "import os; print(os.getenv('SECRET_KEY'))"
```

## Best Practices

1. **Never commit .env files** - Always use .gitignore
2. **Use Doppler for teams** - Consistency across developers
3. **Rotate secrets regularly** - Especially in production
4. **Use different secrets per environment** - dev, staging, prod
5. **Enable audit logging** - Track secret access
6. **Test configuration loading** - Before deploying
7. **Document required variables** - Keep .env.example updated

## Support

For issues related to:
- **Configuration**: Check `config.py` 
- **Doppler**: Visit https://docs.doppler.com
- **Application**: See main README.md
