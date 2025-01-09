import pathlib

import pydantic
import pydantic_settings
import sqlalchemy.engine.url as sa_url
from dotenv import load_dotenv

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
DOTENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=DOTENV_PATH, override=True)


class PostgreSQLConnectionSettings(pydantic_settings.BaseSettings):
    """PostgreSQL connection settings."""

    DB_NAME: pydantic.SecretStr
    DB_HOST: pydantic.SecretStr
    DB_MIGRATION_HOST: pydantic.SecretStr
    DB_PORT: pydantic.SecretStr
    DB_USER: pydantic.SecretStr
    DB_PASS: pydantic.SecretStr

    IS_ECHO: bool = False

    @property
    def async_url(self) -> sa_url.URL:
        """Create an async URL for the PostgreSQL connection."""
        return sa_url.URL.create(
            drivername="postgresql+asyncpg",
            database=self.DB_NAME.get_secret_value(),
            username=self.DB_USER.get_secret_value(),
            password=self.DB_PASS.get_secret_value(),
            host=self.DB_HOST.get_secret_value(),
            port=int(self.DB_PORT.get_secret_value()),
        )

    @property
    def migration_async_url(self) -> sa_url.URL:
        """Create an async URL for the PostgreSQL connection."""
        return sa_url.URL.create(
            drivername="postgresql+asyncpg",
            database=self.DB_NAME.get_secret_value(),
            username=self.DB_USER.get_secret_value(),
            password=self.DB_PASS.get_secret_value(),
            host=self.DB_MIGRATION_HOST.get_secret_value(),
            port=int(self.DB_PORT.get_secret_value()),
        )

    @property
    def sync_url(self) -> sa_url.URL:
        """Create a sync URL for the PostgreSQL connection."""
        return sa_url.URL.create(
            drivername="postgresql",
            database=self.DB_NAME.get_secret_value(),
            username=self.DB_USER.get_secret_value(),
            password=self.DB_PASS.get_secret_value(),
            host=self.DB_MIGRATION_HOST.get_secret_value(),
            port=int(self.DB_PORT.get_secret_value()),
        )



postgresql_connection_settings = PostgreSQLConnectionSettings()
