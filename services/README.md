# Services

## Service Architecture & Structure

All components of this backend—including microservices, workers, and schedulers—adhere to a **strict, uniform architecture and naming convention**. This standardization is essential for easier management, automation, and faster developer context-switching across the entire system.

### Service Uniformity and Naming Conventions

Maintaining consistent naming for services, containers, and configuration variables is mandatory. All names must be **all lowercase** and descriptive of the service's core function.

#### Key Naming Conventions

| Component                   | Standard                                                   | Example                          | Notes                                                                                         |
| :-------------------------- | :--------------------------------------------------------- | :------------------------------- | :-------------------------------------------------------------------------------------------- |
| **Service Folder**          | Core functionality, all lowercase.                         | `./services/auth`                | Located in the top-level `services/` directory.                                               |
| **Docker Container**        | All lowercase, matches the service name.                   | `auth`                           | Name used within `docker-compose.yml`.                                                        |
| **`SERVICE_NAME` Variable** | Must match the service folder/container name.              | `SERVICE_NAME: str = "auth"`     | Set in `src/core/config.py` within the service. Critical for configuration and event routing. |
| **Database Variable**       | Service-specific database name is passed to the container. | `POSTGRES_DB: ${AUTH_DATABASE?}` | Defined in `.env` file and passed through `docker-compose.yml`.                               |

#### Required Scripts

For global automation (GitHub Actions, development scripts), every service must contain a `scripts/` folder with the following two bash files:

- **`run-tests.sh`**: For running tests on that specific service.
- **`lint.sh`**: For running lint checks and code quality standards.

### Standard Service Structure

The directory structure is identical for every service, worker, and scheduler, ensuring consistency.

| Folder/File         | Purpose                                                                                                                       | Example Path                       |
| :------------------ | :---------------------------------------------------------------------------------------------------------------------------- | :--------------------------------- |
| **`src/`**          | The core application source code.                                                                                             | `services/{SERVICE}/src/`          |
| **`src/main.py`**   | The main service entry point. Initializes the FastAPI app, defines routers, and **manually sets the default API version**.    | `services/{SERVICE}/src/main.py`   |
| **`src/api/{vX}/`** | **Versioned API Endpoints.** A specific API version folder (e.g., `v1`, `v2`). Contains the endpoint routes for that version. | `services/{SERVICE}/src/api/v1/`   |
| **`src/models.py`** | Defines the database schema (SQLAlchemy models) for the service. Used by Alembic for migrations.                              | `services/{SERVICE}/src/models.py` |
| **`tests/`**        | Houses all unit and integration tests for the service.                                                                        | `services/{SERVICE}/tests/`        |
| **`alembic/`**      | Database migration files.                                                                                                     | `services/{SERVICE}/alembic/`      |

### Shared Libraries (`libs/`) Inheritance

The root-level **`libs/`** directory contains centralized, reusable code. Services consume this code directly, eliminating duplication and enforcing global consistency for critical features (like security and event handling).

| Library Example       | Core Functionality                        | Purpose and Usage                                                                                                                                              |
| :-------------------- | :---------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`libs/auth_lib/`**  | **Role-Based Access Control (RBAC)**      | Centralizes all authentication and authorization logic. Services import dependencies (e.g., `gen_auth_token_dep`) to secure endpoints and retrieve user roles. |
| **`libs/utils_lib/`** | **Standard Shared Service Functionality** | Provides common base schemas/tables, database session helpers, event routing logic, and general utilities used across all services.                            |

## Tests

In each service of this project, we have implemented automated testing to ensure code quality and functionality.
By default, tests are configured to run automatically using GitHub Actions whenever there is a push to the main branch. This ensures that any changes made to the codebase are validated against the test suite, helping to maintain the integrity of the project.

You can execute all tests using the following bash script, which will completely wipe volumes and rebuild the containers:

```bash
bash scripts/test.sh
```

If your containers are already running and you want to execute the tests without stopping the current processes, you can run tests for each service (e.g. auth):

```bash
docker compose exec -t auth bash scripts/run-tests.sh
```

To evaluate how much of the code is covered by tests, we utilize coverage reporting. The coverage results can be found in the following location of each service (e.g. auth) `./services/auth/htmlcov/index.html`

### Important Note

Tests can only be run in `local` and `staging` environments. Ensure you are in the appropriate environment before attempting to run the tests to avoid unexpected behavior.

## Linter

In addition to the pre-commit hook, you can manually run lint checks using the script located in the `./services/{SERVICE}/lint.sh` file of each service. This script is designed to check for code errors and enforce coding standards across your services code.

You can execute all linters using the following bash script, which will completely wipe volumes and rebuild the containers:

```bash
bash scripts/lint.sh
```

If your containers are already running and you want to execute the linter without stopping the current processes, run the following command in the desired services container (e.g. auth)

```bash
docker compose exec -t auth bash scripts/lint.sh
```

Keep in mind these checks will also be done when pushing to the main branch.

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

