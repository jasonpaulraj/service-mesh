# ServiceMesh

![Version](https://img.shields.io/github/v/release/jasonpaulraj/service-mesh?include_prereleases)
![Build Status](https://img.shields.io/github/workflow/status/jasonpaulraj/service-mesh/CI)

A FastAPI application that integrates with monitoring and infrastructure management tools

---

## 📋 Overview

ServiceMesh integrates with multiple monitoring and infrastructure management tools:

- **Uptime Kuma** for monitoring - using [uptime-kuma-api](https://github.com/lucasheld/uptime-kuma-api) by [Lucas Held](https://github.com/lucasheld)
- **Prometheus** for metrics collection - using [prometheus-api-client](https://github.com/4n4nd/prometheus-api-client-python) by [Anand Sanmukhani](https://github.com/4n4nd)
- **Grafana** for visualization - using [grafana-client](https://github.com/panodata/grafana-client) by [Panodata](https://github.com/panodata)
- **Proxmox** for infrastructure management - using [proxmoxer](https://github.com/proxmoxer/proxmoxer) by [Proxmoxer Team](https://github.com/proxmoxer)

## 🎬 Demo

![{766D7B58-E841-4019-BE6D-DADE314D3D3B}](https://github.com/user-attachments/assets/022339c8-f0b5-404d-bdeb-0b793eaa3009)

## ✨ Features

- FastAPI backend with high-performance, asynchronous API design
- Integration with various monitoring and infrastructure management tools
- Comprehensive error handling and logging
- Health check endpoints for system monitoring
- Modular architecture with clear separation of concerns
- Documentation with OpenAPI/Swagger
- Containerization and orchestration support
- CI/CD pipeline configuration
- Database integration for storing credentials and configurations
- API for managing service credentials and monitors

---

## 🔧 Requirements

- Python 3.10+
- FastAPI
- Pydantic
- SQLAlchemy
- MySQL
- uptime-kuma-api
- prometheus-api-client-python
- grafana-client
- proxmoxer

---

## 🚀 Local Development Setup with Docker

The easiest way to get started with local development is using Docker and Docker Compose. This approach ensures consistent development environments and minimizes setup issues.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

---

### Getting Started

##### 1. Environment Configuration

Copy the example environment file and modify it with your settings:

```bash
cp .env.example .env
```

Edit the `.env` file to set your API keys and service credentials.

##### 2. Build and Start the Containers

```bash
docker compose up -d
```

This will:

- Build the API container
- Start a MySQL database container
- Initialize the database
- Start the FastAPI application with hot-reload enabled

##### 3. Access the API

- The API will be available at http://localhost:6000

- API Documentation:
  - Swagger UI: http://localhost:6000/docs
  - ReDoc: http://localhost:6000/redoc

##### 4. Live Code Reloading

The development setup uses uvicorn with the --reload flag, so any changes to your code will automatically reload the server.

---

## 💾 Database Management

### Running Database Migrations

The container automatically runs migrations at startup, but if you need to run them manually:

```bash
docker compose exec api alembic upgrade head
```

---

### Setting Up Alembic (First-Time Setup)

If you're setting up the project from scratch or need to initialize Alembic:

##### 1. Initialize Alembic in your project:

```bash
docker compose exec api alembic init migrations
```

This creates the initial migration environment with a migrations folder and alembic.ini file.

##### 2. Configure Alembic:

- Update the alembic.ini file to point to your database URL or use environment variables.
- Edit the migrations/env.py file to use the SQLAlchemy models from your application.

##### 3. Generate your first migration:

```bash
docker compose exec fastapi alembic revision --autogenerate -m "fresh migration"
```

This command scans your SQLAlchemy models and generates migration scripts to create the corresponding database schema.

##### 4. Apply the migrations:

```bash
docker compose exec api alembic upgrade head
```

This applies all pending migrations to bring your database schema up to date.

---

### Common Alembic Commands

- Create a new migration manually:

  ```bash
  docker compose exec api alembic revision -m "description of changes"
  ```

- Generate migration based on model changes:

  ```bash
  docker compose exec api alembic revision --autogenerate -m "description of changes"
  ```

- Upgrade to a specific version:

  ```bash
  docker compose exec api alembic upgrade <revision>
  ```

- Downgrade to a previous version:

  ```bash
  docker compose exec api alembic downgrade <revision>
  ```

- View migration history:

  ```bash
  docker compose exec api alembic history
  ```

- View current database version:

  ```bash
  docker compose exec api alembic current
  ```

---

### Accessing the Database

The application is configured to connect to either an external MySQL database or another MySQL container. The connection details are specified in your .env file.

To connect directly to the MySQL database:

```bash
docker compose exec db mysql -u <DB_USER> -p<DB_PASSWORD> <DB_NAME>
```

### Stopping the Environment

```bash
docker compose down
```

To completely remove all data (including database volumes):

```bash
docker compose down -v
```

---

## 📚 API Documentation

Once the application is running, you can access the OpenAPI documentation at:

- Swagger UI: http://localhost:6000/docs
- ReDoc: http://localhost:6000/redoc

### API Endpoints Health Check

- GET /api/v1/health - Check the health of the API Service Credentials
- GET /api/v1/credentials - List all service credentials
- GET /api/v1/credentials/{id} - Get a specific credential by ID
- GET /api/v1/credentials/service/{service_type} - Get credentials by service type
- POST /api/v1/credentials - Create a new service credential
- PATCH /api/v1/credentials/{id} - Update a service credential
- DELETE /api/v1/credentials/{id} - Delete a service credential

---

## 🚢 Deployment

The application includes deployment configurations for both Docker and Kubernetes environments.

### Docker Deployment

To deploy the application using Docker:

```bash
# Build the Docker image
docker build -t service-mesh:latest .

# Run the container
docker run -d -p 6000:5000 --env-file .env --name monitoring-api service-mesh:latest
```

---

### Kubernetes Deployment

Kubernetes manifests are provided in the kubernetes/ directory:

##### 1. Deploy to Kubernetes

```bash
# Apply the ConfigMap
kubectl apply -f kubernetes/configmap.yaml

# Apply the Deployment
kubectl apply -f kubernetes/deployment.yaml

# Apply the Service
kubectl apply -f kubernetes/service.yaml
```

##### 2. Check the deployment status

```bash
kubectl get deployments
kubectl get pods
kubectl get services
```

---

## 🔄 CI/CD Pipeline

This project includes GitHub Actions workflows for both CI and CD:

- CI Pipeline : Automatically runs on pull requests to test the codebase
- CD Pipeline : Deploys to your Kubernetes cluster when changes are merged to the main branch

### GitHub Actions Workflows Workflow Description Trigger CI

- Runs tests, linting, and security checks

- Pull requests to main CD

- Builds and deploys to production

- Push to main branch Release

- Creates a new release with version tag

- Manual trigger

### Versioning

This project follows Semantic Versioning :

- MAJOR version for incompatible API changes
- MINOR version for new functionality in a backward compatible manner
- PATCH version for backward compatible bug fixes

#### To create a new release:

1. Update the version in pyproject.toml
2. Create a new tag: `git tag v1.0.0`
3. Push the tag: `git push origin v1.0.0`
4. The GitHub Actions workflow will automatically create a release

### Setting Up CI/CD

To set up the CD pipeline, you'll need to add the following secrets to your GitHub repository:

```bash
- KUBE_CONFIG : Your Kubernetes configuration file (base64 encoded)
- DOCKER_USERNAME : Your Docker Hub username
- DOCKER_PASSWORD : Your Docker Hub password
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---
