"""Definição de classes utilizadas no projeto"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

CategoriasInsumo = Literal[
    "Material Elétrico", "Material de Limpeza", "Material de Pintura",
    "Material de Pedreiro", "Material de Gesso", "Serviços Terceiros",
    "Logística/Transporte", "Material de Proteção",
    "Material de Bombeiro/Hidraulico", "Argamassa", "Outros"
]

CategoriasComprovante = Literal[
    "NF VENDA", "NF SERVIÇO", "RECIBO", "ORÇAMENTO", "Outros"
]

class SQLGerado(BaseModel):

    sql: str = Field(
        description="Consulta SQL PostgreSQL somente leitura."
    )

    explicacao: str = Field(
        description="Breve explicação da estratégia utilizada."
    )

    tabelas_utilizadas: List[str] = Field(
        description="Lista das tabelas utilizadas."
    )

class ItemNotaFiscal(BaseModel):
    codigo: Optional[str] = Field(None, description="Código identificador do produto ou serviço na nota")
    descricao: str = Field(..., description="Descrição literal do produto ou serviço")
    unidade: str = Field(..., description="Descrição ou código da unidade utilizada para o produto ou serviço")
    quantidade: float = Field(..., description="Quantidade adquirida")
    valor_unitario: float = Field(..., description="Valor unitário do item")
    valor_total: float = Field(..., description="Valor total declarado do item")

class NotaFiscal(BaseModel):
    numero_documento: str = Field(..., description="Número identificador da nota, cupom ou recibo (Ex: 270, 000.093.238)")
    emitente_nome: str = Field(..., description="Razão Social ou Nome do fornecedor emissor")
    emitente_cnpj_cpf: Optional[str] = Field(None, description="CNPJ ou CPF do emitente")
    remetente_nome: str = Field(..., description="Razão Social ou Nome do remetente ou destinatário")
    remetente_cnpj_cpf: Optional[str] = Field(None, description="CNPJ ou CPF do remetente ou destinatário")
    data_emissao: str = Field(..., description="Data de emissão (Formato DD/MM/AAAA)")
    valor_total_nota: float = Field(..., description="Valor total bruto documentado no comprovante")
    chave_acesso: Optional[str] = Field(None, description="Chave eletrônica de acesso com 44 dígitos (NF-e/NFS-e)")
    categoria_comprovante: CategoriasComprovante = Field(
        ...,
        description="Classificação automática baseada no tipo de comprovante seja NOTA FISCAL DE VENDA DE MERCADO, NOTA FISCAL DE SERVIÇO ou simples RECIBO"
    )
    itens: List[ItemNotaFiscal] = Field(default=[], description="Lista detalhada dos insumos e produtos extraídos de dentro desta nota")

class ItemQuadroResumo(BaseModel):
    numero_nf: str = Field(..., description="Número ou identificação da NF lançado na linha da tabela resumo")
    data: str = Field(..., description="Data da despesa lançada na tabela no formato DD/MM/YYYY")
    emitente: str = Field(..., description="Nome abreviado do emitente lançado na tabela")
    aplicacao_material: str = Field(..., description="Descrição da aplicação do material ou motivo do gasto")
    valor: float = Field(..., description="Valor total atribuído a este item no quadro resumo")
    categoria_insumo: CategoriasInsumo = Field(
        ...,
        description="Classificação automática baseada na aplicação do material"
    )

class QuadroResumo(BaseModel):
    numero_relatorio: str = Field(..., description="Identificação do documento de prestação de contas (Ex: Nº 08, Nº 10)")
    nome_cliente: str = Field(..., description="Nome do cliente final destinatário")
    endereco: str = Field(..., description="Endereço da obra ou residência descrita")
    data_envio: str = Field(..., description="Data de envio da prestação de contas no formato DD/MM/YYYY")
    nome_relatorio : str = Field(..., description="Nome/caminho do arquivo que está sendo processado")

    # Totais consolidados declarados no rodapé do quadro resumo
    valor_total_materiais: float = Field(..., description="Somatório do valor dos materiais no rodapé")
    valor_administracao_material: float = Field(..., description="Taxa de administração contratual referentes a aquisição de materiais (Adm 15%)")
    valor_administracao_servico: float = Field(..., description="Taxa de administração contratual referentes a serviços de terceiros (15%)")
    des_administracao_servico: str = Field(..., description="Concatenação das descrições referentes a taxa de administração contratual de serviços de terceiros (15%)")
    total_a_pagar: float = Field(..., description="Total líquido final faturado ao cliente")

    # Matrizes de dados coletadas
    itens_quadro_resumo: List[ItemQuadroResumo] = Field(..., description="Todas as linhas processadas da tabela de resumo principal")
    lista_notas_fiscais: List[NotaFiscal] = Field(..., description="Todas iamgens de notas fiscais ou recibos processadas da tabela de notas fiscais")
