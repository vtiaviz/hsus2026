from apps.core.services import import_discharge_reasons

from ._base import ImportCommand


class Command(ImportCommand):
    help = "Importa motivos de saída e permanência do SIH."
    importer = staticmethod(import_discharge_reasons)
    label = "Motivos de saída"
