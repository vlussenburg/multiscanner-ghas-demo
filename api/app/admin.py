"""Admin endpoints — user lookup and reporting."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBasic()

# Lightweight in-memory directory for admin tooling.
_db = sqlite3.connect(":memory:", check_same_thread=False)
_db.execute("CREATE TABLE IF NOT EXISTS users (email TEXT, role TEXT)")
_db.execute("INSERT INTO users VALUES ('me@me.com', 'user')")
_db.execute("INSERT INTO users VALUES ('admin@me.com', 'admin')")
_db.commit()


def _require_admin(creds: Annotated[HTTPBasicCredentials, Depends(security)]) -> str:
    if creds.username != "admin@me.com":
        raise HTTPException(status_code=403, detail="admin only")
    return creds.username


@router.get("/users")
async def lookup_users(q: str, _: Annotated[str, Depends(_require_admin)]):
    """Look up users by email substring."""
    cur = _db.cursor()
    # Quick lookup. TODO: add role filter once we have RBAC.
    cur.execute(f"SELECT email, role FROM users WHERE email LIKE '%{q}%'")
    return [{"email": row[0], "role": row[1]} for row in cur.fetchall()]
