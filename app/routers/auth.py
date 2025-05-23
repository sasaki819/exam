from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, schemas # Assuming schemas are in app.schemas
from app.core import security
from app.db.database import get_db # Assuming get_db is in app.db.database
from app.models.models import User # Assuming User model is in app.models.models
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Relative to the router prefix

def get_user_from_db(db: Session, username: str) -> User | None:
    return crud.crud_user.get_user_by_username(db, username=username)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = security.decode_token(token)
    if username is None:
        raise credentials_exception
    user = get_user_from_db(db, username=username)
    if user is None:
        raise credentials_exception
    return user

# Optional: If you add an 'is_active' field to your User model
# async def get_current_active_user(
#     current_user: Annotated[models.User, Depends(get_current_user)]
# ) -> models.User:
#     if not current_user.is_active: # Assuming you add an is_active field
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = crud.crud_user.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
