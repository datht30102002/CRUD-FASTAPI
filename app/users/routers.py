from app.users import schemas, models
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, APIRouter, Response
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from sqlalchemy import or_


router = APIRouter()


@router.get('/')
def get_users(db: Session = Depends(get_db), limit: int = 10, page: int = 1, search: str = ''):

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

    users = db.query(models.User).order_by(models.User.id.asc()).filter(
        or_(
            models.User.first_name.contains(search),
            models.User.last_name.contains(search)
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
        first_name = payload.first_name,
        last_name = payload.last_name
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")
    return {'status': "success", 'note': new_user}


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
