# app/qr_store.py
from __future__ import annotations
import sqlite3
import uuid
import json
import time
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional


DB_PATH = Path(__file__).resolve().parent.parent / "storage" / "qr_sessions.sqlite3"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            doc_type TEXT NOT NULL,
            title TEXT,
            fecha TEXT,
            commitments_json TEXT,
            participant_areas_json TEXT,
            short_code TEXT,
            created_at REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS qr_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT NOT NULL,
            area TEXT,
            nombre TEXT,
            email TEXT,
            conforme TEXT,
            created_at REAL
        )
    """)
    conn.commit()
    conn.close()

def create_meeting(doc_type: str, title: str, fecha: str, commitments: List[Dict], participant_areas: List[str]) -> str:
    meeting_id = uuid.uuid4().hex[:10]
    short_code = f"{secrets.randbelow(1_000_000):06d}"
    conn = _connect()
    conn.execute(
        "INSERT INTO meetings (id, doc_type, title, fecha, commitments_json, participant_areas_json, short_code, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (meeting_id, doc_type, title, fecha, json.dumps(commitments), json.dumps(participant_areas), short_code, time.time()),
    )
    conn.commit()
    conn.close()
    return meeting_id


def get_meeting_by_code(short_code: str) -> Optional[str]:
    """Devuelve el meeting_id correspondiente a un codigo corto, o None."""
    conn = _connect()
    row = conn.execute(
        "SELECT id FROM meetings WHERE short_code=? ORDER BY created_at DESC LIMIT 1",
        (short_code,),
    ).fetchone()
    conn.close()
    return row["id"] if row else None


def get_meeting(meeting_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    row = conn.execute("SELECT * FROM meetings WHERE id=?", (meeting_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "doc_type": row["doc_type"],
        "title": row["title"],
        "fecha": row["fecha"],
        "commitments": json.loads(row["commitments_json"] or "[]"),
        "participant_areas": json.loads(row["participant_areas_json"] or "[]"),
        "short_code": row["short_code"],
    }

def update_meeting_commitments(meeting_id: str, commitments: List[Dict], participant_areas: List[str] = None) -> bool:
    conn = _connect()
    if participant_areas is not None:
        conn.execute(
            "UPDATE meetings SET commitments_json=?, participant_areas_json=? WHERE id=?",
            (json.dumps(commitments), json.dumps(participant_areas), meeting_id),
        )
    else:
        conn.execute(
            "UPDATE meetings SET commitments_json=? WHERE id=?",
            (json.dumps(commitments), meeting_id),
        )
    conn.commit()
    updated = conn.total_changes > 0
    conn.close()
    return updated


def add_qr_participant(meeting_id: str, area: str, nombre: str, email: str, conforme: str):
    conn = _connect()
    conn.execute(
        "INSERT INTO qr_participants (meeting_id, area, nombre, email, conforme, created_at) VALUES (?,?,?,?,?,?)",
        (meeting_id, area, nombre, email, conforme, time.time()),
    )
    conn.commit()
    conn.close()


def list_qr_participants(meeting_id: str) -> List[Dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        "SELECT area, nombre, email, conforme, created_at FROM qr_participants WHERE meeting_id=? ORDER BY created_at",
        (meeting_id,),
    ).fetchall()
    conn.close()
    return [{"area": r["area"], "nombre": r["nombre"], "email": r["email"], "conforme": r["conforme"]} for r in rows]

def delete_meeting(meeting_id: str) -> None:
    """Invalida una reunion (y sus registros QR) una vez generado el PDF final."""
    conn = _connect()
    conn.execute("DELETE FROM qr_participants WHERE meeting_id=?", (meeting_id,))
    conn.execute("DELETE FROM meetings WHERE id=?", (meeting_id,))
    conn.commit()
    conn.close()