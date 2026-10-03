"""Processamento extratção dos dados dos relatórios PDF  funções auxiliares """

import os
import re
import unicodedata
from pathlib import Path
from dateutil import parser
from thefuzz import fuzz
from google import genai
from google.genai import types
import json

from .config import EXTRACT_LLM_MODEL, SQL_LLM_MODEL
from .config import CHAVE_API_GEMINI
from .models import QuadroResumo


def normalizar_texto(texto):
  """Remove espaços extras, pontuações, acentos e converte para minúsculas para limpeza básica."""
  if not texto:
    return ""

  texto_processado = str(texto).lower()

  # Remove acentos
  texto_processado = unicodedata.normalize('NFKD', texto_processado).encode('ascii', 'ignore').decode('utf-8')

  # Remove pontuação (mantém apenas letras, números e espaços)
  texto_processado = re.sub(r'[^À-ſ a-zA-Z0-9]', '', texto_processado)

  # Normaliza e remove espaços extras
  texto_processado = re.sub(r'\s+', ' ', texto_processado).strip()

  if texto_processado.isdigit():
    # 2. Remove os zeros à esquerda
    texto_processado = texto_processado.lstrip('0')

    # Se o texto era "000", lstrip remove tudo. Tratamos isso para retornar "0".
    if texto_processado == "":
        texto_processado = "0"

  return texto_processado

def converter_para_ymd(data_texto):
    # Dicionário simples para traduzir meses em português (caso venha por extenso)
    meses_pt = {
        "janeiro": "jan", "fevereiro": "feb", "março": "mar", "abril": "apr",
        "maio": "may", "junho": "jun", "julho": "jul", "agosto": "aug",
        "setembro": "sep", "outubro": "oct", "novembro": "nov", "dezembro": "dec"
    }

    # Prepara o texto: deixa em minúsculo e remove conectores como "de" (ex: 06 de abril)
    data_limpa = str(data_texto).lower().replace(" de ", " ")

    # Traduz o mês para o parser inglês entender se necessário
    for pt, en in meses_pt.items():
        if pt in data_limpa:
            data_limpa = data_limpa.replace(pt, en)
            break

    try:
        # O parser descobre o formato sozinho.
        # dayfirst=True garante que formatos como 06/04 sejam lidos como 6 de Abril (padrão BR), e não 4 de Junho (padrão EUA)
        objeto_data = parser.parse(data_limpa, dayfirst=True)

        # Retorna no formato final exato que você pediu: YYYY-MM-DD
        return objeto_data.strftime("%Y-%m-%d")

    except Exception as e:
        return f"Erro: Não foi possível identificar o formato da data '{data_texto}'"

def carregar_arquivos(pasta):
  """  pasta = Path(pasta)

    if not pasta.exists():
        print("❌ A pasta não existe.")
        return []

    if not pasta.is_dir():
        print("❌ O caminho informado não é uma pasta.")
        return []

    arquivos = list(pasta.glob("*.pdf"))"""
  # 1. Diretório atual do Colab
  os.chdir('/content/')
  diretorio = "."

  print(f"📁 Pasta: {diretorio}")

  # 1. Listar arquivos que começam com 'N' ou 'n' e terminam com '.pdf'
  arquivos_pdf = [
    f
    for f in os.listdir(diretorio)
    if (f.startswith("N") or f.startswith("n")) and f.lower().endswith(".pdf")
  ]
  print(f"📄 Arquivos encontrados: {len(arquivos_pdf)}")

  for arq in arquivos_pdf:
    print(f"   - {arq}")

  return

