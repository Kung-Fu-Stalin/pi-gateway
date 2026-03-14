import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin, get_current_user
from api.database import get_db
from api.models import UIUser

router = APIRouter(tags=["logs"])

SQUID_LOG = "/var/log/squid/access.log"


def parse_log_line(line: str) -> dict | None:
    parts = line.strip().split()
    if len(parts) < 10:
        return None
    try:
        return {
            "timestamp": datetime.fromtimestamp(float(parts[0])).isoformat(),
            "duration": int(parts[1]),
            "client": parts[2],
            "result": parts[3],
            "bytes": int(parts[4]),
            "method": parts[5],
            "url": parts[6],
            "user": parts[7] if parts[7] != "-" else None,
            "hierarchy": parts[8],
            "type": parts[9],
        }
    except (ValueError, IndexError):
        return None


@router.get("/api/logs")
async def get_logs(
    limit: int = Query(50, le=500),
    page: int = Query(1),
    user: UIUser = Depends(require_admin),
):
    log_path = Path(SQUID_LOG)
    if not log_path.exists():
        return {"total": 0, "items": []}

    lines = log_path.read_text().splitlines()
    lines.reverse()

    parsed = []
    for line in lines:
        entry = parse_log_line(line)
        if entry:
            parsed.append(entry)

    offset = (page - 1) * limit

    return {
        "total": len(parsed),
        "items": parsed[offset: offset + limit],
    }


@router.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    await websocket.accept()
    log_path = Path(SQUID_LOG)

    if not log_path.exists():
        await websocket.close(code=1008)
        return

    try:
        with open(log_path, "r") as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    entry = parse_log_line(line)
                    if entry:
                        await websocket.send_json(entry)
                else:
                    await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass