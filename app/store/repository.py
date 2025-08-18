# app/store/repository.py
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass
from pydantic import EmailStr
from pydantic_br import CPF
from app.store.db import Database
from app.models.schemas import PaymentStatus

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS users (
        cpf VARCHAR(11) PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS payments (
        txid TEXT PRIMARY KEY,
        user_cpf VARCHAR(11) REFERENCES users(cpf) ON DELETE NO ACTION,
        amount INTEGER NOT NULL,
        status TEXT NOT NULL,
        pixCopiaECola TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )"""
]

@dataclass
class User:
    # password
    # agency: Optional[str] = None
    # account: Optional[str] = None
    # ispb: Optional[str] = None
    cpf: CPF
    email: EmailStr
    name: str

@dataclass
class Payment:
    txid: str
    user_cpf: CPF
    amount: int
    status: PaymentStatus
    pixCopiaECola: str

class Repository:
    def __init__(self, db: Database, auto_create: bool = True):
        self.db = db
        self.db.connect()
        if auto_create:
            self.ensure_schema()

    def ensure_schema(self) -> None:
        for sql in SCHEMA:
            self.db.execute(sql)

    def get_or_create_user(self, cpf: CPF, email: EmailStr, name: str) -> User:
        row = self.db.query_one("SELECT cpf, email, name FROM users WHERE cpf=%s", (cpf,))
        if row:
            return User(cpf=row[0], email=row[1], name=row[2])
        row = self.db.query_one("INSERT INTO users(cpf, email, name) VALUES (%s, %s, %s) RETURNING cpf", (cpf, email, name))
        return User(cpf=cpf, email=email, name=name)

    def create_payment(self, txid: str, user_cpf: CPF, amount: int, pixCopiaECola: str) -> Payment:
        status = PaymentStatus.ACTIVE.value
        self.db.execute(
            "INSERT INTO payments(txid, user_cpf, amount, status, pixCopiaECola) VALUES (%s, %s, %s, %s, %s)",
            (txid, user_cpf, amount, status, pixCopiaECola),
        )
        return Payment(txid=txid, user_cpf=user_cpf, amount=amount, status=PaymentStatus.ACTIVE, pixCopiaECola=pixCopiaECola)

    def get_payment(self, txid: str) -> Optional[Payment]:
        row = self.db.query_one("SELECT txid, user_cpf, amount, status, pixCopiaECola FROM payments WHERE txid=%s", (txid,))
        if not row:
            return None
        return Payment(txid=row[0], user_cpf=row[1], amount=row[2], status=PaymentStatus(row[3]), pixCopiaECola=row[4])

    def set_status(self, txid: str, status: PaymentStatus) -> Optional[Payment]:
        self.db.execute("UPDATE payments SET status=%s, updated_at=CURRENT_TIMESTAMP WHERE txid=%s", (status.value, txid))
        return self.get_payment(txid)
