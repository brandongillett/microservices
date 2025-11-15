# Frontend

Modern Frontend built with:

- **React** + **TypeScript** — type-safe component development
- **Vite** — fast build tool and development server
- **Chakra UI** — accessible and customizable component library
- **TanStack Router** — file-based routing
- **TanStack Query** — server state management
- **Design Tokens** — consistent styling across platforms

---

## Code Structure

The frontend code is organized as follows:

- `frontend/src` — Main frontend source code
- `frontend/public/assets` — Static assets (images, fonts, tokens, etc.)
- `frontend/src/client` — Generated OpenAPI clients for microservice APIs
- `frontend/src/components` — Reusable React components
- `frontend/src/hooks` — Custom React hooks
- `frontend/src/routes` — Route definitions including page components
- `frontend/src/theme.tsx` — Custom Chakra UI theme configuration

## Removing Frontend

If you want to deploy only the microservice backend without the frontend, follow these steps:

- Delete the `./frontend` directory.
- Remove the frontend-related build files from the `./k8s` folder.
- Remove frontend deployment workflows from the `.github/actions` folder (both staging and production).
- Remove references to frontend in `./scripts/*.sh`.
- In the `docker-compose.yml` file, remove the `frontend` service section.

> **Note:** Cleaning up environment variable references is more complex because some may still expect a frontend to exist — either built within this project or managed separately. Please review your configuration carefully to avoid runtime issues.