```python
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

```bash
docker compose exec auth bash
```

3. Run the Autogenerate Revision
   Use Alembic to create a new migration file that reflects the changes made in the models. Run the following command, replacing the message with a descriptive one about your changes:

```bash
alembic revision --autogenerate -m "{INSERT DESCRIPTION OF CHANGES HERE}"
```

5. Apply the Migration
   To apply the new migration and update your database schema, run:

```bash
alembic upgrade head
```

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

# Service Communication

This section details the event-driven architecture used for communication between services. The system is designed to ensure data consistency, trigger asynchronous workflows, and retrieve information across service boundaries reliably.

### Architecture

Our inter-service communication is built on a durable, event-driven foundation:

- **In/Outbox Pattern:** We utilize an In/Outbox pattern to guarantee **at-least-once message delivery**, preventing data loss even during service outages.
- **NATS Jetstream:** NATS Jetstream serves as the high-performance message broker, enabling fast and persistent publish/subscribe (pub/sub) capabilities.
- **Acknowledgements:** Subscribers send acknowledgements (`ack`) upon successful event processing, confirming receipt and completion.
- **Automated Retries:** A scheduled job periodically re-sends any failed or pending outbox events, ensuring eventual consistency.
- **Monitoring:** Failed events are exposed as Prometheus metrics, allowing for monitoring and alerting.

### Implementing Service Communication

The process of creating and handling events is standardized to ensure consistency. The following guide walks through publishing a new event and subscribing to it.

#### Step 1: Define an Event Route

First, define a unique route for your event. This acts as a centralized, typed identifier for the event's subject name, preventing typos and ensuring uniformity between publishers and subscribers.

Event routes for a given service should be defined in its shared library (e.g., `libs/auth_lib/events.py`).

```python
from libs.utils_lib.core.faststream import nats
from libs.utils_lib.schemas import EventRoute
from src.core.config import settings
CREATE_USER_ROUTE = EventRoute(
   service=settings.SERVICE_NAME,
   name="create.user",
   stream_name=nats.stream,
)
```

- `service` Always use `settings.SERVICE_NAME`. This prefixes the subject with the publishing service's name (e.g., `auth.user.created`).
- `name` A unique, dot-separated name describing the event.
- `stream_name` The NATS stream the event will be published to. This is typically the same for all routes.

#### Step 2: Create the Event Schema

Next, define the data payload for your event using a schema. This ensures that event data is strongly typed and validated. Schemas should also be defined in the shared library (e.g., `libs/auth_lib/schemas.py`).

```python
from libs.utils_lib.schemas import EventMessageBase
class CreateUserEvent(EventMessageBase):
  user: Users
```

- `EventMessageBase`: This base schema automatically includes essential fields like `event_id` and the publishing `service`.

#### Step 3: Publish the Event

Publishing is a two-part process: first, create an `Outbox` entry in the database within your transaction, and second, publish it to NATS after the transaction commits. Helper functions streamline this process.

This is typically done within a database transaction where a resource is being created or updated.

```python
from uuid import uuid4
from libs.auth_lib.schemas import CreateUserEvent
from libs.utils_lib.crud import create_outbox_event
from libs.utils_lib.api.events import handle_publish_event
event_users_create_user_id = uuid4()
event_users_create_user_schema = CreateUserEvent(
   event_id=event_users_create_user_id, user=new_user
)

event_users_create_user = await create_outbox_event(
   session=session,
   event_id=event_users_create_user_id,
   event_type=CREATE_USER_ROUTE.subject_for("users"),
   data=event_users_create_user_schema.model_dump(mode="json"),
   commit=False,
)

await handle_publish_event(
   session=session,
   event=event_users_create_user,
   event_schema=event_users_create_user_schema,
)
```

Key parameters for `create_outbox_event`:

- `session` The current active database session.
- `event_id` A unique UUID for this event instance.
- `event_type` The event's subject name. The `subject_for()` helper on your `EventRoute` generates this, taking the target service as an argument.
- `data` The JSON-serialized event schema.
- `commit` Set to `False` if you plan to commit the outbox event along with other database changes in the same transaction.

The `handle_publish_event` function then takes the created outbox entry and publishes its payload to the NATS Jetstream.

#### Step 4: Subscribing to the event

Subscribing to an event involves creating a handler that listens on a specific NATS subject. This process is standardized using a decorator and a helper function to manage the complexities of the In/Outbox pattern and message acknowledgements.

1.  **The Subscriber Decorator:** The `@nats_router.subscriber` decorator from FastStream registers a function to listen for messages. We use the `EventRoute` object created in Step 1 to provide the correct `subject`, `stream`, and other configuration details, ensuring consistency.

2.  **The `handle_subscriber_event` Helper:** This function wraps your core business logic. It's responsible for creating an `Inbox` entry to prevent duplicate processing, running your logic within a database transaction, and sending the final acknowledgement (`ack`) back to the publisher upon success.

```python
from faststream.nats.fastapi import NatsRouter

from libs.auth_lib.api.events import CREATE_USER_ROUTE
from libs.auth_lib.schemas import CreateUserEvent
from libs.utils_lib.api.events import handle_subscriber_event

nats_router = NatsRouter()

@nats_router.subscriber(
    subject=CREATE_USER_ROUTE.subject,
    stream=CREATE_USER_ROUTE.stream,
    pull_sub=CREATE_USER_ROUTE.pull_sub,
    durable=CREATE_USER_ROUTE.durable,
)
async def create_user_event(session: async_session_dep, data: CreateUserEvent) -> None:

    async def process_event(session: AsyncSession, data: CreateUserEvent) -> None:

        dbObj = Users.model_validate(data.user)
        session.add(dbObj)
        await session.commit()
        await session.refresh(dbObj)

   await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type=CREATE_USER_ROUTE.subject,
        process_fn=process_event,
        data=data,
    )

```

- `process_event`: An inner function that contains only the core business logic (e.g., creating a user in the local database). It must accept `session` and `data` as arguments.
- `handle_subscriber_event`: The helper that orchestrates the process. It takes your business logic (`process_fn`) and executes it safely within the transactional inbox flow.

# Prometheus Metrics

Prometheus serves as the primary source of monitoring for this project. All services, schedulers, and workers are instrumented to expose performance and operational metrics.

## Metrics Endpoint and Access

The metrics endpoint is exposed uniformly by every component on port `9000` inside the container. The standard path is /metrics.
