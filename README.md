# 🧩 Microservices Boilerplate

A production-ready boilerplate for building scalable, event-driven microservices in Python FastAPI.

## 🧠 Backend: Python Microservices

- ⚡ **FastAPI** – Async APIs for high-throughput service endpoints
- 🔄 **FastStream** – Event-driven inter-service communication over NATS JetStream
- 🧮 **TaskIQ** – Async task scheduler and background worker system
- 🧰 **Alembic** – Database schema migrations
- 📊 **Prometheus** – Metrics collection and monitoring for endpoints and workers
- 🔐 **Custom Rate Limiter** – IP-based abuse prevention, designed for async performance
- 🧪 **Pytest** – Modular, high-performance test suite
- 📏 **Mypy & Ruff** – Type checking and linting for maximum stability
- 📦 **Uv** – Reliable and reproducible Python dependency management
- 🔑 **JWT-based authentication** and encrypted token storage
- 🧷 **URL-safe tokens** used for secure links and verification flows

---

## 🗄️ Database & Messaging

- 💾 **PostgreSQL** – SQL database
- 🧠 **Redis** – In-memory store for caching, rate-limiting, distributed locks, etc.
- ✉️ **NATS JetStream** – Message broker with pub/sub, queuing, and durability

---

## 🧪 DevOps

- 🐙 **GitHub Actions** – CI/CD pipeline for linting, testing, and deploying changes to services (staging & production)
- 🐳 **Docker Compose** – Local development environment
- 💻 **Kubernetes** – YAML manifests for deployments for services
- 🚀 **Rolling Updates** – Zero-downtime deployments

---

## Deployment

Deployment docs: [deployment.md](./deployment.md).

---

## Development

Development docs: [development.md](./development.md).

---

## Backend README

Backend docs: [services/README.md](./services/README.md).

---

## Acknowledgements

- **[full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)** - This project's design is heavily inspired by FastAPI's full stack template. The primary goal was to adapt its monolithic approach into a scalable microservices architecture.

- **[fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)** - Several performance optimizations, particularly for asynchronous operations, were inspired by the best practices found in this repository.

- **[fastapi-tips](https://github.com/Kludex/fastapi-tips)** - Additional development tips and useful patterns were adopted from this repository.

- **[faststream](https://github.com/ag2ai/faststream)** - This project relies on FastStream for asynchronous, event-driven communication between services.

- **[taskiq](https://github.com/taskiq-python/taskiq)** - Taskiq is used for managing background jobs and scheduling periodic tasks across workers.
