# Services

## Tests
In each service of this project, we have implemented automated testing to ensure code quality and functionality.
By default, tests are configured to run automatically using GitHub Actions whenever there is a push to the main branch. This ensures that any changes made to the codebase are validated against the test suite, helping to maintain the integrity of the project.

You can execute all tests using the following bash script, which will completely wipe volumes and rebuild the containers:
```
bash scripts/test.sh
```

If your containers are already running and you want to execute the tests without stopping the current processes, you can run tests for each service (e.g. auth-service):
```
docker compose exec -t auth-service bash scripts/tests-start.sh
```

To evaluate how much of the code is covered by tests, we utilize coverage reporting. The coverage results can be found in the following location of each service (e.g. auth) ```./services/auth/htmlcov/index.html```

### Important Note
Tests can only be run in ```local``` and ```staging``` environments. Ensure you are in the appropriate environment before attempting to run the tests to avoid unexpected behavior.

## Versioning
In this project, we have adopted a versioning strategy for our services to ensure smooth upgrades and backward compatibility for both the development and production environments. The versioning system is designed to provide clear separation between different API versions while also offering flexibility for continuous development and deployment. Below is a breakdown of how the versioning system works:

### Overview
We follow the principle of semantic versioning, where each version of the services is clearly identified by a version number. This allows us to introduce new features, deprecate old ones, and make breaking changes in a controlled manner.

* By default, the documentation for the latest version for each service (e.g. auth) is available at http://auth.localhost/docs. You can also access documentation for specific versions across all services (e.g. auth) through the following URLs (note: docs/redoc are only available for the local and staging environments):
  * http://auth.localhost/v1/docs (for version 1)
  * http://auth.localhost/v1/redoc (Redoc for version 1)
* The latest version is manually set in the ```services/{SERVICE}/app/main.py file```. In this file, you determine which version of the API the latest version endpoint should point to by including the corresponding router. For example, to point to ```v1```, you would set: ```app.include_router(v1_router)``` This step is essential for local development and testing, as tools like pytest rely on the latest version when running tests. You can update this to point to the desired version as needed.
* Additionally, you can access specific version endpoints as well as the latest version endpoints for each service (e.g. auth). For example:
  * http://auth.localhost/utils/version (for the latest version)
  * http://auth.localhost/v1/utils/version (for version 1)


### Creating Versions
To create a new version for a desired service while ensuring backward compatibility with older versions, follow these steps:

1. Copy the folder of the previous version in ```./services/{SERVICE}/app/api/```. For example, to create version ```v2```, copy the v1 folder: ```./services/{SERVICE}/app/api/v1``` → ```./services/{SERVICE}/app/api/v2```
2. Inside the newly copied version folder (```./services/{SERVICE}/app/api/v2/```), update the imports to reference the new version’s code. For example, change the import in ```./services/{SERVICE}/app/api/v2/routes/utils.py``` from:
```from app.api.v1.routes import auth, users, utils``` to: ```from app.api.v2.routes import auth, users, utils```
3. In the appropriate files (e.g., ```./services/{SERVICE}/app/api/v2/routes/utils.py```), change any version-related values to reflect the new version. For example, change:
```return "v1"``` to: ```return "v2"```
4. Create a new app for the version ```./services/{SERVICE}/app/main.py```:
  1. At the top of ```./services/{SERVICE}/app/main.py```, import the new router: ```from app.api.v2.main import api_router as v2_router```
  2. Create a new FastAPI app instance for version ```v2``` and mount it to the main app:
  ```
  app_v2 = FastAPI(version="v2", title=settings.PROJECT_NAME, docs_url=settings.DOCS_URL)
  
  app_v2.include_router(v2_router)
  
  app.mount("/v2", app_v2)
  ```
  3. Update the latest version router (e.g. ```app.include_router(v1_router)``` to ```app.include_router(v2_router)```)


### Database Migrations
This project uses Alembic for database migrations, allowing you to manage changes to your database schema easily.

Follow these steps to make database schema changes for the desired service:
1. Make Changes to the Models
Update the tables in the ```./services/{SERVICE}/app/models.py``` file as needed. For example, you might add a new column or modify an existing one.
2. Start a shell session in the desired service (e.g. auth)
Open a terminal and run the following command (while containers are running):
```
docker compose exec auth-service bash
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
In addition to the pre-commit hook, you can manually run lint checks using the script located in the ```./services/{SERVICE}/lint.sh``` file of each service. This script is designed to check for code errors and enforce coding standards across your services code.

To execute the linting checks, run the following command in the desired services container (e.g. auth)
```
docker compose exec -t auth-service bash scripts/lint.sh
```

Keep in mind these checks will also be done when pushing to the main branch.
