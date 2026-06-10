"""
Utilidades compartidas para cargar resultados de módulos en PostGIS.
"""
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def get_engine():
    url = (
        f"postgresql+psycopg://{os.environ['DB_USER']}:{os.environ['DB_PASS']}"
        f"@{os.environ.get('DB_HOST', 'localhost')}:{os.environ.get('DB_PORT', '5432')}"
        f"/{os.environ['DB_NAME']}"
    )
    return create_engine(url)


def load_to_postgis(df: pd.DataFrame, table: str, schema: str = "analysis",
                    if_exists: str = "replace") -> None:
    """Carga un DataFrame en PostGIS. Usa CASCADE al reemplazar para no fallar con vistas dependientes."""
    engine = get_engine()
    if if_exists == "replace":
        with engine.connect() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS {schema}."{table}" CASCADE'))
            conn.commit()
        if_exists = "fail"
    df.to_sql(table, engine, schema=schema, if_exists=if_exists, index=False)
    print(f"  ✓ {schema}.{table}  ({len(df)} filas cargadas)")
