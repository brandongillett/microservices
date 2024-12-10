<p align="center">
  <a href="" rel="noopener">
</p>

<h1 align="center">Development</h1>

<h3 align=center>Local Endpoints (Default)</h3>

<h4 align="center">
  Traefik Dashboard: <a href="http://traefik.localhost/">http://traefik.localhost/</a><br>
  Adminer: <a href="http://adminer.localhost/">http://adminer.localhost/</a><br>
  Backend: <a href="http://auth.localhost/">http://{SERVICE}.localhost/ (ex. http://auth.localhost/)</a><br>
  Backend (Docs): <a href="http://auth.localhost/docs">http://{SERVICE}.localhost/docs (ex. http://auth.localhost/docs)</a><br>
  Backend (Redoc): <a href="http://auth.localhost/redoc ">http://{SERVICE}.localhost/redoc (ex. http://auth.localhost/redoc)</a><br>
</h4>

## Getting Started

### Running the Local Stack
To run the local development environment, use the following command (in a separate terminal):

```bash
docker compose watch
```

This will:
* Start all services in docker-compose.override.yml and docker-compose.yml files.
* Track all changes and properly sync files accordingly.
* Rebuild containers when necessary.

In contrast, if the containers are already running and you don't want to re-run them:

```bash
docker compose watch --no-up
```

## Environment Variables

### ```.env``` File
The ```.env``` file contains configuration settings that control various aspects of your development environment. It allows you to customize your setup without modifying the source code directly. Below are some key variables you may find in your ```.env``` file:

### Domain Configuration
DOMAIN: This variable defines the base domain. By default, it is set to localhost. You can change it to a custom domain, such as localhost.example, to suit your preferences.
Note: Change this to your domain in production/staging.

```plaintext
DOMAIN=localhost.example
```

This change will affect how you access your services. http://localhost.example/

### ```changethis``` Configurations
Several configurations in the .env file are marked as "changethis". You can leave these values as is for local development, although for deployments you will ideally modify these using GitHub Secrets.

### Other Configurations
There are many configurations but here is a brief rundown of the important ones and why/when you would want to change them.

* ```ENVIRONMENT```: Set to "local" by default, this will make it so that certain features are available to you in you development environment. You can also change these to "staging" and "production" for specified environments.
* ```PROJECT_NAME```: This variable will be used throughout the project, without worrying about inconsistencies with spelling of your project/app name.
* ```STACK_NAME```: This is used as tagging containers with prefix labels for Docker and Traefik (ideally changed in different environments).
* ```SECRET_KEY```: This variable is used with your JWT token encryption (very important to have a strong variable in production environments).

## Virtual Environment

