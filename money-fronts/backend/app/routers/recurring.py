from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/recurring-rules", tags=["recurring-rules"])


@router.get("", response_model=list[schemas.RecurringRuleOut])
def get_recurring_rules(db: Session = Depends(get_db)):
    return crud.list_recurring_rules(db)


@router.post("", response_model=schemas.RecurringRuleOut, status_code=201)
def create_recurring_rule(payload: schemas.RecurringRuleCreate, db: Session = Depends(get_db)):
    return crud.create_recurring_rule(db, payload)


@router.delete("/{rule_id}", status_code=204)
def delete_recurring_rule(rule_id: str, db: Session = Depends(get_db)):
    if not crud.delete_recurring_rule(db, rule_id):
        raise HTTPException(status_code=404, detail="Regra recorrente não encontrada")


@router.post("/generate")
def generate(month: int | None = None, year: int | None = None, db: Session = Depends(get_db)):
    today = date.today()
    created = crud.generate_recurring_transactions(db, month or today.month, year or today.year)
    return {"created": created}
