from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.all_models import TaskDB, TransactionDB
from ..schemas.all_schemas import TaskCreate, TransactionCreate

router = APIRouter()

# --- TASKS ---
@router.get("/tasks")
def read_tasks(db: Session = Depends(get_db)):
    return db.query(TaskDB).all()

@router.post("/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = TaskDB(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

# --- FINANCE ---
@router.get("/finance")
def read_finance(db: Session = Depends(get_db)):
    return db.query(TransactionDB).all()

@router.post("/finance")
def create_transaction(tx: TransactionCreate, db: Session = Depends(get_db)):
    db_tx = TransactionDB(**tx.dict())
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx

# --- STATS ---
@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    tasks = db.query(TaskDB).all()
    txs = db.query(TransactionDB).all()
    
    tasks_completed = len([t for t in tasks if t.status == "COMPLETE"])
    active_projects = len([t for t in tasks if t.status == "RUNNING"])
    total_expenses = sum([t.amount for t in txs if t.amount < 0])
    score = int((tasks_completed / len(tasks) * 100)) if tasks else 0
    
    return {
        "tasks_completed": tasks_completed,
        "active_projects": active_projects,
        "total_expenses": round(abs(total_expenses), 2),
        "productivity_score": f"{score}%"
    }
