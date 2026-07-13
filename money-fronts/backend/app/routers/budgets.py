from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


@router.get("", response_model=list[schemas.BudgetOut])
def get_budgets(month: int, year: int, db: Session = Depends(get_db)):
    return crud.list_budgets(db, month, year)


@router.post("", response_model=schemas.BudgetOut, status_code=201)
def create_budget(payload: schemas.BudgetCreate, db: Session = Depends(get_db)):
    return crud.create_budget(db, payload)


@router.get("/progress", response_model=list[schemas.BudgetProgress])
def get_budget_progress(month: int, year: int, db: Session = Depends(get_db)):
    return crud.budget_progress(db, month, year)
