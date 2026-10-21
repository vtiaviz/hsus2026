from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("patients", "0002_initial")]

    operations = [UnaccentExtension()]
