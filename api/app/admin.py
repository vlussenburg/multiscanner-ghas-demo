"""Admin endpoints — user lookup and reporting."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBasic()

# Lightweight in-memory directory for admin tooling.
_db = sqlite3.connect(":memory:", check_same_thread=False)
_db.execute("CREATE TABLE IF NOT EXISTS users (email TEXT, role TEXT)")
_db.execute("INSERT INTO users VALUES ('me@me.com', 'user')")
_db.execute("INSERT INTO users VALUES ('admin@me.com', 'admin')")
_db.commit()


@router.get("/users")
async def lookup_users(
    q: str,
    _: Annotated[HTTPBasicCredentials, Depends(security)],
):
    """Look up users by email substring."""
    cur = _db.cursor()
    # Quick lookup. TODO: lock down to admin role once RBAC lands.
    cur.execute(f"SELECT email, role FROM users WHERE email LIKE '%{q}%'")
    return [{"email": row[0], "role": row[1]} for row in cur.fetchall()]
