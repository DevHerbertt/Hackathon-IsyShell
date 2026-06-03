from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "IsyShell"
    version: str = "2.0.0"
    scripts_dir: str = "/opt/isyone/scripts"
    db_path: str = "./isyshell.db"
    default_token: str = "isy-hackathon-2026-default-token"
    execution_timeout: int = 120

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
