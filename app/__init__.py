from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth.routes import auth_router
from .jobs.routes import job_router
from .applications.routes import application_router

version = 'v1'
app = FastAPI(
    title='JobFinder',
    description='A REST API for a job finder web service',
    version=version
)

origins = [
    "https://diman-job-ui.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Angular server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix='/auth', tags=['auth'])  # include routers in our main app
app.include_router(job_router, prefix='/jobs', tags=['jobs'])
app.include_router(application_router, prefix='/application', tags=['applications'])
