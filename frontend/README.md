# Frontend

Modern Frontend built with:

- **React** + **TypeScript** — type-safe component development
- **Vite** — fast build tool and development server
- **Chakra UI** — accessible and customizable component library
- **TanStack Router** — file-based routing
- **TanStack Query** — server state management
- **Design Tokens** — consistent styling across platforms

---

## Development

The frontend development server runs inside a Docker environment:

- In **development**, `Dockerfile.dev` is used for hot-reload and fast feedback loops.
- In **staging/production**, Kubernetes deploys using the standard `Dockerfile`.

This setup ensures a seamless developer experience with hot reload.

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

## Dynamic API Client System

The frontend features a **dynamic microservice client system** that automatically discovers and configures API clients:

- **Auto-discovery**: Automatically finds available services in `src/client/` folders
- **Zero configuration**: Only requires `VITE_API_URL` environment variable
- **Dynamic calls**: Use any API method with clean React Query hooks

### Usage

```tsx
import { useServiceMutation, useServiceQuery } from './client'

// Mutations (POST, PUT, DELETE)
const forgotPassword = useServiceMutation(
  'auth',
  'sendForgotPasswordPasswordForgotPost'
)
const resetPassword = useServiceMutation(
  'auth',
  'resetPasswordPasswordResetPost'
)

// Queries (GET)
const userProfile = useServiceQuery('users', 'getCurrentUserUsersGetCurrentGet')

// Call the API
forgotPassword.mutate({ requestBody: { email: 'user@example.com' } })
```

### Adding New Services

1. Add OpenAPI spec to `openapi/newservice.json`
2. Run `npm run build:clients` to generate client
3. Immediately available as `useServiceMutation('newservice', 'methodName')`

## Design Token System

This project leverages design tokens to maintain **consistent styling** and enable **easy UI updates** across multiple applications.

- The tokens are **exposed publicly** under `public/assets/tokens` for external consumption by other apps, mobile clients, and email templates.
- Locally, design tokens are **built and compiled** into strongly typed modules, allowing the React app to consume them directly.

To generate the latest tokens, run:

```bash
npm run build:tokens
```

## Removing Frontend

If you want to deploy only the microservice backend without the frontend, follow these steps:

- Delete the `./frontend` directory.
- Remove the frontend-related build files from the `./k8s` folder.
- Remove frontend deployment workflows from the `.github/actions` folder (both staging and production).
- Remove references to frontend in `./scripts/*.sh`.
- In the `docker-compose.yml` file, remove the `frontend` service section.

> **Note:** Cleaning up environment variable references is more complex because some may still expect a frontend to exist — either built within this project or managed separately. Please review your configuration carefully to avoid runtime issues.
