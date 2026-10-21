from apps.core.services import import_sigtap

from ._base import ImportCommand


class Command(ImportCommand):
    help = "Importa procedimentos do SIGTAP (tb_procedimento.txt)."
    importer = staticmethod(import_sigtap)
    label = "SIGTAP"
