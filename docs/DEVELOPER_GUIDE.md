# BattyCoda Developer Guide

This guide provides information for developers who want to contribute to BattyCoda or extend its functionality.

## Project Structure

BattyCoda is a Django application with an R component for audio analysis. The main components are:

```
battycoda/
├── battycoda_app/        # Core Django application
│   ├── audio/            # Audio processing code
│   ├── middleware/       # Custom middleware
│   ├── models/           # Django models (database structure)
│   ├── views_*.py        # View modules by feature
│   └── utils_modules/    # Utility functions
├── config/               # Django configuration
├── R_code/               # R scripts for audio analysis
│   ├── api_endpoints.R   # API endpoints for Django-R communication
│   └── model_functions/  # ML model implementation
├── static/               # Static assets (CSS, JS, images)
├── templates/            # HTML templates
└── docs/                 # Documentation
```

## Development Environment Setup

Follow the [Installation Guide](INSTALLATION.md) for basic setup, then:

1. Configure your IDE/editor with:
   - Black formatter
   - isort for imports
   - flake8 for linting

2. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Code Style

BattyCoda follows these coding standards:

- **Python**: PEP 8 with 120 character line limit
- **Imports**: Grouped by standard library, Django, then project modules; alphabetized within groups
- **JavaScript**: ESLint standard configuration
- **CSS**: BEM methodology for class naming

Use the project's linting tools:
```bash
./lint.sh       # Check code quality
./format.sh     # Auto-format code
```

## Key Components

### Django Models

Core models are organized in the `battycoda_app/models/` directory:

- `user.py`: User management, groups, profiles
- `organization.py`: Projects, species, and call types
- `recording.py`: Audio recordings and segmentation
- `task.py`: Annotation tasks and batches
- `detection.py`: Classification models and results

### Audio Processing

The audio processing pipeline includes:

1. `battycoda_app/audio/utils.py`: Core audio utilities
2. `battycoda_app/views_segmentation/`: Segmentation views
3. `R_code/model_functions/`: R-based audio analysis

### Task System

The task system (`battycoda_app/views_task_*.py`) manages the annotation workflow:

1. Task creation from segments
2. Batch organization
3. Annotation interface
4. Progress tracking

### R Integration

Communication between Django and R:

1. Django calls R endpoints via HTTP
2. R processes audio and returns results
3. Django stores and displays results

## Adding New Features

### Adding a New Model

1. Create or modify the appropriate model file in `battycoda_app/models/`
2. Create migrations:
   ```bash
   docker compose exec -T web python manage.py makemigrations
   ```
3. Apply migrations:
   ```bash
   docker compose exec -T web python manage.py migrate
   ```

### Adding a New View

1. Create a new view function in an appropriate views file
2. Add the URL pattern in `battycoda_app/urls.py`
3. Create templates in `templates/` directory

### Adding a New R Feature

1. Develop and test your R function in `R_code/model_functions/`
2. Add an API endpoint in `R_code/api_endpoints.R`
3. Create a Django interface to call the R endpoint

## Testing

### Python Tests

Run the test suite:
```bash
docker compose exec -T web python manage.py test
```

Run specific tests:
```bash
docker compose exec -T web python manage.py test battycoda_app.tests.TestClassName
```

### Adding Tests

1. Add test methods to files in the `battycoda_app/tests/` directory
2. Follow the Django testing patterns
3. Use the `TestCase` class for most tests

## Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Configure proper database settings
3. Use nginx for serving static files
4. Set up SSL certificates

## Common Development Tasks

### Database Changes

After model changes:
```bash
docker compose exec -T web python manage.py makemigrations
docker compose exec -T web python manage.py migrate
```

### Static Assets

Collect static files:
```bash
docker compose exec -T web python manage.py collectstatic --noinput
```

### R Package Management

Add R packages to the `Dockerfile.r_ubuntu`:
```dockerfile
RUN R -e "install.packages(c('package1', 'package2'), repos='https://cran.r-project.org/')"
```

Then rebuild the R container:
```bash
docker compose build r-server
docker compose up -d r-server
```

## Troubleshooting

### Debugging Django

1. Set `DEBUG=True` in `.env`
2. Check logs:
   ```bash
   docker compose logs -f web
   ```
3. Use Django's debug tools

### Debugging R

1. Check R server logs:
   ```bash
   docker compose logs -f r-server
   ```
2. Add debug print statements in R code
3. Test R functions independently

### Common Issues

- **Django migrations conflicts**: Reset migrations or use `--fake` flag
- **R package installation failures**: Check system dependencies
- **Audio processing errors**: Verify file formats and paths

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Run tests and linting
5. Submit a pull request

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [R for Data Science](https://r4ds.had.co.nz/)
- [Docker Documentation](https://docs.docker.com/)
- [Celery Documentation](https://docs.celeryq.dev/)