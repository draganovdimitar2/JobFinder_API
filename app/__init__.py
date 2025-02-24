from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth.routes import auth_router
from .jobs.routes import job_router
from .applications.routes import application_router
from .notifications.routes import notification_router
from .errors import register_all_errors

version = 'v1'
app = FastAPI(
    title='JobFinder',
    description="JobFinder API is a RESTful service designed to connect job seekers with organizations. "
                "It enables users to view job postings, apply for jobs, manage applications, and interact with their accounts.\n\n"

                "User Roles:\n"
                "- Regular Users: Can view, apply for, like job postings, and manage their accounts.\n"
                "- Organizations: Can publish job postings, view applicants, and manage applications.\n\n"

                "This API supports role-based access control (RBAC) to ensure that each user can perform actions appropriate to their role.",
    version=version,
    contact={
        'name': 'Dimitar Draganov',
        'url': 'https://github.com/draganovdimitar2',
        'email': 'dragnovdimitar2@gmail.com'
    }
)

register_all_errors(app)  # register all custom errors

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix='/auth', tags=['auth'])
app.include_router(job_router, prefix='/jobs', tags=['jobs'])
app.include_router(application_router, prefix='/application', tags=['applications'])
app.include_router(notification_router, prefix='/notification', tags=['notifications'])