# 🧩 Microservices Boilerplate

A production-ready boilerplate for building scalable, event-driven microservices with Python, React, and Kubernetes.

## 🧠 Backend: Python Microservices

- ⚡ **FastAPI** – Async APIs for high-throughput service endpoints
- 🔄 **FastStream** – Event-driven inter-service communication over **NATS JetStream**
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

## 🎯 Frontend: React

- ⚛️ **React + TypeScript** – Modern component-based web frontend
- ⚡ **Vite** – Lightning-fast builds and hot module reload
- 🎨 **Design Tokens** - Shared styling (colors, typography, spacing) for UI consistency across all applications
- 🤖 **Playwright** – End-to-end testing of user flows and critical paths

---

## 🧪 DevOps

- 🐙 **GitHub Actions** – CI/CD pipeline for linting, testing, and deploying changes to services/frontend (staging & production)
- 🐳 **Docker Compose** – Local development environment
- 💻 **Kubernetes** – YAML manifests for deployments for services / frontend
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

## Frontend README

Frontend docs: [frontend/README.md](./frontend/README.md).