### Setup
This project utilizes a virtual environment to manage dependencies effectively. Dependencies are managed with [uv](https://docs.astral.sh/uv/). Follow the steps below to install the necessary packages and activate the virtual environment.

Once you have ```uv``` installed, navigate to the desired service in ```./services/``` directory ```ex. ./services/auth``` and install all the required dependencies with the following command:

```bash
uv sync
```

This command will set up the virtual environment and install the necessary packages specified in your project.

### Activating the Virtual Environment
After installing the dependencies, you can activate the virtual environment with the following command from the service directory ```ex. ./services/auth```:
```bash
source .venv/bin/activate
```

## Formatting

To maintain code quality and consistency, our project utilizes a custom formatting script with a pre-commit hook. This setup ensures that code adheres to our standards before being added to the repository.

#### Preferred Method: Formatting Script 
Instead of running pre-commit directly, use the formatting script ```scripts/format.sh```, which formats all files and ensures pre-commit checks are also run. This is the recommended approach to maintain consistency across the project.

To format and check all files, run:

```bash
bash scripts/format.sh
```

This script:

* Formats and lints all services and libs folders.
* Runs pre-commit hooks across all files to verify compliance.

## Services

### Tests
In the each service of this project, we have implemented automated testing to ensure code quality and functionality.
By default, tests are configured to run automatically using GitHub Actions whenever there is a push to the main branch. This ensures that any changes made to the codebase are validated against the test suite, helping to maintain the integrity of the project.

You can execute all tests using the following bash script, which will completely wipe volumes and rebuild the containers:
```
bash scripts/test.sh
```

If your containers are already running and you want to execute the tests without stopping the current processes, you can run tests for each service (ex. auth):
```
docker compose exec -t auth-service bash scripts/tests-start.sh
```

To evaluate how much of the code is covered by tests, we utilize coverage reporting. The coverage results can be found in the following location ```./services/{SERVICE}/htmlcov/index.html (ex. ./services/auth/htmlcov/index.html```

#### Important Note
Tests can only be run in ```local``` and ```staging``` environments. Ensure you are in the appropriate environment before attempting to run the tests to avoid unexpected behavior.

### Versioning
In this project, we have adopted a versioning strategy for our API to ensure smooth upgrades and backward compatibility for both the development and production environments. The versioning system is designed to provide clear separation between different API versions, while also offering flexibility for continuous development and deployment. Below is a breakdown of how the versioning system works:

#### Versioning Overview
We follow the principle of semantic versioning where each version of the API is clearly identified by a version number. This allows us to introduce new features, deprecate old ones, and make breaking changes in a controlled manner.

* By default, the documentation for the latest version is available at http://api.localhost/docs. You can also access documentation for specific versions through the following URLs (note: docs/redoc are only available for the local environment):
  * http://api.localhost/v1/docs (for version 1)
  * http://api.localhost/v1/redoc (Redoc for version 1)
* The latest version is manually set in the ```backend/app/main.py file```. In this file, you determine which version of the API the latest version endpoint should point to by including the corresponding router. For example, to point to ```v1```, you would set: ```app.include_router(v1_router)``` This step is essential for local development and testing, as tools like pytest rely on the latest version when running tests. You can update this to point to the desired version as needed.
* Additionally, you can access specific version endpoints as well as latest version endpoints. For example:
  * http://api.localhost/utils/version (for the latest version)
  * http://api.localhost/v1/utils/version (for version 1)


#### Creating Versions
To create a new version while ensuring backward compatibility with older versions, follow these steps:

1. Copy the folder of the previous version in ```backend/app/api/```. For example, to create version ```v2```, copy the v1 folder: ```backend/app/api/v1``` → ```backend/app/api/v2```
2. Inside the newly copied version folder (```backend/app/api/v2/```), update the imports to reference the new version’s code. For example, change the import in ```backend/app/api/v2/routes/utils.py``` from:
```from app.api.v1.routes import auth, users, utils``` to: ```from app.api.v2.routes import auth, users, utils```
3. In the appropriate files (e.g., ```backend/app/api/v2/routes/utils.py```), change any version-related values to reflect the new version. For example, change:
```return "v1"``` to: ```return "v2"```
4. Create new app for the version ```backend/app/main.py```:
   1. At the top of ```backend/app/main.py```, import the new router: ```from app.api.v2.main import api_router as v2_router```
   2. Create a new FastAPI app instance for version ```v2``` and mount it to the main app:
      ```
      app_v2 = FastAPI(version="v2", title=settings.PROJECT_NAME, docs_url=settings.DOCS_URL)

      app_v2.include_router(v2_router)

      app.mount("/v2", app_v2)
      ```
  3. Update the latest version router (e.g. ```app.include_router(v1_router)``` to ```app.include_router(v2_router)```)


### Database Migrations
This project uses Alembic for database migrations, allowing you to manage changes to your database schema easily.

Follow these steps to make database schema changes:
1. Make Changes to the Models
Update the tables in the ```backend/app/models.py``` file as needed. For example, you might add a new column or modify an existing one.
2. Start a Shell Session in the Backend Container
Open a terminal and start a shell session in the backend container:
```
docker compose exec backend bash
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

### Linter
In addition to the pre-commit hook, you can manually run lint checks using the script located in the ```backend/lint.sh``` file. This script is designed to check for code errors and enforce coding standards across your backend code.

To execute the linting checks, run the following command:
```
docker compose exec -t backend bash scripts/lint.sh
```

Keep in mind these checks will also be done when pushing to the main branch.
