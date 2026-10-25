from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import datetime
from database import engine, SessionLocal
from models import Base, Transaction
from schemas import TransactionCreate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Finance Tracker API", version="2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        index_path = os.path.join(os.path.dirname(__file__), "index.html")
        return FileResponse(index_path)
    return {"message": "Finance Tracker Running"}

@app.post("/add")
def add_transaction(data: TransactionCreate):
    db = SessionLocal()
    try:
        date_val = data.date.strip() if data.date and data.date.strip() else datetime.date.today().isoformat()
        new_transaction = Transaction(
            type=data.type.lower().strip(),
            amount=float(data.amount),
            category=(data.category.strip() if data.category else "") or "General",
            date=date_val,
            note=(data.note.strip() if data.note else "")
        )
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)
        return {
            "message": "Transaction Added",
            "transaction": {
                "id": new_transaction.id,
                "type": new_transaction.type,
                "amount": new_transaction.amount,
                "category": new_transaction.category,
                "date": new_transaction.date,
                "note": new_transaction.note
            }
        }
    finally:
        db.close()

@app.get("/transactions")
def get_transactions():
    db = SessionLocal()
    try:
        transactions = db.query(Transaction).order_by(Transaction.id.desc()).all()
        return transactions
    finally:
        db.close()

@app.get("/stats")
def get_stats():
    db = SessionLocal()
    try:
        transactions = db.query(Transaction).all()
        total_income = sum(t.amount for t in transactions if t.type == "income")
        total_expense = sum(t.amount for t in transactions if t.type == "expense")
        balance = total_income - total_expense
        
        cat_expenses = {}
        cat_income = {}
        for t in transactions:
            cat = t.category or "General"
            if t.type == "expense":
                cat_expenses[cat] = cat_expenses.get(cat, 0.0) + t.amount
            elif t.type == "income":
                cat_income[cat] = cat_income.get(cat, 0.0) + t.amount

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "count": len(transactions),
            "expense_by_category": cat_expenses,
            "income_by_category": cat_income
        }
    finally:
        db.close()

@app.delete("/delete/{transaction_id}")
def delete_transaction(transaction_id: int):
    db = SessionLocal()
    try:
        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()

        if not transaction:
            return JSONResponse(status_code=404, content={"error": "Transaction not found"})

        db.delete(transaction)
        db.commit()
        return {"message": "Transaction Deleted"}
    finally:
        db.close()

@app.put("/update/{transaction_id}")
def update_transaction(
    transaction_id: int,
    data: TransactionCreate
):
    db = SessionLocal()
    try:
        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()

        if not transaction:
            return JSONResponse(status_code=404, content={"error": "Transaction not found"})

        transaction.type = data.type.lower().strip()
        transaction.amount = float(data.amount)
        transaction.category = (data.category.strip() if data.category else "") or "General"
        if data.date:
            transaction.date = data.date.strip()
        if data.note is not None:
            transaction.note = data.note.strip()

        db.commit()
        return {"message": "Transaction Updated"}
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "FinPulse API",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@app.get("/app")
@app.get("/index.html")
def serve_frontend():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(index_path)

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    reload = os.environ.get("RELOAD", "false").lower() == "true"
    uvicorn.run("main:app", host=host, port=port, reload=reload)