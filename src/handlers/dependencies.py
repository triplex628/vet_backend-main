from fastapi import Depends, Body
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from hashlib import sha256
import hmac
import base64

#from cryptography.hazmat.backends import default_backend
#from cryptography.hazmat.primitives import hashes
#from cryptography.hazmat.primitives.asymmetric import padding, serialization

from src import services
from src import schemas
from src.utils import exceptions
from src import config
from src import database
from src import repositories

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/create")
prodamus_sign_scheme = APIKeyHeader(name='sign', auto_error=False)

SECRET_KEY = 'b6b1ab83593b9541b1b2b47925a42fe1f46fa6f6b1eda6e0d364ba1da69950b3'


def get_current_user(db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)) -> schemas.User:
    try:
        payload = jwt.decode(token, config.get_settings().secret_key, algorithms=config.get_settings().access_token_alg)
        email: str = payload.get('sub')
        if email is None:
            raise exceptions.credentials_exception
        user_uuid_str: str = payload.get('access_uuid')
        if user_uuid_str is None:
            raise exceptions.credentials_exception
        token_data = schemas.TokenData(email=email, uuid_str=user_uuid_str)
    except JWTError:
        raise exceptions.credentials_exception
    user = services.user.get_user_by_email(db, email)
    if user is None:
        raise exceptions.credentials_exception
    if user_uuid_str != repositories.get_uuid_token(db, user.id).__str__():
        raise exceptions.credentials_exception
    return user


def get_current_active_user(current_user: schemas.User = Depends(get_current_user)) -> schemas.User:
    if current_user.is_active is False:
        raise exceptions.bad_request_exception('Inactive user')
    return current_user


#def verify_signature(signature: str = Depends(prodamus_sign_scheme), data: bytes = Body(...)):
#    signature = base64.b64decode(signature)
#    public_key = "-----BEGIN PUBLIC KEY-----\n" + public_key + "\n-----END PUBLIC KEY-----"
#    public_key = serialization.load_pem_x509_certificate(public_key.encode(), default_backend()).public_key()
#    try:
#        public_key.verify(
#            signature,
#            raw_body,
#            padding.PKCS1v15(),
#            hashes.SHA256(),
#        )
#    except Exception as e:
#        raise exceptions.credentials_exception
#
#    return signature
#    #expected_signature = generate_signature(data, SECRET_KEY)
#    #print(f'expected_signature={expected_signature}')
#    #print(f'got_signature={signature}')
#    #if not hmac.compare_digest(signature, expected_signature):
#    #    raise exceptions.credentials_exception
#    #return signature
#

def generate_signature(data: bytes, secret_key: str):
    hmac_digest = hmac.new(SECRET_KEY.encode(), data, sha256)
    print(f'hmac_digest={hmac_digest.digest()}')
    signature = base64.b64encode(hmac_digest.digest()).decode()
    return signature
