from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str

    AZURE_BLOB_ACCOUNT_URL: str
    AZURE_BLOB_CONTAINER_NAME: str
    AZURE_BLOB_SAS_TOKEN: str
    model_config = SettingsConfigDict(  # read out .env file
        env_file=".env",
        extra="ignore"
    )


Config = Settings()  # call it everytime we need to access .env variable
