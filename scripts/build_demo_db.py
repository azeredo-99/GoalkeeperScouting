"""
Gera a base de dados SQLite da demo pública a partir do snapshot CSV.

A demo online não precisa de um PostgreSQL gerido: a API só lê
`gk_performances` uma vez no arranque (ver `db/repository.py`), e são 619
linhas. O snapshot `data/demo/gk_performances.csv` é uma exportação 1:1
da tabela PostgreSQL local (mesmo schema, mesmos valores, NULL continua
NULL -- nunca 0). Este script recria a tabela com o próprio modelo
SQLAlchemy, por isso o schema da demo nunca diverge do de produção.

Uso:
    python scripts/build_demo_db.py [csv] [sqlite]

Depois:
    DATABASE_URL=sqlite:///data/demo/gk_performances.sqlite
"""

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gk_scouting.db.models import Base, GKPerformance  # noqa: E402

DEFAULT_CSV = ROOT / "data" / "demo" / "gk_performances.csv"
DEFAULT_DB = ROOT / "data" / "demo" / "gk_performances.sqlite"


def build(csv_path: Path = DEFAULT_CSV, db_path: Path = DEFAULT_DB) -> int:
    df = pd.read_csv(csv_path)

    expected = [column.name for column in GKPerformance.__table__.columns]
    missing = set(expected) - set(df.columns)
    if missing:
        raise ValueError(f"Snapshot sem colunas do modelo: {sorted(missing)}")

    db_path.unlink(missing_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    # NaN -> NULL: métricas sem eventos ficam em falta, nunca a 0.
    records = df[expected].astype(object).where(df[expected].notna(), None).to_dict("records")
    with engine.begin() as connection:
        connection.execute(GKPerformance.__table__.insert(), records)
    engine.dispose()
    return len(records)


if __name__ == "__main__":
    csv_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    db_arg = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_DB
    rows = build(csv_arg, db_arg)
    print(f"{rows} linhas -> {db_arg}")
