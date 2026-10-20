import pytest

from apps.core.models import Cbo, Cid10, DischargeReason, Municipality, SigtapProcedure
from apps.core.services import (
    ImportFormatError,
    import_cbo,
    import_cid10,
    import_discharge_reasons,
    import_municipalities,
    import_sigtap,
)
from config.settings.base import BASE_DIR

pytestmark = pytest.mark.django_db


def write(tmp_path, name, content, encoding="latin-1"):
    path = tmp_path / name
    path.write_bytes(content.encode(encoding))
    return path


def sigtap_line(code, name, competence="202610"):
    return f"{code}{name:<250}" + " " * 70 + competence


def test_import_cid10_latin1_is_idempotent(tmp_path):
    path = write(
        tmp_path,
        "CID-10-SUBCATEGORIAS.CSV",
        "SUBCAT;CLASSIF;DESCRICAO\nJ189;;Pneumonia não especificada\nA000;;Cólera\n",
    )
    assert import_cid10(path).total == 2
    assert import_cid10(path).total == 2
    assert Cid10.objects.count() == 2
    assert Cid10.objects.get(code="J189").description == "Pneumonia não especificada"


def test_import_cid10_updates_description(tmp_path):
    import_cid10(write(tmp_path, "a.csv", "CAT;DESCRICAO\nJ18;Antiga\n"))
    import_cid10(write(tmp_path, "b.csv", "CAT;DESCRICAO\nJ18;Nova\n", encoding="utf-8"))
    assert Cid10.objects.get(code="J18").description == "Nova"


def test_import_cid10_requires_columns(tmp_path):
    with pytest.raises(ImportFormatError):
        import_cid10(write(tmp_path, "x.csv", "FOO;BAR\n1;2\n"))


def test_import_sigtap_default_layout(tmp_path):
    content = "\n".join([sigtap_line("0303010037", "TRATAMENTO DE OUTRAS DOENCAS BACTERIANAS"), ""])
    path = write(tmp_path, "tb_procedimento.txt", content)
    assert import_sigtap(path).total == 1
    procedure = SigtapProcedure.objects.get()
    assert procedure.code == "0303010037"  # zero à esquerda preservado
    assert procedure.competence == "202610"


def test_import_sigtap_uses_layout_file(tmp_path):
    write(
        tmp_path,
        "tb_procedimento_layout.txt",
        "Coluna,Tamanho,Inicio,Fim,Tipo\n"
        "CO_PROCEDIMENTO,10,1,10,VARCHAR2\n"
        "NO_PROCEDIMENTO,20,11,30,VARCHAR2\n"
        "DT_COMPETENCIA,6,31,36,CHAR\n",
    )
    path = write(tmp_path, "tb_procedimento.txt", f"0301010072{'CONSULTA MEDICA':<20}202609\n")
    import_sigtap(path)
    assert SigtapProcedure.objects.get().name == "CONSULTA MEDICA"


def test_import_sigtap_rejects_invalid_layout_and_code(tmp_path):
    write(tmp_path, "tb_procedimento_layout.txt", "Coluna,Tamanho,Inicio,Fim,Tipo\nX,1,1,1,C\n")
    with pytest.raises(ImportFormatError):
        import_sigtap(write(tmp_path, "tb_procedimento.txt", "x"))
    other = tmp_path / "outro"
    other.mkdir()
    with pytest.raises(ImportFormatError):
        import_sigtap(write(other, "tb_procedimento.txt", sigtap_line("ABC", "X")))


def test_import_cbo(tmp_path):
    import_cbo(
        write(tmp_path, "cbo.csv", "CODIGO;TITULO\n225125;Médico clínico\n223505;Enfermeiro\n")
    )
    assert Cbo.objects.count() == 2


def test_import_municipalities_validates_code(tmp_path):
    import_municipalities(
        write(tmp_path, "m.csv", "codigo,nome,uf\n1501758,Brejo Grande do Araguaia,pa\n")
    )
    assert Municipality.objects.get().state == "PA"
    with pytest.raises(ImportFormatError):
        import_municipalities(write(tmp_path, "n.csv", "codigo;nome;uf\n150175;Brejo;PA\n"))


def test_import_discharge_reasons_from_repository_file():
    result = import_discharge_reasons(BASE_DIR / "data" / "motivos_saida_sih.csv")
    assert result.total == DischargeReason.objects.count() == 26
    assert DischargeReason.objects.get(code="21").kind == DischargeReason.Kind.STAY


def test_import_discharge_reasons_rejects_unknown_kind(tmp_path):
    with pytest.raises(ImportFormatError):
        import_discharge_reasons(write(tmp_path, "d.csv", "codigo;descricao;tipo\n12;Alta;foo\n"))
