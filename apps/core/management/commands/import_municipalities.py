from apps.core.services import import_municipalities

from ._base import ImportCommand


class Command(ImportCommand):
    help = "Importa municípios do IBGE."
    importer = staticmethod(import_municipalities)
    label = "Municípios"
