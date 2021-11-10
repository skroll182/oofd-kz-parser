from pydantic import BaseSettings


class Settings(BaseSettings):
    chromedriver_path: str
