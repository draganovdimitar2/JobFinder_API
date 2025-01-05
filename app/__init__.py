from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth.routes import auth_router
from .jobs.routes import job_router
from .applications.routes import application_router
import logging

logging.basicConfig(level=logging.DEBUG)
version = 'v1'
app = FastAPI(
    title='JobFinder',
    description='A REST API for a job finder web service',
    version=version
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix='/auth', tags=['auth'])  # include routers in our main app
app.include_router(job_router, prefix='/jobs', tags=['jobs'])
app.include_router(application_router, prefix='/application', tags=['applications'])
