<p align="center">
  <a href="" rel="noopener">
</p>

<h1 align="center">Development</h1>

<h3 align=center>Local Endpoints (Default)</h3>

<h4 align="center">
  Frontend: <a href="http://localhost/">http://localhost/</a><br>
  Adminer: <a href="http://adminer.localhost/">http://adminer.localhost/</a><br>
  NATS: <a href="http://nats.localhost/">http://nats.localhost/</a><br>
  MailCatcher: <a href="http://mailcatcher.localhost/">http://mailcatcher.localhost/</a><br>
  Traefik Dashboard: <a href="http://traefik.localhost/">http://traefik.localhost/</a><br>
  Backend: <a href="http://api.localhost/auth">http://api.localhost/{SERVICE} (e.g. http://api.localhost/auth)</a><br>
  Backend (Docs): <a href="http://api.localhost/docs">http://api.localhost/{SERVICE}/docs (e.g. http://api.localhost/auth/docs)</a><br>
  Backend (Redoc): <a href="http://api.localhost/auth/redoc ">http://api.localhost/auth/redoc (e.g. http://api.localhost/auth/redoc)</a><br>
</h4>

## Getting Started

### Running the Development Environment

To run the local development environment, use the following command (in a separate terminal):

```
docker compose build && docker compose up --watch
```

This will:

- Start all services in docker-compose.override.yml and docker-compose.yml files.
- Track all changes and properly sync files accordingly.
- Rebuild containers when necessary.

## Environment Variables

### `.env` File

The `.env` file contains configuration settings that control various aspects of your development environment. It allows you to customize your setup without modifying the source code directly. Below are some key variables you may find in your `.env` file:

### Domain Configuration

DOMAIN: This variable defines the base domain. By default, it is set to localhost. You can change it to a custom domain, such as localhost.example, to suit your preferences.
Note: Change this to your domain in production/staging.

```
DOMAIN=localhost.example
```

This change will affect how you access your services. http://localhost.example/

### `changethis` Configurations

Several configurations in the .env file are marked as "changethis". You can leave these values as is for local development, although for deployments you will ideally modify these using GitHub Secrets.

### Other Configurations

There are many configurations, but here is a brief rundown of the important ones and why/when you would want to change them.

- `ENVIRONMENT`: Set to "local" by default, this will make it so that certain features are available to you in your development environment. You can also change these to "staging" and "production" for specified environments.
- `PROJECT_NAME`: This variable will be used throughout the project, without worrying about inconsistencies with the spelling of your project/app name.
- `STACK_NAME`: This is used for tagging containers with prefix labels for Docker and Traefik (ideally changed in different environments).
- `SECRET_KEY`: This variable is used with your JWT token encryption (it is very important to have a strong variable in production environments).

## Virtual Environment

### Setup

This project utilizes a virtual environment to manage dependencies effectively. Dependencies are managed with [uv](https://docs.astral.sh/uv/). Follow the steps below to install the necessary packages and activate the virtual environment.

Once you have `uv` installed, navigate to the desired service in the `./services/` directory and install all the required dependencies with the following command:

```
uv sync
```

This command will set up the virtual environment and install the necessary packages specified in your project.

### Activating the Virtual Environment

After installing the dependencies, you can activate the virtual environment with the following command from the service directory `e.g. ./services/auth`:

```
source .venv/bin/activate
```

## Formatting

To maintain code quality and consistency, our project utilizes a custom formatting script with a pre-commit hook. This setup ensures that code adheres to our standards before being added to the repository.

#### Preferred Method: Formatting Script 

Instead of running pre-commit directly, use the formatting script `scripts/format.sh`, which formats all files and ensures pre-commit checks are also run. This is the recommended approach to maintain consistency across the project.

To format and check all files, run:

```
bash scripts/format.sh
```

This script:

- Formats and lints all services and libs folders.
- Runs pre-commit hooks across all files to verify compliance.
