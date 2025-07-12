from app.users import schemas, models
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, APIRouter, Response
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from sqlalchemy import or_


router = APIRouter()


@router.get('/')
def get_users(db: Session = Depends(get_db), limit: int = 10, page: int = 1, search: str = ''):
    skip = (page -1) * limit

    users = db.query(models.User).filter(
        or_(
            models.User.first_name.contains(search),
            models.User.last_name.contains(search)
        )
    ).limit(limit).offset(skip).all()

    return {'status': 'success', 'results': len(users), 'users': users}


@router.post('/', status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserSchema, db: Session = Depends(get_db)):
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
def update_user(userId: str, payload: schemas.UserSchema, db: Session = Depends(get_db)):
    user_query = db.query(models.User).filter(models.User.id == userId)
    db_user = user_query.first()

    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No user with this id: {userId} found')

    update_data = payload.model_dump(exclude_unset=True)

    user_query.update(update_data, synchronize_session=False)
    db.commit()
    db.refresh(db_user)
    return {"status": "success", "note": db_user}


@router.get('/{userId}')
def get_user(userId: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == userId).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No user with this id: {userId} found")
    return {"status": "success", "user": user}


@router.delete('/{userId}')
def delete_user(userId: str, db: Session = Depends(get_db)):
    user_query = db.query(models.User).filter(models.User.id == userId)
    note = user_query.first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No user with this id: {userId} found')
    user_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)