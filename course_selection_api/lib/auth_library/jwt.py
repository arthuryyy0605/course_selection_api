import base64
import datetime
import json
import re
from abc import ABC, abstractmethod
from typing import Optional

import urllib3
from ..base_exception import UnauthorizedException
from ..setting import EnvironmentSettings
from jose import JWTError, jwk, jwt
from jose.exceptions import ExpiredSignatureError
from pydantic import BaseModel

from .exception import TokenExpiredException

_http = urllib3.PoolManager()


class JWTKey(EnvironmentSettings):
    jwt_public_key: str
    jwt_private_key: Optional[str]

    def get_public_key(self) -> bytes:
        return base64.b64decode(
            bytes(self.jwt_public_key, 'utf-8'))

    def get_private_key(self) -> Optional[str]:
        return base64.b64decode(
            bytes(self.jwt_private_key, 'utf-8')) if self.jwt_private_key else None


class JWTTokener(ABC):
    @property
    @abstractmethod
    def algorithm(self) -> str:
        pass

    issuer: str

    def __init__(self, key: JWTKey, issuer: str):
        self.private_key = key.get_private_key()
        self.public_key = key.get_public_key()
        self.issuer = issuer

    def generate_token(self, claims: dict, expired_time: int = None) -> str:
        if not self.private_key:
            raise ValueError('The private key is required')
        iat = datetime.datetime.now().timestamp()
        common_claims = {
            'iss': self.issuer,
            'iat': int(iat),
        }
        if expired_time and expired_time > 0:
            common_claims['exp'] = int(iat + expired_time)
        claims.update(common_claims)
        return jwt.encode(claims, self.private_key, algorithm=self.algorithm)

    def get_claims_and_verify_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.public_key, algorithms=[self.algorithm], issuer=self.issuer)
        except ExpiredSignatureError as e:
            raise TokenExpiredException()
        except JWTError as e:
            raise UnauthorizedException(message=str(e))


class JwtToken(JWTTokener):
    algorithm = 'ES256'
    issuer = 'wild_force.io'

    def __init__(self, key: JWTKey):
        super().__init__(key, self.issuer)

    @classmethod
    def get_claims(cls, token: str) -> dict:
        try:
            claims = jwt.get_unverified_claims(token)
            return claims if cls.issuer == claims.get('iss') else None
        except JWTError:
            return {}


class JWKKey(BaseModel):
    alg: str
    e: str
    kid: str
    kty: str
    n: str
    use: str

    def to_pem(self) -> bytes:
        return jwk.construct(self.dict()).to_pem()


def get_keys_from_online(keys_url: str) -> tuple[list[JWKKey], Optional[int]]:
    response = _http.request('GET', keys_url)
    data = json.loads(response.data.decode('utf-8'))['keys']

    max_age = None
    if cache_control := response.headers.get('cache-control', ''):
        match = re.search(r'max-age=(\d+)', cache_control)
        if match:
            max_age = int(match.group(1))
    return [JWKKey(**datum) for datum in data], max_age


class JWTTokenDecoder:
    @property
    @abstractmethod
    def algorithm(self) -> str:
        pass

    issuer: Optional[str]
    audience: Optional[str]
    keys: dict[str, bytes]

    def __init__(self, keys: list[JWKKey], issuer: str = None, audience: str = None):
        self.keys = {key.kid: key.to_pem() for key in keys}
        self.issuer = issuer
        self.audience = audience

    def _get_public_key(self, kid: str) -> Optional[JWKKey]:
        return self.keys.get(kid)

    def get_claims_and_verify_token(self, token: str, subject: str = None, verify_options=None) -> dict:
        headers = jwt.get_unverified_headers(token)
        kid = headers['kid']
        public_key = self._get_public_key(kid)
        if public_key is None:
            raise UnauthorizedException(
                message='Public key not found')
        try:
            return jwt.decode(token, public_key, algorithms=[self.algorithm],
                              issuer=self.issuer, audience=self.audience, subject=subject,
                              options=verify_options)
        except ExpiredSignatureError as e:
            raise TokenExpiredException()
        except JWTError as e:
            raise UnauthorizedException(message=str(e))
