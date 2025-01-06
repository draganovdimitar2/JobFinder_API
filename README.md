# JobFinder

## Project Announcement: JobFinder 🚀

We are excited to announce that the **JobFinder** application is now live! This platform seamlessly integrates the back-end API and front-end interface to deliver a complete solution for connecting organizations and job seekers.

- **Explore the Application**: [JobFinder Application](https://diman-job-ui.vercel.app)
- **API Documentation**: [JobFinder API Documentation](https://diman-job-finder-fast-api-tpmk.onrender.com/docs)

#### Note
The back-end API is hosted on Render's free plan. Because of this, the initial access can take anywhere from **30 to 50 seconds** to load. We appreciate your patience!

#### Contributors
- **Back-End Development**: Developed by [Dimitar Draganov](https://github.com/draganovdimitar2) (me), the back-end API is built using FastAPI for performance and scalability.
- **Front-End Development**: Big thanks to [realun00](https://github.com/realun00), who designed and implemented the front-end with intuitive and responsive user interface.

Thank you for supporting JobFinder, and stay tuned for future updates and enhancements!
## Project Overview

The Job Finder API application will feature two types of users: **Organizations** and **Regular Users**. Each role will be able to perform the following operations:

### 1. Regular User
- **View Job Postings**: Can view existing job postings.
- **Apply for Jobs**: Can apply for active job postings.
- **Like Job Postings**: Can like an existing active job posting.
- **View Application Status**: Can see a list of all job postings they have applied for, including whether they have been approved or not.
- **Manage Account**: Can change their account information (name, password).
- **Deactivate Account**: Can deactivate (delete) their account.

### 2. Organization
- **View Job Postings**: Can view existing job postings.
- **Publish Job Postings**: Can publish job postings (edit and delete their own postings).
- **View Applicants**: Can view a list of candidates who have applied for a specific job posting.
- **Manage Applications**: Can approve or reject candidates.
- **Deactivate Account**: Can deactivate (delete) their account, which will make all their job postings inactive.

## Technical Requirements

Each object must meet the following requirements:

### 1. User
- **Attributes**: Unique identifier, name, email, password.
- **Applications**: A user can apply for multiple job postings.
- **Like**: A user can like a specific job posting only once.

### 2. Organization
- **Attributes**: Unique identifier, name, email, password.
- **Job Postings**: An organization can publish multiple job postings.
- **User Approval**: An organization can approve only one user for a specific job posting.

### 3. Job Posting
- **Attributes**: Unique identifier, title, description, number of likes, type of job (part-time, full-time, remote), and category (e.g., Office Administration, Development).
- **Category**: A job posting can belong to only one category.
- **Applicants**: A list of all users who have applied for the posting, along with their approval status.
  
## Getting Started
Follow the instructions below to set up and run your FastAPI project.

### Prerequisites
Ensure you have the following installed:

- Python >= 3.10
- PostgreSQL
  
## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/draganovdimitar2/JobFinder_API.git
    ```
2. Navigate to the project directory:
    ```bash
    cd JobFinder_API
    ```
3. Create and activate a virtual environment:
    ```bash
    python3 -m venv env
    ```
    * for powershell
    ```bash
    env\Scripts\activate
    ```
    * for linux/os
    ```bash
    source env/bin/activate
    ```
4. Install dependencies:
    ```bash
    pip install -r requirements.txt "fastapi[standard]"
    ```
5. Run database migrations to initialize the database schema:
    ```bash
    alembic upgrade head
    ```
    
## Running the application
Start the application:
```bash
fastapi dev app/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
