# Services

## Tests

In each service of this project, we have implemented automated testing to ensure code quality and functionality.
By default, tests are configured to run automatically using GitHub Actions whenever there is a push to the main branch. This ensures that any changes made to the codebase are validated against the test suite, helping to maintain the integrity of the project.

You can execute all tests using the following bash script, which will completely wipe volumes and rebuild the containers:

```
bash scripts/test.sh
```

If your containers are already running and you want to execute the tests without stopping the current processes, you can run tests for each service (e.g. auth):

```
docker compose exec -t auth bash scripts/run-tests.sh
```

To evaluate how much of the code is covered by tests, we utilize coverage reporting. The coverage results can be found in the following location of each service (e.g. auth) `./services/auth/htmlcov/index.html`

### Important Note

Tests can only be run in `local` and `staging` environments. Ensure you are in the appropriate environment before attempting to run the tests to avoid unexpected behavior.

## API Versioning

In this project, we have adopted a versioning strategy for our services to ensure smooth upgrades and backward compatibility for both the development and production environments. The versioning system is designed to provide clear separation between different API versions while also offering flexibility for continuous development and deployment. Below is a breakdown of how the versioning system works:

### Overview

We follow the principle of semantic versioning, where each version of the services is clearly identified by a version number. This allows us to introduce new features, deprecate old ones, and make breaking changes in a controlled manner.

- By default, the documentation for the latest version for each service (e.g. auth) is available at http://api.localhost/auth/docs. You can also access documentation for specific versions across all services (e.g. auth) through the following URLs (note: docs/redoc are only available for the local and staging environments):
  - http://api.localhost/auth/v1/docs (for version 1)
  - http://api.localhost/auth/v1/redoc (Redoc for version 1)
- The latest version is manually set in the `services/{SERVICE}/src/main.py file`. In this file, you determine which version of the API the latest version endpoint should point to by including the corresponding router. For example, to point to `v1`, you would set: `src.include_router(v1_router)` This step is essential for local development and testing, as tools like pytest rely on the latest version when running tests. You can update this to point to the desired version as needed.
- Additionally, you can access specific version endpoints as well as the latest version endpoints for each service (e.g. auth). For example:
  - http://api.localhost/auth/utils/version (for the latest version)
  - http://api.localhost/auth/v1/utils/version (for version 1)

### Creating Versions

To create a new version for a desired service while ensuring backward compatibility with older versions, follow these steps:

1. Copy the folder of the previous version in `./services/{SERVICE}/src/api/`. For example, to create version `v2`, copy the v1 folder: `./services/{SERVICE}/src/api/v1` → `./services/{SERVICE}/src/api/v2`
2. Inside the newly copied version folder (`./services/{SERVICE}/src/api/v2/`), update the imports to reference the new version’s code. For example, change the import in `./services/{SERVICE}/src/api/v2/routes/utils.py` from:
   `from src.api.v1.routes import auth, users, utils` to: `from src.api.v2.routes import auth, users, utils`
3. In the appropriate files (e.g., `./services/{SERVICE}/src/api/v2/routes/utils.py`), change any version-related values to reflect the new version. For example, change:
   `return "v1"` to: `return "v2"`
4. Create a new app for the version `./services/{SERVICE}/src/main.py`:
5. At the top of `./services/{SERVICE}/src/main.py`, import the new router: `from src.api.v2.main import api_router as v2_router`
6. Create a new FastAPI app instance for version `v2` and mount it to the main app:

```
app_v2 = FastAPI(version="v2", title=settings.PROJECT_NAME, docs_url=settings.DOCS_URL)

app_v2.include_router(v2_router)

app.mount("/v2", app_v2)
```

3. Update the latest version router (e.g. `app.include_router(v1_router)` to `app.include_router(v2_router)`)

## Database Migrations

This project uses Alembic for database migrations, allowing you to manage changes to your database schema easily.

Follow these steps to make database schema changes for the desired service:

1. Make Changes to the Models
   Update the tables in the `./services/{SERVICE}/src/models.py` file as needed. For example, you might add a new column or modify an existing one.
2. Start a shell session in the desired service (e.g. auth)
   Open a terminal and run the following command (while containers are running):

```
docker compose exec auth bash
```

3. Run the Autogenerate Revision
   Use Alembic to create a new migration file that reflects the changes made in the models. Run the following command, replacing the message with a descriptive one about your changes:

```
alembic revision --autogenerate -m "{INSERT DESCRIPTION OF CHANGES HERE}"
```

5. Apply the Migration
   To apply the new migration and update your database schema, run:

