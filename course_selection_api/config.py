from functools import lru_cache

from course_selection_api.lib.setting import EnvironmentSettings


class Settings(EnvironmentSettings):
    db_host: str
    db_port: str
    db_user: str
    db_password: str
    db_name: str
    jwt_public_key: str
    jwt_private_key: str
    ENABLE_API_DOCS: str


@lru_cache()
def get_settings():
    return Settings()
