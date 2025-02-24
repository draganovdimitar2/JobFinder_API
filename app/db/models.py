from sqlmodel import SQLModel, Field, Column, Relationship
import sqlalchemy.dialects.postgresql as pg
from typing import List, Optional
from enum import Enum
from datetime import datetime
import uuid


class User(SQLModel, table=True):
    __tablename__ = 'users'
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,  # Automatically generate a new UUID for each user
        sa_column=Column(
            pg.UUID,  # PostgreSQL-specific data type for UUIDs
            primary_key=True,  # Set uid as the primary key (enforcing uniqueness automatically)
            unique=True,  # Explicitly enforces uniqueness, though redundant on primary keys
            nullable=False  # Prevents NULL values in the uid column, ensuring each user has a UUID
        )
    )
    username: str = Field(nullable=False, unique=True)
    email: str = Field(nullable=False, unique=True)
    password_hash: str = Field(nullable=False, exclude=True)  # this field should be excluded from serialization
    role: str = Field(sa_column=Column(
        pg.VARCHAR, nullable=False, server_default='user'
    ))
    firstName: Optional[str] = Field(default=None)
    lastName: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True, nullable=False)
    # Relationships (lazy='selectin' argument optimizes query performance)
    applications: List['Applications'] = Relationship(back_populates='user', sa_relationship_kwargs={
        'lazy': 'selectin'})  # A user can submit multiple job applications. (one-to-many relationship)
    jobs: List['Jobs'] = Relationship(back_populates='author', sa_relationship_kwargs={
        'lazy': 'selectin'})  # A User (organization) can create multiple Job postings. (one-to-many relationship)
    liked_jobs: List['JobLikes'] = Relationship(back_populates='user', sa_relationship_kwargs={
        'lazy': 'selectin'})  # A user can "like" multiple jobs and a job can be "liked" by multiple user  (many-to-many relationship)

    notifications_received: List["Notification"] = Relationship(
        back_populates="recipient",
        sa_relationship_kwargs={"foreign_keys": "Notification.recipient_uid", "lazy": "selectin"}
    )
    notifications_sent: List["Notification"] = Relationship(
        back_populates="sender", sa_relationship_kwargs={"foreign_keys": "Notification.sender_uid", "lazy": "selectin"}
    )


class Jobs(SQLModel, table=True):
    __tablename__ = 'jobs'
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,  # Automatically generate a new UUID for each user
        sa_column=Column(
            pg.UUID,  # PostgreSQL-specific data type for UUIDs
            primary_key=True,  # Set uid as the primary key (enforcing uniqueness automatically)
            unique=True,  # Explicitly enforces uniqueness, though redundant on primary keys
            nullable=False  # Prevents NULL values in the uid column, ensuring each user has a UUID
        )
    )
    title: str = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    type: str = Field(nullable=False)
    likes: int = Field(default=0)
    category: str = Field(nullable=False)
    author_uid: uuid.UUID = Field(foreign_key="users.uid", nullable=False)
    is_active: bool = Field(default=True)
    author: 'User' = Relationship(
        back_populates='jobs', sa_relationship_kwargs={
            'lazy': 'selectin'})  # A job is created by one user (organization)  (Many-to-one relationship)
    applicants: List['Applications'] = Relationship(
        back_populates='job',
        sa_relationship_kwargs={'lazy': 'selectin'})  # A job can have multiple applicants (One-to-many relationship)
    liked_by: List['JobLikes'] = Relationship(
        back_populates='job', sa_relationship_kwargs={
            'lazy': 'selectin'})  # A job can be liked by multiple users and multiple users can like one job.  (Many-to-many relationship)


class JobLikes(SQLModel, table=True):  # association table, which maps user IDs to job IDs.
    __tablename__ = "job_likes"
    user_id: uuid.UUID = Field(foreign_key="users.uid", primary_key=True)
    job_id: uuid.UUID = Field(foreign_key="jobs.uid", primary_key=True)
    user: 'User' = Relationship(
        back_populates='liked_jobs')  # Many-to-one relationship with User. A like is associated with one user.
    job: 'Jobs' = Relationship(
        back_populates='liked_by')  # Many-to-one relationship with Jobs. A like is associated with one job


class StatusEnum(str, Enum):  # define enum for the status
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class Applications(SQLModel, table=True):
    __tablename__ = 'applications'
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,  # Automatically generate a new UUID for each application
        sa_column=Column(
            pg.UUID,  # PostgreSQL-specific data type for UUIDs
            primary_key=True,  # Set uid as the primary key (enforcing uniqueness automatically)
            unique=True,  # Explicitly enforces uniqueness, though redundant on primary keys
            nullable=False  # Prevents NULL values in the uid column, ensuring each user has a UUID
        )
    )
    user_uid: uuid.UUID = Field(default=None, foreign_key="users.uid", nullable=False)
    job_uid: uuid.UUID = Field(default=None, foreign_key="jobs.uid", nullable=False)
    status: StatusEnum = Field(
        default=StatusEnum.PENDING,  # Default value is pending
        nullable=False  # Prevent NULL values
    )
    coverLetter: str = Field(nullable=False)
    appliedAt: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    # Relationships
    user: 'User' = Relationship(
        back_populates='applications', sa_relationship_kwargs={
            'lazy': 'selectin'})  # Many-to-one relationship with User. An application is submitted by one user.
    job: 'Jobs' = Relationship(
        back_populates='applicants', sa_relationship_kwargs={
            'lazy': 'selectin'})  # Many-to-one relationship with Jobs. An application is for one job.


class Notification(SQLModel, table=True):
    __tablename__ = 'notifications'
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            unique=True,
            nullable=False
        )
    )
    # The recipient of the notification (could be a company or an applicant)
    recipient_uid: uuid.UUID = Field(foreign_key="users.uid", nullable=False)
    # The sender of the notification (the one triggering the event, e.g., company or system)
    sender_uid: uuid.UUID = Field(foreign_key="users.uid", nullable=False)
    message: str = Field(nullable=False)
    is_read: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(pg.TIMESTAMP, nullable=False)
    )

    # Relationships
    recipient: 'User' = Relationship(
        back_populates="notifications_received",
        sa_relationship_kwargs={"foreign_keys": "Notification.recipient_uid", "lazy": "selectin"}
    )
    sender: 'User' = Relationship(
        back_populates="notifications_sent",
        sa_relationship_kwargs={"foreign_keys": "Notification.sender_uid", "lazy": "selectin"}
    )
