import json
from datetime import datetime
from functools import lru_cache
from uuid import UUID

import urllib3

from ..logger import get_prefix_logger_adapter
from ..setting import EnvironmentSettings


class Settings(EnvironmentSettings):
    auth_api_host: str
    api_getter_token: str


_user_mapping: dict[str, str] = {}
_logger = get_prefix_logger_adapter('auth_username_mapping')

SYSTEM_ID = '00000000-0000-0000-0000-000000000000'
MIGRATOR_ID = '10000000-0000-0000-0000-000000000000'
SYSTEM_USERNAME = 'System'


def _get_user_enumeration():
    global _http, _setting
    if _http is None:
        _http = urllib3.PoolManager()
    if _setting is None:
        _setting = Settings()

    url = f'{_setting.auth_api_host}/admin/user/enumeration'
    try:
        response = _http.request('GET', url, headers={
            'Authorization': _setting.api_getter_token})
        return json.loads(response.data.decode('utf-8'))['result']
    except Exception:
        _logger.exception('Can not get user enumeration')


@lru_cache(maxsize=1)
def _get_username_mapping(hash=None):
    return {u['id']: u['username'] for u in _get_user_enumeration()}


def get_username(uuid: str) -> str:
    if uuid in [SYSTEM_ID, MIGRATOR_ID]:
        return SYSTEM_USERNAME
    global _user_mapping
    if _user_mapping is None or (username := _user_mapping.get(uuid)) is None:
        # Non-existent users will cause a large number of repeated requests
        every_ten_minutes = datetime.now().strftime("%Y%m%d%H%M")[:-1]
        _user_mapping = _get_username_mapping(every_ten_minutes)
        username = _user_mapping.get(uuid, uuid)
    return username


class Operator(str):

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        try:
            UUID(v)
            return cls(get_username(v))
        except ValueError:
            return v
