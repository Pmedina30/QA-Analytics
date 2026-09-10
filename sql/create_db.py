"""
create_db.py
============
Crea una base de datos SQLite desde el CSV limpio de evaluaciones QA.

Uso:
    python sql/create_db.py

Genera:
    sql/qa_evaluations.db — Base de datos SQLite lista para queries

Por qué SQLite:
    SQLite no requiere servidor. Es el motor SQL más usado para
    portafolios, demos y análisis local. Las mismas queries SQL
    funcionan en PostgreSQL o SQL Server con mínimos cambios.
"""
import sqlite3
import pandas as pd
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

CLEAN_CSV = ROOT / "Output" / "qa_clean.csv"
DB_PATH   = ROOT / "sql"   / "qa_evaluations.db"

def main():
    print("=" * 55)
    print("  Creating SQLite Database from qa_clean.csv")
    print("=" * 55)

    if not CLEAN_CSV.exists():
        print(f"\n  ❌ Not found: {CLEAN_CSV}")
        print("  Run 'python run_analysis.py' first to generate qa_clean.csv")
        sys.exit(1)

    # Cargar CSV limpio
    df = pd.read_csv(CLEAN_CSV, parse_dates=["Date"])
    print(f"\n  Loaded: {len(df):,} records × {len(df.columns)} columns")

    # Conectar y crear DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Escribir tabla principal
    df.to_sql("evaluations", conn, if_exists="replace", index=False)
    print(f"  Table 'evaluations' created in: {DB_PATH.name}")

    # Crear índices para acelerar queries
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_team     ON evaluations(Team)",
        "CREATE INDEX IF NOT EXISTS idx_agent    ON evaluations(Agent)",
        "CREATE INDEX IF NOT EXISTS idx_process  ON evaluations(Process)",
        "CREATE INDEX IF NOT EXISTS idx_date     ON evaluations(Date)",
        "CREATE INDEX IF NOT EXISTS idx_status   ON evaluations(Status)",
        "CREATE INDEX IF NOT EXISTS idx_valid    ON evaluations(data_valid)",
    ]
    for idx_sql in indexes:
        cursor.execute(idx_sql)
    conn.commit()

    # Verificar
    row_count = cursor.execute(
        "SELECT COUNT(*) FROM evaluations WHERE data_valid=1"
    ).fetchone()[0]
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()

    print(f"\n  Valid records in DB: {row_count:,}")
    print(f"  Tables: {[t[0] for t in tables]}")
    print(f"  Indexes: {len(indexes)} created")

    conn.close()
    print(f"\n  ✅ Database ready: {DB_PATH}")
    print("=" * 55)

if __name__ == "__main__":
    main()
