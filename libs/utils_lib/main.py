import json
import logging
import os

from fastapi import FastAPI

from src.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAPI_PATH = f"./openapi/{settings.SERVICE_NAME}.json"


def generate_openapi(app: FastAPI) -> None:
    openapi_data = app.openapi()
    openapi_json = json.dumps(openapi_data, indent=2, sort_keys=True)
    app.openapi_schema = None  # Clear the schema to avoid caching issues

    # Check if the OpenAPI file already exists and is unchanged
    if os.path.exists(OPENAPI_PATH):
        with open(OPENAPI_PATH) as f:
            existing = f.read()
            if existing.strip() == openapi_json.strip():
                logger.info("OpenAPI schema unchanged — skipping write.")
                return

    # Write the OpenAPI schema to the file
    os.makedirs(os.path.dirname(OPENAPI_PATH), exist_ok=True)
    with open(OPENAPI_PATH, "w") as f:
        f.write(openapi_json)
        logger.info(f"Updated OpenAPI schema written to {OPENAPI_PATH}")
