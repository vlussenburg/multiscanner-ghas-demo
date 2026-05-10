"""Telemetry export — download archived report files."""

import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

router = APIRouter(prefix="/export", tags=["export"])
security = HTTPBasic()

REPORTS_DIR = "reports"


@router.get("/{filename}")
async def download_report(
    filename: str,
    _: Annotated[HTTPBasicCredentials, Depends(security)],
):
    """Download a previously generated telemetry report by filename."""
    path = os.path.join(REPORTS_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="report not found")
    return FileResponse(path)
