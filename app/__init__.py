from fastapi import FastAPI
from .auth.routes import auth_router
from .jobs.routes import job_router

version = 'v1'
app = FastAPI(
    title='JobFinder',
    description='A REST API for a job finder web service',
    version=version
)

app.include_router(auth_router, tags=['auth'])  # include routers in our main app
app.include_router(job_router, tags=['jobs'])  # include routers in our main app
