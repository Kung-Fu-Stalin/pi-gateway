import json
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from api.auth import require_admin, decode_token
from api.config import settings
from api.models import UIUser

router = APIRouter(tags=["logs"])

logger = logging.getLogger(__name__)


def parse_log_line(line: str) -> dict | None:
    parts = line.strip().split()
    if len(parts) < 10:
        return None
    try:
        return {
            "timestamp": datetime.fromtimestamp(float(parts[0]), tz=timezone.utc).isoformat(),
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
    page: int = Query(1, ge=1),
    user: UIUser = Depends(require_admin),
):
    log_path = Path(settings.squid_log)
    if not log_path.exists():
        return {"total": 0, "items": [], "page": page, "limit": limit}

    # Читаем построчно чтобы не грузить всё в память
    lines = []
    with open(log_path, "r") as f:
        for line in f:
            entry = parse_log_line(line)
            if entry:
                lines.append(entry)

    lines.reverse()
    offset = (page - 1) * limit

    return {
        "total": len(lines),
        "items": lines[offset: offset + limit],
        "page": page,
        "limit": limit,
    }


@router.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
        msg = json.loads(raw)
    except asyncio.TimeoutError:
        await websocket.close(code=4001)
        return
    except Exception:
        await websocket.close(code=4001)
        return

    if msg.get("type") != "auth" or not msg.get("token"):
        await websocket.close(code=4001)
        return

    try:
        payload = decode_token(msg["token"])
        if payload.get("role") != "admin":
            await websocket.close(code=4003)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    log_path = Path(settings.squid_log)
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
    except Exception as e:
        logger.error("WebSocket logs error: %s", e)
