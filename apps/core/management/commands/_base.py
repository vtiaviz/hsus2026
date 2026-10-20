from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.core.services import ImportFormatError


class ImportCommand(BaseCommand):
    """Base dos comandos import_*: recebe o caminho do arquivo e chama `importer`."""

    importer = None
    label = ""

    def add_arguments(self, parser):
        parser.add_argument("path", type=Path, help="Caminho do arquivo oficial")

    def handle(self, *args, path: Path, **options):
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        try:
            result = type(self).importer(path)
        except ImportFormatError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(f"{self.label}: {result.total} registros importados."))
