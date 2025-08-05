# models.py
# contém as definições de todas as classes de dados (dataclasses) da aplicação.
from __future__ import annotations # Permite referenciar a própria classe em type hints
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime

#  Classes de Dados (Models) 

# region Data Classes

@dataclass
class Fornecedor:
    """dados de contato de um fornecedor"""
    id: int
    nome: str
    empresa: str
    telefone: str
    email: str
    morada: str

    def __str__(self):
        """isso vai ser usado para exibir o fornecedor em uma lista"""
        return f"{self.id} - {self.nome} ({self.empresa})"

@dataclass
class Localizacao:
    # repsresenta uma localização física no inventário, como um armazém ou uma loja mesmo
    id: int
    nome: str
    endereco: str = ""

    def __str__(self):
        #aquela mesma parada lá, de exibir a localização em uma lista
        return f"{self.id} - {self.nome}"

@dataclass
class Produto:
    """produto no inventário."""
    id: int
    nome: str
    descricao: str
    categoria: str
    fornecedor: Fornecedor
    codigo_barras: str
    preco_compra: float
    preco_venda: float
    ponto_ressuprimento: int # o ponto de ressuprimento é o estoque mínimo que deve ser mantido
    # aqui vamos usar um defaultdict para armazenar a quantidade do produto por nome de localização
    estoque_por_local: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))

    def get_estoque_total(self) -> int:
        """faz o calculo e retorna a soma do estoque de todas as localizações"""
        return sum(self.estoque_por_local.values())

    def __str__(self):
        """representação em string para listas e seleções"""
        return f"{self.id} - {self.nome} (Estoque Total: {self.get_estoque_total()})"


@dataclass
class HistoricoMovimento:
    """aqui, nós registramos as movimentações de estoque de um produto"""
    produto: Produto
    tipo: str # exemplo: entrada, saída, transferência
    quantidade: int
    localizacao: Localizacao
    data: datetime = field(default_factory=datetime.now)

@dataclass
class ItemOrdemCompra:
    """nisso, nós vamos representar um item dentro de uma ordem de Compra"""
    # ou seja, um produto que está sendo comprado através do fornecedor
    produto: Produto
    quantidade: int
    preco_unitario: float

    @property
    def subtotal(self) -> float:
        """calculo do valro subtotal do item da ordem de compra"""
        return self.quantidade * self.preco_unitario

@dataclass
class OrdemCompra:
    """aqui, nós ja temoos a nossa tal ordem de compra kkkkk ai meu deus eu tô ficando louco"""
    id: int
    fornecedor: Fornecedor
    itens: list[ItemOrdemCompra]
    status: str # : pendente, recebida, cancelada
    data_criacao: datetime = field(default_factory=datetime.now)

    @property
    def valor_total(self) -> float:
        """calcolo do valor total da ordem de compra"""
        return sum(item.subtotal for item in self.itens)

    def __str__(self):
        """Representação em string para listas e seleções."""
        # Usando ,.2f para formatar o número com separador de milhar e duas casas decimais
        valor_formatado = f"R$ {self.valor_total:,.2f}"
        data_formatada = self.data_criacao.strftime('%d/%m/%Y')
        return (f"OC #{self.id} | {data_formatada} | "
                f"Fornecedor: {self.fornecedor.empresa} | "
                f"{valor_formatado} | Status: {self.status}")

@dataclass
class ItemVenda:
    produto: Produto
    quantidade: int
    preco_venda_unitario: float

    @property
    def subtotal(self) -> float:
        return self.quantidade * self.preco_venda_unitario

@dataclass
class Venda:
    id: int
    cliente: str
    itens: list[ItemVenda]
    data: datetime = field(default_factory=datetime.now)

    @property
    def valor_total(self) -> float:
        return sum(item.subtotal for item in self.itens)
    
    def __str__(self):
        """pra deixar mais bonitinho"""
        valor_formatado = f"R$ {self.valor_total:,.2f}"
        data_formatada = self.data.strftime('%d/%m/%Y')
        return f"Venda #{self.id} | Data: {data_formatada} | Cliente: {self.cliente} | Valor: {valor_formatado}"

@dataclass
class ItemDevolucao:
    """representa um produto específico dentro de um processo de devolução"""
    produto: Produto
    quantidade: int
    motivo_devolucao: str
    condicao_produto: str # tipo um "novo", "com defeito", "danificado"

    @property
    def subtotal(self) -> float:
        """vai caclcular o valor do item devolvido (que é baseado no preço de venda da compra original)"""
        return self.quantidade * self.produto.preco_venda

@dataclass
class Transacao:
    """representa o movimento financeiro associado a uma devolução oi troca"""
    id: int
    devolucao_id: int
    tipo: str # "reembolso", "credito", "pagamento_troca"
    valor: float
    data: datetime = field(default_factory=datetime.now)

@dataclass
class Devolucao:
    """representa o processo geral de devolução ou troca"""
    id: int
    venda_original: Venda
    cliente_nome: str
    itens: list[ItemDevolucao]
    status: str # solicitada, em analise, aprovada, concluida
    data: datetime = field(default_factory=datetime.now)
    observacoes: str = ""
    transacao: Transacao | None = None
    nova_venda_troca: Venda | None = None

    @property
    def valor_total_devolvido(self) -> float:
        return sum(item.subtotal for item in self.itens)

    def __str__(self):
        valor_formatado = f"R$ {self.valor_total_devolvido:,.2f}"
        data_formatada = self.data.strftime('%d/%m/%Y')
        return (f"Devolução #{self.id} | {data_formatada} | "
                f"Venda Orig.: #{self.venda_original.id} | Cliente: {self.cliente_nome} | "
                f"Status: {self.status}")

#endregion