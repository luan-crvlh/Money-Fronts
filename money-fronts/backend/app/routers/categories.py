from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[schemas.CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    return crud.list_categories(db)


@router.post("", response_model=schemas.CategoryOut, status_code=201)
def create_category(payload: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return crud.create_category(db, payload)


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: str, db: Session = Depends(get_db)):
    ok = crud.delete_category(db, category_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
