from fastapi import FastAPI
from .auth.routes import auth_router
from .jobs.routes import job_router
import logging

# Basic configuration
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more verbose output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Output logs to the console
    ]
)
logger = logging.getLogger("test_logger")

logger.info("This is a test INFO log")
logger.debug("This is a test DEBUG log")
logger.warning("This is a test WARNING log")
logger.error("This is a test ERROR log")
logger.critical("This is a test CRITICAL log")
version = 'v1'
app = FastAPI(
    title='JobFinder',
    description='A REST API for a job finder web service',
    version=version
)

app.include_router(auth_router, tags=['auth'])  # include routers in our main app
app.include_router(job_router, tags=['jobs'])  # include routers in our main app
