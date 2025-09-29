<p align="center">
  <a href="" rel="noopener">
</p>

<h1 align="center">Deployment</h1>

This document outlines the process for deploying the application using the provided GitHub Actions workflows. The deployment pipeline is designed for automated, zero-downtime deployments to a Kubernetes cluster.

---

## Prerequisites

Before you can deploy, you must have the following set up:

- A Kubernetes cluster with `kubectl` access.
- A Docker Hub account (or another container registry).
- Prometheus Operator or a similar tool for scraping metrics (recommended).

## Deployment Variables

Deployment is configured entirely through **GitHub Secrets**. You must create the following secrets in your repository for both `STAGING` and `PRODUCTION` environments.

In the variable names below, replace `{ENV}` with either `STAGING` or `PRODUCTION`.

- `DOCKER_USERNAME` - Your container registry username.
- `DOCKER_PASSWORD` - Your container registry password or access token.
- `PROJECT_NAME` - The project's name, used for tagging images.
- `{ENV}_DOMAIN` - The root domain for the environment (e.g., `yourapp.staging.com`).
- `{ENV}_KUBE_CONFIG` - The base64-encoded Kubernetes configuration file.
- `{ENV}_NAMESPACE` - The target Kubernetes namespace for application services.
- `{ENV}_DATABASE_NAMESPACE`- The namespace where the database is located.
- `{ENV}_STACK_NAME` - A unique name for the deployment stack (e.g., `myapp-staging`).
- `{ENV}_AUTH_REDIS_URL` - The connection URL for the Auth service's Redis instance.
- `{ENV}_USERS_REDIS_URL` - The connection URL for the Users service's Redis instance.
- `{ENV}_EMAILS_REDIS_URL` - The connection URL for the Emails service's Redis instance.
- `{ENV}_NATS_URL` - The connection URL for the NATS messaging server.
- `{ENV}_POSTGRES_PASSWORD` - The password for the PostgreSQL database.
- `{ENV}_SMTP_PASSWORD` - The password for the SMTP server.
- `{ENV}_SECRET_KEY` - The application's global secret key for signing tokens, etc.
- `{ENV}_ROOT_USER_PASSWORD` - An optional password for a default root user (this is needed for testing so its recommended to keep it for staging).

## Deployment Customization

While the workflows are designed to work out-of-the-box, you can customize certain behaviors by editing the workflow `build-deploy*` files in `.github/workflows/`.

### Replicas

The number of replicas for each service is defined by variables at the top of the workflow files. While this is suitable for setting a baseline, it's recommended to implement a **Horizontal Pod Autoscaler (HPA)** for dynamic, resource-based scaling in production.

### Image Architecture

The target CPU architecture for the Docker images is controlled by the `DOCKER_PLATFORMS` variable in the workflow files. You can specify one or more platforms separated by commas.

```
DOCKER_PLATFORMS: linux/arm64 # ex. linux/amd64,linux/arm64
```

### Docker Build Cloud

This project is configured to use Docker Build Cloud to accelerate ARM64 image builds, as native ARM builds on standard GitHub runners can be very slow. You can disable this if you are using self-hosted runners or only building `linux/amd64` images.

To disable, remove the `driver: cloud` and the `endpoint` lines from the `Set up Docker Buildx` step in the workflow file.

## Key Features

### Smart Deployments (Change Detection)

To save build time and resources, the CI/CD pipeline automatically detects which services have changed in a given commit. Only the images for the modified services (and the frontend) are rebuilt and redeployed. This is ideal for a monorepo architecture.

### Rolling Deployments

The Kubernetes manifests are configured with a `RollingUpdate` strategy. This ensures that new versions are rolled out incrementally without any service interruption. The update strategy can be fine-tuned in the `k8s/` manifests for each service.

### Prometheus Endpoints

All services (API, workers, schedulers) expose a Prometheus metrics endpoint on port `9000`. It is your responsibility to configure a Prometheus instance to scrape these internal endpoints for monitoring and alerting.
