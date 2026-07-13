from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=list[schemas.AccountOut])
def get_accounts(db: Session = Depends(get_db)):
    return crud.list_accounts(db)


@router.post("", response_model=schemas.AccountOut, status_code=201)
def create_account(payload: schemas.AccountCreate, db: Session = Depends(get_db)):
    return crud.create_account(db, payload)
