# BattyCoda Installation Guide

This guide provides instructions for setting up BattyCoda in both server and local development environments.

## Prerequisites

BattyCoda requires the following software:

- Docker and Docker Compose (v2)
- Git
- PostgreSQL 15
- Redis
- R (for the R server component with the necessary packages)
- Nginx (for production deployments)

## Server Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/battycoda.git
cd battycoda
```

### 2. Configure Environment Variables

Create a `.env` file in the project root directory based on the provided `.env.example`:

```bash
cp .env.example .env
```

Edit the `.env` file and set the required variables:

```
# Required configuration
SECRET_KEY=your-secret-key-here
DOMAIN_NAME=your-domain-name.com
DEBUG=False

# Database configuration
DB_NAME=battycoda
DB_USER=battycoda
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432

# Email configuration (if using AWS SES)
AWS_SES_REGION_NAME=your-aws-region
AWS_SES_ACCESS_KEY_ID=your-access-key
AWS_SES_SECRET_ACCESS_KEY=your-secret-key
DEFAULT_FROM_EMAIL=no-reply@your-domain.com

# Optional configuration
MAX_UPLOAD_SIZE_MB=100
```

### 3. Set Up Nginx

Run the provided script to configure Nginx:

```bash
sudo ./setup_nginx.sh
```

This will create and enable an Nginx configuration for BattyCoda based on your `.env` settings.

### 4. SSL Configuration (Recommended for Production)

If using HTTPS (recommended for production):

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Run the Nginx setup script again after installing certificates:

```bash
sudo ./setup_nginx.sh
```

### 5. Start the Application

Build and start all the Docker containers:

```bash
docker compose build
docker compose up -d
```

### 6. Create a Superuser

```bash
docker compose exec -T web python manage.py createsuperuser
```

### 7. Access the Application

Visit your domain in a web browser to access BattyCoda. If running locally, visit `http://localhost:8000`.

## Local Development Setup

For local development, the setup is similar but with a few differences:

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/battycoda.git
cd battycoda
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

For local development, update these settings:

```
DEBUG=True
DOMAIN_NAME=localhost
```

### 3. Start the Application in Development Mode

```bash
docker compose build
docker compose up
```

Note: For development, you may want to run without the `-d` flag to see logs directly in the console.

### 4. Create a Superuser

```bash
docker compose exec -T web python manage.py createsuperuser
```

### 5. Access the Development Server

Visit `http://localhost:8000` in your web browser.

## Docker Command Reference

```bash
# Build and start all containers
docker compose build
docker compose up -d

# Run Django commands within container
docker compose exec -T web python manage.py [command]

# Run tests
docker compose exec -T web python manage.py test
docker compose exec -T web python manage.py test battycoda_app.tests.TestClassName.test_method_name

# Check logs
docker compose logs -f web
docker compose logs -f celery

# Clean up resources (remove all containers, networks, and volumes)
docker compose down

# For R server specifically
docker compose up -d r-server     # Start only the R server
docker compose exec r-server bash # Enter the R server container
docker compose logs -f r-server   # View R server logs
```

## Linting and Formatting

The project includes tools for maintaining code quality:

```bash
./lint.sh         # Check code quality with flake8, black, and isort
./format.sh       # Auto-format code with black and isort
./run_linters.sh  # Run ALL linters including the CSS class checker
```

## R Server

The R server component handles advanced audio processing and machine learning. It runs in its own container and communicates with the Django application through a set of API endpoints.

Make sure the R server container is running:

```bash
docker compose logs -f r-server
```

If you need to install additional R packages, you can modify the `Dockerfile.r_ubuntu` file.

## Common Issues and Troubleshooting

### Permissions Issues

If you encounter permissions issues with file access:

```bash
# Set appropriate ownership for all files
sudo chown -R yourusername:yourusername .
```

### Database Migrations

If the database schema needs to be updated:

```bash
docker compose exec -T web python manage.py makemigrations
docker compose exec -T web python manage.py migrate
```

### Static Files

If static files are not being served:

```bash
docker compose exec -T web python manage.py collectstatic --noinput
```

### R Server Connection Issues

If the Django application cannot connect to the R server:

1. Check the R server logs:
   ```bash
   docker compose logs -f r-server
   ```

2. Verify network settings in `docker-compose.yml`

3. Ensure all required R packages are installed in the R server container

## Next Steps

After installation:

1. Create a research group
2. Add bat species and call types
3. Create a project
4. Upload your first recordings
5. Begin segmentation and annotation

For more details, refer to the [User Guide](USER_GUIDE.md).