"""Telemetry export — download archived report files."""

import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app import storage

router = APIRouter(prefix="/export", tags=["export"])
security = HTTPBasic()
logger = logging.getLogger(__name__)

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

    # Mirror the report to the archive bucket on every access.
    s3_uri = storage.upload_report(filename)
    logger.info("archived %s to %s", filename, s3_uri)

    return FileResponse(path)
