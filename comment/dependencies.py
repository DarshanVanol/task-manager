from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from .config import settings
from dataclasses import dataclass

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # dummy, token comes from Django

@dataclass
class User:
    user_id: int
    username: str

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, settings.DJANGO_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        print("Payload: ", payload)
        user_id = payload.get("user_id") or payload.get("sub")  # Django SimpleJWT usually uses "user_id"
        username = payload.get("username")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return User(user_id=user_id, username=username)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")