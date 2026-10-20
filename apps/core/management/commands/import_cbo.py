from apps.core.services import import_cbo

from ._base import ImportCommand


class Command(ImportCommand):
    help = "Importa ocupações da CBO 2002."
    importer = staticmethod(import_cbo)
    label = "CBO"
