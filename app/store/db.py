# app/store/db.py
from __future__ import annotations
import psycopg
from typing import Any, Optional, Tuple, List


class Database: # TODO: improve error messages
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection: Optional[psycopg.Connection] = None

    def connect(self) -> None:
        if not self.connection or self.connection.closed:
            self.connection = psycopg.connect(self.database_url, autocommit=True)

    def execute(self, query: str, params: Optional[Tuple] = None) -> None:
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)

    def query_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Tuple[Any, ...]]:
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    def query_all(self, query: str, params: Optional[Tuple] = None) -> List[Tuple[Any, ...]]:
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def close(self) -> None:
        if self.connection:
            self.connection.close()

