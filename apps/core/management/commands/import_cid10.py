from apps.core.services import import_cid10

from ._base import ImportCommand


class Command(ImportCommand):
    help = "Importa CID-10 (DATASUS)."
    importer = staticmethod(import_cid10)
    label = "CID-10"
