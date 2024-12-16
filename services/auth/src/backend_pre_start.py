import asyncio

from libs.utils_lib.backend_pre_start import initialize_services, logger


def main() -> None:
    """
    Main function to run the initialization process.
    """
    try:
        logger.info("Initializing services...")
        asyncio.run(initialize_services())
        logger.info("Services finished initializing...")
    except Exception as e:
        logger.critical(f"Service initialization failed: {e}")


if __name__ == "__main__":
    main()
