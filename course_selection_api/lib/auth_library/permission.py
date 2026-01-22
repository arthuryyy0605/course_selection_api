from enum import Enum
from typing import Optional, Tuple
from fastapi import Depends
from fastapi.security import APIKeyHeader

from .jwt import JwtToken, JWTKey
from ..base_exception import BadRequestException, ForbiddenException, UnauthorizedException
from pydantic import BaseModel

from ...config import get_settings

_authorization = APIKeyHeader(name='Authorization', scheme_name="Authorization")
_settings = get_settings()


class Scope(Enum):
    ALL = 'all'
    GROUP = 'group'
    PERSONAL = 'personal'


class Permission(BaseModel):
    key: str
    scope: Scope


class User(BaseModel):
    id: str
    username: str
    roles: str
    attributes: list


class Auth(BaseModel):
    token: Optional[str]
    user: Optional[User]
    permission: Optional[Permission]


MASTER_KEY = 'master_key'


def get_permission(permissions: dict, platform: str, key: str) -> Permission:
    if platform not in permissions:
        raise ForbiddenException(
            message=f'Do not have permission to access {platform}')
    platform_permissions = permissions[platform]
    if MASTER_KEY in platform_permissions:
        return Permission(key=MASTER_KEY, scope=Scope.ALL)
    elif key not in platform_permissions:
        raise ForbiddenException(
            message=f'Do not have permission to access resource(key={key})')
    return Permission(key=key, scope=Scope(platform_permissions[key]))


def get_user_from_hyena_token_claims(claims: dict) -> User:
    user_id = claims['user_id']
    username = claims['username']
    roles = claims['roles']
    attributes = claims['attributes']
    print(claims)
    return User(id=user_id, username=username,
                roles=roles, attributes=attributes)


def generate_hyena_token_claims(user: User, permissions: dict) -> dict:
    return {
        'user_id': user.id,
        'username': user.username,
        'roles': user.roles,
        'attributes': user.attributes,
        'permissions': permissions
    }


def get_brand_ids_from_auth(auth: Auth) -> list[int]:
    brand_ids = auth.user.attributes.get('brand_id')
    if not brand_ids:
        return []
    elif isinstance(brand_ids, list):
        return [int(brand_id) for brand_id in brand_ids]
    else:
        return [int(brand_ids)]


class AgentAuth(Auth):
    usable_brand_ids: list[int]

    def has_permission(self) -> bool:
        return self.permission is not None

    def is_usable_brand_id(self, brand_id: int) -> bool:
        return self.has_permission() and (Scope.ALL == self.permission.scope or brand_id in self.usable_brand_ids)

    def is_allowed_brand_id(self, brand_id: int):
        if not self.is_usable_brand_id(brand_id):
            raise BadRequestException(message='Incorrect brand id.')

    @staticmethod
    def of(auth: Optional[Auth]):
        if auth:
            auth_dict = auth.dict()
            auth_dict['usable_brand_ids'] = get_brand_ids_from_auth(auth)
        else:
            auth_dict = {'usable_brand_ids': []}
        return AgentAuth(**auth_dict)


def get_auth_from_token(token: str) -> Tuple[User, Permission]:
    if JwtToken.get_claims(token):
        claims = JwtToken(JWTKey(jwt_private_key=None, jwt_public_key=_settings.jwt_public_key)).get_claims_and_verify_token(token)
        user = get_user_from_hyena_token_claims(claims)
        permission = Permission(key='Wild', scope=Scope.ALL)
        return user, permission
    else:
        raise UnauthorizedException()


def depend_auth():
    def dependency(authorization_token: str = Depends(_authorization)) -> Auth:
        user, permission = get_auth_from_token(authorization_token)
        return Auth(token=authorization_token, user=user, permission=permission)
    return Depends(dependency)