def extrair_dados_comprovantes_pdf(pdf_path: str):
    """
    Realiza o envio do PDF para a API oficial do Gemini, processa o layout visualmente,
    injeta classificação Zero-Shot e retorna um dicionário estritamente tipado.
    """
    # Inicializa o cliente Gemini 
    client = genai.Client(api_key=CHAVE_API_GEMINI)
    print(f"\n-> {EXTRACT_LLM_MODEL} para extração dos dados do relatorio PDF (processamento multimodal nativo) ...")

    try :
     
     pdf = client.files.upload(file=pdf_path)

    except Exception as e:
        print(f"Erro ao realizar o upload do arquivo para a API: {e}")
        return

    prompt_passo_1 = """
    Atue como um especialista em extração de dados de despesas de obras civis.
    Analise o documento PDF fornecido por completo e preencha o esquema JSON estruturado anexado.
    O documento contém uma tabela resumo de pedidos, seguidos de imagens de comprovantes de despesas que podem ser:
    notas fiscais, recibos, orçamentos, comprovantes de transferências, comprovantes de pix, etc.

    INSTRUÇÕES ESPECÍFICAS DE MAPEAMENTO:
    1. Primeiras Páginas: Capture os dados cadastrais (Cliente, Endereço, Número do Relatório e Data de Envio) e processe cada linha do Quadro Resumo.
    2. Números e Valores: Remova formatações de moeda brasileiras ('R$', pontos de milhar) e converta campos de preço para números decimais do tipo float (Ex: '78,80' vira 78.80 / '1.871,50' vira 1871.50).
    3. Para o número do relatório, considere apenas o valor numérico, sem o texto.
    5. Para número de nf, recibo, ou número do documento, não usar separador de cadas decimais ou zeros a esquerda. Casoo númeo não seja informado, não exista, usar SN.
    6. As informações sobre data estão em vários formatos, extrair no formato "DD/MM/YYYY" em todos os níveis de dados.
    7. A informação correspondente a "Adm (15%)" deve ser preenchida no campo valor_administracao_material da classe QuadroResumo.
    8. No quadro resumo, caso haja uma ou mais descrições que se referem a 15% de administração de contratos de
    terceiros ou de alguma outra atividade que não seja aquisição de material,proceder da seguinte forma: extrair os valores que sucedem a descrição e consolidar a soma destes valores no campo valor_administracao_servico da classe QuadroResumo.
    As descrições identificadas devem ser concantenadas no campo des_administracao_servico da classe QuadroResumo, colocando-se um espaço em branco entre elas.


    REGRAS DE CLASSIFICAÇÃO ZERO-SHOT para o campo 'categoria_insumo'):
        Analise detidamente a 'Aplicacao do Material' de cada item do quadro resumo e atribua uma das seguintes categorias:
         'Material Elétrico', 'Material de Limpeza', 'Material de Pintura', 'Material de Pedreiro',
         'Serviços Terceiros', 'Logística / Transporte',
         'Material de Proteção', 'Material de Gesso', 'Material de Bombeiro/Hidraulico','Argamassa'.
          Caso não encontre, utilizar "Outros"

    9. Quando a data de emissão ou data despesa não for definida, utilizar a data do relatório
    10. Processar imagens de notas fiscais ou recibos coletando as informações do número da nota fiscal ou recibo, cnpj ou cpf e nome do emitente, valor total da nota ou recibo,
    número de itens, cnpj ou cpf do destiantário, nome ou razão social do destinatário, data de emissão da nota ou recibo e chave de acesso, quando houver.
    11. Processar também os itens da nota fiscal, recibos, etc: código do produto, descrição, unidade utilizada, quantidade, valor unitário e valor total.
    12. Extrair dados sem fazer calculos."""

    #print("-> Enviando lote para análise cognitiva ", EXTRACT_LLM_MODEL, "...")
    response = client.models.generate_content(
        model=EXTRACT_LLM_MODEL,
        contents=[pdf, prompt_passo_1],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QuadroResumo  # Garante estruturação de esquema assistida por tipo
           
        ),
    )


    # Descarte programático do arquivo em nuvem pós-leitura por conformidade de privacidade
    client.files.delete(name=pdf.name)

    return json.loads(response.text)
