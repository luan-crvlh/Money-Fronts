from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("", response_model=list[schemas.TransactionOut])
def get_transactions(
    month: int | None = None,
    year: int | None = None,
    category_id: str | None = None,
    account_id: str | None = None,
    db: Session = Depends(get_db),
):
    return crud.list_transactions(db, month, year, category_id, account_id)


@router.post("", response_model=schemas.TransactionOut, status_code=201)
def create_transaction(payload: schemas.TransactionCreate, db: Session = Depends(get_db)):
    return crud.create_transaction(db, payload)


@router.patch("/{transaction_id}", response_model=schemas.TransactionOut)
def update_transaction(
    transaction_id: str, payload: schemas.TransactionUpdate, db: Session = Depends(get_db)
):
    obj = crud.update_transaction(db, transaction_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return obj


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: str, db: Session = Depends(get_db)):
    ok = crud.delete_transaction(db, transaction_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