```
alembic upgrade head
```

## Linter

In addition to the pre-commit hook, you can manually run lint checks using the script located in the `./services/{SERVICE}/lint.sh` file of each service. This script is designed to check for code errors and enforce coding standards across your services code.

You can execute all linters using the following bash script, which will completely wipe volumes and rebuild the containers:

```
bash scripts/lint.sh
```

If your containers are already running and you want to execute the linter without stopping the current processes, run the following command in the desired services container (e.g. auth)

```
docker compose exec -t auth bash scripts/lint.sh
```

Keep in mind these checks will also be done when pushing to the main branch.

## Service Uniformity

In this project, it is essential to maintain consistent naming conventions for all services, Docker containers, and configuration variables. Adhering to these standards ensures uniformity and easier management across the entire system.

### Service Folder Naming

- Every service folder in the `services/` directory must be named according to the service's core functionality, using lowercase letters.
- Example: The authentication service should be named `auth`.

### Docker Container Naming

- When creating the Docker container for each service, it should be named all lowercase: `{service-name}`.
- For example: the authentication service would be named `auth`

### Environment Variables

- The `.env` file will define most of the environment variables used for local development and production. However, some variables are service-specific in `docker-compose.yml`. For example, each service must pass the environment variable `POSTGRES_DB` for database configuration. Ensure that the value of `POSTGRES_DB` corresponds to the service being developed.
- Example in docker-compose.yml for the `auth` service:

```
services:
  auth:
    environment:
      POSTGRES_DB: ${AUTH_DATABASE?Variable not set}
```

### Other Configurations

- In the src/core/config.py file, there is a critical variable called `SERVICE_NAME`. This variable should always be updated to match the name of the service (e.g. for the `auth` service: `SERVICE_NAME: str = "auth"`).
- Each service should contain a `lint.sh` and a `run-tests.sh` in the scripts folder, this ensures you are able to run the global `scripts/test.sh` and `scripts/lint.sh` files for testing/linting all services (also used for github actions on commit).

## Role-Based Access & User Dependencies

To ensure security and maintain consistency across all services, this project implements a centralized Role-Based Access Control (RBAC) system. This system not only protects endpoints by verifying user roles but also provides a uniform way to access the authenticated user's information through FastAPI's dependency injection.

### Shared Authorization Library

The core logic for authentication and authorization is centralized in a shared library located at `./libs/auth_lib/`. This ensures that every service uses the exact same validation rules and dependencies, eliminating code duplication and potential security inconsistencies.

The primary authorization dependencies that you will use in your services are exported from `libs.auth_lib.api.deps`.

### Uniform Role Definitions

Role definitions are critical for system-wide security. All user roles are defined in a shared `UserRole` enum within the `auth_lib`. This provides a single source of truth for permissions. It is essential that all services rely on this central enum when defining endpoint access levels.

Key permission sets are pre-configured for common use cases:

- `GEN_AUTH_ROLES`: For any authenticated user.

- `MGMT_AUTH_ROLES`: For administrative users (e.g., `admin`, `root`).

- `ROOT_AUTH_ROLES`: For system-level `root` users only.

### Using Authorization Dependencies

Protecting an endpoint and retrieving the current user's data is accomplished by adding a pre-configured dependency to your path operation function. These dependencies serve as both a security guard and a data provider. If the incoming request's token is invalid or lacks the required role, the dependency automatically raises a `401 Unauthorized` or `403 Forbidden` error.

1.  **Import the Dependency**
    First, import the required dependency from the shared `auth_lib`. For example, to secure an endpoint for any authenticated user:

    ```python
    from libs.auth_lib.api.deps import gen_auth_token_dep
    from libs.auth_lib.schemas import TokenData
    ```

2.  **Add it to Your Endpoint**
    Next, add the dependency to your function signature. The dependency will inject a `TokenData` object containing the user's information (`user_id`, `role`, etc.) if the authorization is successful.

    ```python
    @router.get("/me")
    async def get_my_profile(user_token: TokenData = Depends(gen_auth_token_dep)):
        # The user is now authenticated. You can access their data via user_token.
        user_id = user_token.user_id

        # ... fetch and return user profile from database using user_id
        return {"user_id": user_id, "role": user_token.role}
    ```

The default available dependencies are:

- **`gen_auth_token_dep`**: General access (any authenticated user).
- **`mgmt_auth_token_dep`**: Management access (`admin`, `root`).
- **`root_auth_token_dep`**: Root-only access.

## More to come

- NATS and how services send and receive events to communicate.
