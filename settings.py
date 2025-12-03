from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ipstack_key: str = ""
    logger_name: str = "geolocation"


settings = Settings()
