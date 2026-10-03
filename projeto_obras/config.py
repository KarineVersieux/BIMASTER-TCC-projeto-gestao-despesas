"""Configuração central do projeto usando variáveis de ambiente (.env)."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Raiz do projeto (um nível acima de projeto_obras/)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Carrega o arquivo .env, se existir.
load_dotenv(ENV_FILE, override=True)

# -----------------------------------------------------------------------------
# Credenciais
# -----------------------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_DB_URI = os.getenv("SUPABASE_DB_URI")
CHAVE_API_GEMINI = os.getenv("CHAVE_API_GEMINI")

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT", "6543"),
}

# -----------------------------------------------------------------------------
# Modelos
# -----------------------------------------------------------------------------
# Modelo LLM usado para geração de consulta SQL 
SQL_LLM_MODEL = os.getenv("SQL_LLM_MODEL", "gemini-3.5-flash-lite")
# Modelo LLM usado para extração de dados dos relatorios PDF 
EXTRACT_LLM_MODEL = os.getenv("EXTRACT_LLM_MODEL", "gemini-3.5-flash-lite")

# -----------------------------------------------------------------------------
# Regras de negócio usadas na geração de SQL para a consulta a base de dados 
# relacional
# -----------------------------------------------------------------------------
REGRAS_NEGOCIO_CONSULTA = """
REGRAS DO SISTEMA DE PRESTAÇÃO DE CONTAS DE DESPESAS COM OBRAS

1. A tabela "Relatório" contém a consolidação de despesas por período, incluindo
   materiais, administração de materiais e administração de serviços.
   O total a pagar corresponde à soma desses componentes.
2. Quando o usuário se referenciar ao período do relatório, utilizar o campo dta_envio.
3. A tabela "Despesa" contém cada lançamento de despesa de um relatório.
   des_categoria representa categorias fixas e des_aplicacao descreve a aplicação.
   O status pode ser PENDENTE ou CONCILIADO.
4. A tabela "Comprovante Despesa" contém notas fiscais, recibos, orçamentos e
   comprovantes que podem comprovar despesas. Um comprovante pode ser enviado em
   relatório posterior.
5. Os itens dos comprovantes representam materiais/insumos utilizados na obra.
6. Ao quantificar material ou insumo, informar também a unidade.
7. Para cálculos financeiros ou de quantidade, utilizar SUM quando apropriado.
8. Nome emitente refere-se aos fornecedores.
9. Nome remetente refere-se ao cliente.
10. Regras para geração SQL:
   - PostgreSQL (Supabase).
   - Somente SELECT ou WITH.
   - Utilizar somente tabelas e colunas existentes no catálogo.
   - Não inventar nomes.
   - Respeitar os relacionamentos FK.
   - Nunca executar INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE,
     GRANT ou REVOKE.
   - Nome da tabela entre aspas duplas e precedido pelo esquema.
   - Sempre utilizar id_contrato como critério de segurança dos dados, normalmente
     por meio de junção com a tabela CONTRATO.
"""

EXEMPLOS_CONSULTA = """
Pergunta: Quais são os relatórios enviados no mês de junho de 2026?
SQL: SELECT id_relatorio, num_relatorio, nome_relatorio, dta_envio, total_a_pagar
FROM public."Relatório"
WHERE dta_envio >= '2026-06-01' AND dta_envio <= '2026-06-30'

Pergunta: Quais são as despesas pendentes de comprovação?
SQL: SELECT id_despesa, numero_nf_recibo, dta_despesa, nome_emitente, vlr_despesa,
     des_aplicacao, des_categoria, cod_status_comprovacao
FROM public."Despesa"
WHERE cod_status_comprovacao ILIKE 'PENDENTE'

Pergunta: Qual é o total de despesa por fornecedor por ano e mês?
SQL: SELECT EXTRACT(YEAR FROM dta_despesa) AS ano,
            EXTRACT(MONTH FROM dta_despesa) AS mes,
            nome_emitente,
            SUM(vlr_despesa) AS total_despesa
FROM public."Despesa"
GROUP BY ano, mes, nome_emitente

Pergunta: Informe o total de despesas por tipo de comprovante por ano e mês.
SQL: SELECT EXTRACT(YEAR FROM dta_emissao) AS ano,
            EXTRACT(MONTH FROM dta_emissao) AS mes,
            categoria_comprovante,
            SUM(valor_total) AS total_despesa
FROM public."Comprovante Despesa"
GROUP BY ano, mes, categoria_comprovante
ORDER BY 1, 2
"""


def validar_configuracao():
    """Verifica se as principais credenciais foram carregadas sem exibi-las."""
    obrigatorias = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "SUPABASE_DB_URI": SUPABASE_DB_URI,
        "CHAVE_API_GEMINI": CHAVE_API_GEMINI,
        "DB_USER": DB_CONFIG["user"],
        "DB_PASSWORD": DB_CONFIG["password"],
        "DB_HOST": DB_CONFIG["host"],
    }
    ausentes = [nome for nome, valor in obrigatorias.items() if not valor]
    if ausentes:
        raise RuntimeError(
            "Variáveis de ambiente não configuradas: " + ", ".join(ausentes)
        )
    return True
