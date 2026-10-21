from django.db import migrations

# Os sete exames do template consult.html. O admin cadastra os demais.
EXAM_TYPES = [
    "Hemograma",
    "Glicemia",
    "Ureia",
    "Creatinina",
    "Colesterol",
    "Raio-X de Tórax",
    "ECG",
]


def create_exam_types(apps, schema_editor):
    exam_type = apps.get_model("clinical", "ExamType")
    for name in EXAM_TYPES:
        exam_type.objects.get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies = [("clinical", "0002_initial")]

    operations = [migrations.RunPython(create_exam_types, migrations.RunPython.noop)]
