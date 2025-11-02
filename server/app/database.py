import aiosqlite
from datetime import datetime
from pathlib import Path
import os

DB_PATH = "files.db"

async def init_db():
    """Initialize the database and create tables if they don't exist"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS csv_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL,
                is_selected INTEGER DEFAULT 0,
                file_path TEXT NOT NULL UNIQUE
            )
        """)
        await db.commit()


async def add_csv_file(filename: str, file_size: int, file_path: str):
    """Add a new CSV file record to the database"""
    uploaded_at = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO csv_files (filename, file_size, uploaded_at, is_selected, file_path)
            VALUES (?, ?, ?, ?, ?)
        """, (filename, file_size, uploaded_at, 0, file_path))
        await db.commit()
        result = await db.execute("SELECT last_insert_rowid()")
        row = await result.fetchone()
        return row[0]


async def get_all_files():
    """Get all CSV files from the database"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT id, filename, file_size, uploaded_at, is_selected, file_path
            FROM csv_files
            ORDER BY uploaded_at DESC
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def update_file_selection(file_id: int, is_selected: bool):
    """Update the selection status of a file"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE csv_files
            SET is_selected = ?
            WHERE id = ?
        """, (1 if is_selected else 0, file_id))
        await db.commit()


async def delete_file(file_id: int):
    """Delete a file record and the actual file"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Get file path before deleting
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT file_path FROM csv_files WHERE id = ?", (file_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                file_path = row["file_path"]
                # Delete the actual file
                if os.path.exists(file_path):
                    os.remove(file_path)
                # Delete the database record
                await db.execute("DELETE FROM csv_files WHERE id = ?", (file_id,))
                await db.commit()
                return True
            return False

