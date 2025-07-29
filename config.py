# config.py
# contém as variáveis de configuração e constantes do projeto.

import sys

# --- Constantes de Configuração ---

DB_FILE = "estoque_database.db"

# --- Verificação de Dependências Opcionais ---

# nisso aqui vamos tentar import o ReportLab, se não der certo, vamos deixar a variável REPORTLAB_DISPONIVEL como False
# só pra nao dar erro se caso a gente nao tiver ele instalado
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    REPORTLAB_DISPONIVEL = True
except ImportError:
    # se caso o ReportLab não esteja instalado, define a flag como False
    # o programa vai rodar normal, só vai desabilitar a opção de salvar pdf (sim, temos uma)
    REPORTLAB_DISPONIVEL = False