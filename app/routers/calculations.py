from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Calculation
from app.schemas import CalculationCreate, CalculationRead, CalculationUpdate
from app.factory import CalculationFactory

router = APIRouter(prefix="/calculations", tags=["Calculations"])

# ADD (Create)
@router.post("", response_model=CalculationRead, status_code=status.HTTP_201_CREATED)
def create_calculation(calc_in: CalculationCreate, db: Session = Depends(get_db)):
    result = CalculationFactory.compute(calc_in.a, calc_in.b, calc_in.type)
    db_calc = Calculation(a=calc_in.a, b=calc_in.b, type=calc_in.type, result=result, user_id=calc_in.user_id)
    db.add(db_calc)
    db.commit()
    db.refresh(db_calc)
    return db_calc

# BROWSE (Read all)
@router.get("", response_model=List[CalculationRead])
def read_calculations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Calculation).offset(skip).limit(limit).all()

# READ (Read one)
@router.get("/{id}", response_model=CalculationRead)
def read_calculation(id: int, db: Session = Depends(get_db)):
    calc = db.query(Calculation).filter(Calculation.id == id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return calc

# EDIT (Update)
@router.patch("/{id}", response_model=CalculationRead)
def update_calculation(id: int, calc_in: CalculationUpdate, db: Session = Depends(get_db)):
    calc = db.query(Calculation).filter(Calculation.id == id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")

    # Update only the fields provided by the user
    if calc_in.a is not None: calc.a = calc_in.a
    if calc_in.b is not None: calc.b = calc_in.b
    if calc_in.type is not None: calc.type = calc_in.type

    # Recompute the result with the new values
    try:
        calc.result = CalculationFactory.compute(calc.a, calc.b, calc.type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) # Catches new division by zero

    db.commit()
    db.refresh(calc)
    return calc

# DELETE
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calculation(id: int, db: Session = Depends(get_db)):
    calc = db.query(Calculation).filter(Calculation.id == id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    db.delete(calc)
    db.commit()