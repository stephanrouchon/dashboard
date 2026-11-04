import csv
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from django.conf import settings

DATA_FILE = Path(settings.BASE_DIR) / "data" / "ecritures.txt"

_cache = {"mtime": None, "rows": []}


@dataclass(frozen=True, slots=True)
class Ecriture:
    journal: str
    journal_libelle: str
    date: date
    compte: str
    intitule: str
    auxiliaire: str
    piece: str
    libelle: str
    debit: Decimal
    credit: Decimal
    plan: str
    poste: str


def _decimal(value):
    return Decimal(value.replace(",", ".").replace(" ", "") or "0")


def _read(path):
    # Export comptable Windows : cp1252, séparateur ";"
    with open(path, encoding="cp1252", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)
        for r in reader:
            if len(r) < 12:
                continue
            yield Ecriture(
                journal=r[0].strip("[]"),
                journal_libelle=r[1],
                date=datetime.strptime(r[2], "%d/%m/%Y").date(),
                compte=r[3],
                intitule=r[4],
                auxiliaire=r[5],
                piece=r[7],
                libelle=r[9],
                debit=_decimal(r[10]),
                credit=_decimal(r[11]),
                plan=r[13] if len(r) > 13 else "",
                poste=r[14] if len(r) > 14 else "",
            )


def charger_ecritures():
    """Retourne les écritures, rechargées si le fichier a changé."""
    mtime = DATA_FILE.stat().st_mtime
    if _cache["mtime"] != mtime:
        _cache["rows"] = list(_read(DATA_FILE))
        _cache["mtime"] = mtime
    return _cache["rows"]
