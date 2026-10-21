# Dados de referência

| Arquivo | Origem | Comando |
| --- | --- | --- |
| `motivos_saida_sih.csv` | Tabela de motivos de saída/permanência do SIH/SUS | `python manage.py import_discharge_reasons data/motivos_saida_sih.csv` |
| `municipios_ibge.csv` | 5.571 municípios com código IBGE de 7 dígitos, gerado a partir de [kelvins/municipios-brasileiros](https://github.com/kelvins/municipios-brasileiros) (dados do IBGE) | `python manage.py import_municipalities data/municipios_ibge.csv` |

**A conferir:** a lista foi montada a partir do template antigo (`evolucao_medica.html`), corrigindo
códigos duplicados (41 e 24/25) e trocando "10 - Transferência" por 31. Confira contra a tabela
oficial do SIH antes de usar em produção.

As tabelas oficiais grandes não ficam no repositório; baixe-as da fonte e importe:

| Tabela | Arquivo | Comando |
| --- | --- | --- |
| CID-10 | `CID-10-SUBCATEGORIAS.CSV` (DATASUS) | `import_cid10` |
| SIGTAP | `tb_procedimento.txt` do zip da competência (com `tb_procedimento_layout.txt` ao lado) | `import_sigtap` |
| CBO | `CBO2002 - Ocupacao.csv` | `import_cbo` |
