from app.users import schemas, models
from sqlalchemy.orm import Session

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import HTTPBearer

from sqlalchemy.exc import IntegrityError
from app.database import get_db
from sqlalchemy import or_
from passlib.context import CryptContext
from typing import Annotated

from app.auth.auth import get_current_user
from app.users.models import User
from app.auth.schemas import Authinfo
from app.api_keys.routers import api_key_security


router = APIRouter()


bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
user_dependency = Annotated[dict, Depends(get_current_user)]
oauth2_bearer = HTTPBearer()


@router.get('/')
def get_users(db: Session = Depends(get_db),
              auth_info: dict = Depends(api_key_security),
              limit: int = 10,
              page: int = 1,
              search: str = ''):
    """
       Retrieve a list of users with optional pagination.

       Args:
           skip (int): Number of records to skip for pagination. Defaults to 0.
           limit (int): Maximum number of users to return. Defaults to 10.
           db (Session): SQLAlchemy database session (injected dependency).

       Returns:
           List[UserResponse]: A list of user data objects.
       """
    skip = (page -1) * limit
    if search is None:
        users = db.query(User).order_by(User.id.asc()).filter().limit(limit).offset(skip).all()
        return {'status': 'success', 'results': len(users), 'users': users}
    users = db.query(User).order_by(User.id.asc()).filter(
        or_(
            User.username.contains(search),
            User.first_name.contains(search),
            User.last_name.contains(search)
        )
    ).limit(limit).offset(skip).all()
    return {'status': 'success', 'results': len(users), 'users': users}


@router.post('/', status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserCrateSchema, db: Session = Depends(get_db)):

    """
       Create new a user

       Args:
           payload (UserCrateSchema): The user data from the request body
           db (Session): SQLAlchemy database session (injected dependency).

       Returns:
           UserCrateSchema: The newly created user object.

       raises:
               HTTPException: If user's already exists in the database.
       """

    new_user = models.User(
        username = payload.username,
        password = bcrypt_context.hash(payload.password)
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")
    return {'status': "success", 'username': new_user.username}


@router.get('/me', description="Get Current user")
def get_user_by_token(auth_info: Annotated[Authinfo, Depends(oauth2_bearer)]):
    return {"status": status.HTTP_200_OK,"username":auth_info.username, "message": "OK"}


@router.patch('/{userId}')
def update_user(userId: int, payload: schemas.UserUpdateSchema, db: Session = Depends(get_db)):

    """
           Updating the user

           Args:
               payload (UserUpdateSchema): The user data from the request body
               db (Session): SQLAlchemy database session (injected dependency).

           Returns:
               status: "success",
               user: The user is updated

           raises:
                   HTTPException: If user's already exists in the database.
           """

    user = db.query(models.User).filter(models.User.id == userId).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No user with this id: {userId} found')

    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return {"status": "success", "user": user}


@router.get('/{userId}')
def get_user(userId: int, db: Session = Depends(get_db)):
    """
        Retrieve a user by ID.

        Args:
            user_id (int): The ID of the user to retrieve.
            db (Session): SQLAlchemy database session (dependency injection).

        Returns:
            UserResponse: The user data if found.

        Raises:
            HTTPException: If the user with the given ID does not exist.
        """

    user = db.query(models.User).filter(models.User.id == userId).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No user with this id: {userId} found")

    return {"status": "success", "user": user}


@router.delete('/{userId}')
def delete_user(userId: str, db: Session = Depends(get_db)):
    """
        Delete a user by ID.

        Args:
            user_id (int): The ID of the user to retrieve.
            db (Session): SQLAlchemy database session (dependency injection).

        Returns:
            status: 200 OK
            message: Delete user is success

        Raises:
            HTTPException: If the user with the given ID does not exist.
        """

    user_query = db.query(models.User).filter(models.User.id == userId)
    note = user_query.first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No user with this id: {userId} found')
    user_query.delete(synchronize_session=False)
    db.commit()

    return {"status":status.HTTP_200_OK, "message": "delete user is success"}
