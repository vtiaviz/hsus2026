"""Importação das tabelas oficiais. Todas as funções são idempotentes (upsert pela chave)."""

import csv
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from django.db import transaction

from .models import Cbo, Cid10, DischargeReason, Municipality, SigtapProcedure
from .validators import only_digits


class ImportFormatError(ValueError):
    pass


@dataclass(frozen=True)
class ImportResult:
    total: int


def read_text(path: Path) -> str:
    raw = Path(path).read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    text = read_text(path)
    delimiter = ";" if text.splitlines()[0].count(";") >= text.splitlines()[0].count(",") else ","
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    return [
        {(key or "").strip().upper(): (value or "").strip() for key, value in row.items()}
        for row in reader
    ]


def pick(row: dict[str, str], *columns: str) -> str:
    for column in columns:
        if row.get(column):
            return row[column]
    raise ImportFormatError(f"Coluna obrigatória ausente: uma de {', '.join(columns)}")


def upsert(model, objects: Iterable, update_fields: list[str]) -> ImportResult:
    objects = list(objects)
    pk_name = model._meta.pk.name
    with transaction.atomic():
        model.objects.bulk_create(
            objects,
            batch_size=1000,
            update_conflicts=True,
            unique_fields=[pk_name],
            update_fields=update_fields,
        )
    return ImportResult(total=len(objects))


def import_cid10(path: Path) -> ImportResult:
    """Arquivo CID-10-SUBCATEGORIAS.CSV ou CID-10-CATEGORIAS.CSV do DATASUS."""
    objects = {}
    for row in read_csv_rows(path):
        code = pick(row, "SUBCAT", "CAT").replace(".", "").upper()
        objects[code] = Cid10(code=code, description=pick(row, "DESCRICAO")[:255])
    return upsert(Cid10, objects.values(), ["description"])


def import_cbo(path: Path) -> ImportResult:
    """Arquivo "CBO2002 - Ocupacao.csv" do Ministério do Trabalho."""
    objects = {}
    for row in read_csv_rows(path):
        code = only_digits(pick(row, "CODIGO"))
        objects[code] = Cbo(code=code, title=pick(row, "TITULO")[:255])
    return upsert(Cbo, objects.values(), ["title"])


def import_municipalities(path: Path) -> ImportResult:
    """CSV com colunas CODIGO (IBGE, 7 dígitos), NOME e UF."""
    objects = {}
    for row in read_csv_rows(path):
        code = only_digits(pick(row, "CODIGO", "CODIGO_IBGE"))
        if len(code) != 7:
            raise ImportFormatError(f"Código IBGE deve ter 7 dígitos: {code}")
        objects[code] = Municipality(
            ibge_code=code, name=pick(row, "NOME"), state=pick(row, "UF").upper()
        )
    return upsert(Municipality, objects.values(), ["name", "state"])


def import_discharge_reasons(path: Path) -> ImportResult:
    """CSV com colunas CODIGO, DESCRICAO e TIPO (valores de DischargeReason.Kind)."""
    valid_kinds = set(DischargeReason.Kind.values)
    objects = {}
    for row in read_csv_rows(path):
        kind = pick(row, "TIPO")
        if kind not in valid_kinds:
            raise ImportFormatError(f"Tipo de motivo inválido: {kind}")
        code = only_digits(pick(row, "CODIGO")).zfill(2)
        objects[code] = DischargeReason(code=code, description=pick(row, "DESCRICAO"), kind=kind)
    return upsert(DischargeReason, objects.values(), ["description", "kind"])


# Posições (início, fim, base 1) do layout padrão de tb_procedimento.txt.
SIGTAP_DEFAULT_LAYOUT = {
    "CO_PROCEDIMENTO": (1, 10),
    "NO_PROCEDIMENTO": (11, 260),
    "DT_COMPETENCIA": (331, 336),
}


def read_sigtap_layout(layout_path: Path) -> dict[str, tuple[int, int]]:
    """Lê tb_procedimento_layout.txt (Coluna,Tamanho,Inicio,Fim,Tipo), que vem no zip do SIGTAP."""
    layout = {}
    for row in read_csv_rows(layout_path):
        layout[pick(row, "COLUNA")] = (int(pick(row, "INICIO")), int(pick(row, "FIM")))
    missing = set(SIGTAP_DEFAULT_LAYOUT) - set(layout)
    if missing:
        raise ImportFormatError(f"Layout do SIGTAP sem as colunas: {', '.join(sorted(missing))}")
    return layout


def iter_sigtap_rows(path: Path, layout: dict[str, tuple[int, int]]) -> Iterator[SigtapProcedure]:
    def field(line: str, column: str) -> str:
        start, end = layout[column]
        return line[start - 1 : end].strip()

    for line in read_text(path).splitlines():
        if not line.strip():
            continue
        code = field(line, "CO_PROCEDIMENTO")
        if len(code) != 10 or not code.isdigit():
            raise ImportFormatError(f"Código de procedimento inválido: {code!r}")
        yield SigtapProcedure(
            code=code,
            name=field(line, "NO_PROCEDIMENTO"),
            competence=field(line, "DT_COMPETENCIA"),
        )


def import_sigtap(path: Path) -> ImportResult:
    """Arquivo tb_procedimento.txt do SIGTAP; usa o layout ao lado dele quando existir."""
    path = Path(path)
    layout_path = path.with_name("tb_procedimento_layout.txt")
    layout = read_sigtap_layout(layout_path) if layout_path.exists() else SIGTAP_DEFAULT_LAYOUT
    objects = {procedure.code: procedure for procedure in iter_sigtap_rows(path, layout)}
    return upsert(SigtapProcedure, objects.values(), ["name", "competence"])
