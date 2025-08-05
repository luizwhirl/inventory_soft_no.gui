# manager.py
# Contém a classe GerenciadorEstoque, que lida com toda a lógica de negócios
# e gerenciamento de dados da aplicação.

import sqlite3
from collections import Counter
from datetime import datetime, time

# Importa as classes de modelo e o gerenciador de banco de dados
from models import (Fornecedor, Localizacao, Produto, HistoricoMovimento,
                    ItemOrdemCompra, OrdemCompra, ItemVenda, Venda,
                    Devolucao, ItemDevolucao, Transacao)
from database import DatabaseManager


#  classe principal de lógica de negócios 

class GerenciadorEstoque:
    """cheguemos na classe principal agora"""
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        # dicionários para armazenar os objetos em memória para acesso rápido
        self.produtos: dict[int, Produto] = {}
        self.fornecedores: dict[int, Fornecedor] = {}
        self.localizacoes: dict[int, Localizacao] = {}
        self.historico: list[HistoricoMovimento] = []
        self.ordens_compra: dict[int, OrdemCompra] = {}
        self.vendas: dict[int, Venda] = {}
        self.devolucoes: dict[int, Devolucao] = {} # dicionário para devoluções

    def get_todas_categorias(self) -> list[str]:
        """Busca no banco de dados e retorna uma lista de todas as categorias de produtos distintas."""
        query = "SELECT DISTINCT categoria FROM produtos WHERE categoria IS NOT NULL AND categoria != '' ORDER BY categoria"
        rows = self.db.execute_query(query, fetch='all')
        return [row[0] for row in rows] if rows else []

    def carregar_dados_do_banco(self):
        """Carrega todos os dados do banco de dados para a memória (dicionários)."""
        print("Carregando dados do banco...")
        # Limpa os dicionários em memória antes de recarregar
        self.produtos.clear()
        self.fornecedores.clear()
        self.localizacoes.clear()
        self.historico.clear()
        self.ordens_compra.clear()
        self.vendas.clear()
        self.devolucoes.clear()

        # carrega fornecedores
        fornecedores_data = self.db.execute_query("SELECT * FROM fornecedores", fetch='all')
        if fornecedores_data:
            for row in fornecedores_data:
                self.fornecedores[row[0]] = Fornecedor(*row)

        # carrega localizações
        localizacoes_data = self.db.execute_query("SELECT * FROM localizacoes", fetch='all')
        if localizacoes_data:
            for row in localizacoes_data:
                self.localizacoes[row[0]] = Localizacao(*row)

        # carrega produtos e associa o fornecedor correspondente
        produtos_data = self.db.execute_query("SELECT * FROM produtos", fetch='all')
        if produtos_data:
            for row in produtos_data:
                prod_id, nome, desc, cat, cod, p_compra, p_venda, p_ress, forn_id = row
                fornecedor_obj = self.fornecedores.get(forn_id)
                if fornecedor_obj:
                    self.produtos[prod_id] = Produto(prod_id, nome, desc, cat, fornecedor_obj, cod, p_compra, p_venda, p_ress)

        # carrega o estoque de cada produto em cada localização
        query_estoque = "SELECT p.id, l.nome, e.quantidade FROM estoque e JOIN produtos p ON e.produto_id = p.id JOIN localizacoes l ON e.localizacao_id = l.id"
        estoque_data = self.db.execute_query(query_estoque, fetch='all')
        if estoque_data:
            for prod_id, local_nome, qtd in estoque_data:
                if prod_id in self.produtos:
                    self.produtos[prod_id].estoque_por_local[local_nome] = qtd

        # carrega o histórico de movimentações
        query_hist = "SELECT produto_id, localizacao_id, tipo, quantidade, data FROM historico_movimentos"
        hist_data = self.db.execute_query(query_hist, fetch='all')
        if hist_data:
            for p_id, l_id, tipo, qtd, data_str in hist_data:
                if (produto := self.produtos.get(p_id)) and (localizacao := self.localizacoes.get(l_id)):
                    self.historico.append(HistoricoMovimento(produto, tipo, qtd, localizacao, datetime.fromisoformat(data_str)))

        # carrega as Ordens de Compra (cabeçalho)
        ocs_data = self.db.execute_query("SELECT * FROM ordens_compra", fetch='all')
        if ocs_data:
            for row in ocs_data:
                oc_id, forn_id, status, data_str = row
                if fornecedor := self.fornecedores.get(forn_id):
                    self.ordens_compra[oc_id] = OrdemCompra(oc_id, fornecedor, [], status, datetime.fromisoformat(data_str))

        # carrega os itens de cada Ordem de Compra
        query_itens_oc = "SELECT ordem_id, produto_id, quantidade, preco_unitario FROM itens_ordem_compra"
        itens_oc_data = self.db.execute_query(query_itens_oc, fetch='all')
        if itens_oc_data:
            for oc_id, p_id, qtd, preco in itens_oc_data:
                if (oc := self.ordens_compra.get(oc_id)) and (produto := self.produtos.get(p_id)):
                    item = ItemOrdemCompra(produto, qtd, preco)
                    oc.itens.append(item)

        # carrega o histórico de Vendas (cabeçalho)
        vendas_data = self.db.execute_query("SELECT id, cliente_nome, data FROM vendas", fetch='all')
        if vendas_data:
            for row in vendas_data:
                venda_id, cliente, data_str = row
                self.vendas[venda_id] = Venda(venda_id, cliente, [], datetime.fromisoformat(data_str))

        # carrega os itens de cada venda
        query_itens_venda = "SELECT venda_id, produto_id, quantidade, preco_venda_unitario FROM itens_venda"
        itens_venda_data = self.db.execute_query(query_itens_venda, fetch='all')
        if itens_venda_data:
            for v_id, p_id, qtd, preco in itens_venda_data:
                if (venda := self.vendas.get(v_id)) and (produto := self.produtos.get(p_id)):
                    item = ItemVenda(produto, qtd, preco)
                    venda.itens.append(item)

        # Carrega as devoluções (cabeçalho)
        devolucoes_data = self.db.execute_query("SELECT id, venda_original_id, cliente_nome, status, data, observacoes FROM devolucoes", fetch='all')
        if devolucoes_data:
            for row in devolucoes_data:
                dev_id, venda_id, cliente, status, data_str, obs = row
                if venda_original := self.vendas.get(venda_id):
                    self.devolucoes[dev_id] = Devolucao(
                        id=dev_id, venda_original=venda_original, cliente_nome=cliente, itens=[],
                        status=status, data=datetime.fromisoformat(data_str), observacoes=obs
                    )

        # Carrega os itens de cada devolução
        itens_dev_data = self.db.execute_query("SELECT devolucao_id, produto_id, quantidade, motivo_devolucao, condicao_produto FROM itens_devolucao", fetch='all')
        if itens_dev_data:
            for dev_id, p_id, qtd, motivo, condicao in itens_dev_data:
                if (devolucao := self.devolucoes.get(dev_id)) and (produto := self.produtos.get(p_id)):
                    devolucao.itens.append(ItemDevolucao(produto, qtd, motivo, condicao))

        # Carrega as transações de cada devolução
        transacoes_data = self.db.execute_query("SELECT id, devolucao_id, tipo, valor, data FROM transacoes", fetch='all')
        if transacoes_data:
            for t_id, dev_id, tipo, valor, data_str in transacoes_data:
                if devolucao := self.devolucoes.get(dev_id):
                    devolucao.transacao = Transacao(t_id, dev_id, tipo, valor, datetime.fromisoformat(data_str))

        print("Dados carregados com sucesso.")

    def registrar_venda(self, itens_info: list[dict], nome_cliente: str, localizacao_id: int) -> tuple[Venda, list[Produto]]:
        """Registra uma nova venda, atualiza o estoque e retorna a venda e produtos que atingiram o ponto de ressuprimento."""
        if not itens_info:
            raise ValueError("A venda deve ter pelo menos um item.")
        if not nome_cliente:
            raise ValueError("O nome do cliente é obrigatório.")
        if not (localizacao := self.localizacoes.get(localizacao_id)):
            raise ValueError("Localização de saída do estoque inválida.")

        # Validação de estoque antes de qualquer alteração no banco
        for item_info in itens_info:
            produto = self.produtos[item_info['produto_id']]
            estoque_local = produto.estoque_por_local.get(localizacao.nome, 0)
            if estoque_local < item_info['quantidade']:
                raise ValueError(f"Estoque insuficiente para '{produto.nome}' na localização '{localizacao.nome}'.")

        agora = datetime.now()
        query_venda = "INSERT INTO vendas (cliente_nome, data) VALUES (?, ?)"
        nova_venda_id = self.db.execute_query(query_venda, (nome_cliente, agora.isoformat()))

        produtos_para_alertar = []
        itens_venda_obj = []
        for item_info in itens_info:
            produto_id = item_info['produto_id']
            quantidade = item_info['quantidade']
            produto = self.produtos[produto_id]
            preco_unitario_venda = produto.preco_venda

            query_item = "INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_venda_unitario) VALUES (?, ?, ?, ?)"
            self.db.execute_query(query_item, (nova_venda_id, produto_id, quantidade, preco_unitario_venda))

            # Movimenta o estoque (saída) e verifica se atingiu o ponto de ressuprimento
            _, produto_alertado = self.movimentar_estoque(
                produto_id=produto_id,
                localizacao_id=localizacao_id,
                quantidade=-quantidade,
                tipo_movimento=f"Venda #{nova_venda_id}"
            )

            if produto_alertado:
                produtos_para_alertar.append(produto_alertado)

            item_obj = ItemVenda(produto, quantidade, preco_unitario_venda)
            itens_venda_obj.append(item_obj)

        # Atualiza o objeto de venda em memória
        nova_venda = Venda(nova_venda_id, nome_cliente, itens_venda_obj, agora)
        self.vendas[nova_venda_id] = nova_venda
        return nova_venda, produtos_para_alertar

    def adicionar_fornecedor(self, **kwargs) -> Fornecedor:
        """Adiciona um novo fornecedor ao banco de dados e à memória."""
        query = "INSERT INTO fornecedores (nome, empresa, telefone, email, morada) VALUES (?, ?, ?, ?, ?)"
        params = (
            kwargs['nome'], kwargs.get('empresa', ''), kwargs.get('telefone', ''),
            kwargs.get('email', ''), kwargs.get('morada', '')
        )
        novo_id = self.db.execute_query(query, params)
        novo_fornecedor = Fornecedor(id=novo_id, **kwargs)
        self.fornecedores[novo_id] = novo_fornecedor
        return novo_fornecedor

    def atualizar_fornecedor(self, fornecedor_id: int, **kwargs) -> bool:
        """Atualiza os dados de um fornecedor existente no banco e na memória."""
        if fornecedor_id not in self.fornecedores: return False
        query = "UPDATE fornecedores SET nome=?, empresa=?, telefone=?, email=?, morada=? WHERE id=?"
        params = (
            kwargs['nome'], kwargs.get('empresa', ''), kwargs.get('telefone', ''),
            kwargs.get('email', ''), kwargs.get('morada', ''), fornecedor_id
        )
        self.db.execute_query(query, params)
        fornecedor = self.fornecedores[fornecedor_id]
        fornecedor.nome, fornecedor.empresa = kwargs['nome'], kwargs.get('empresa', '')
        fornecedor.telefone, fornecedor.email = kwargs.get('telefone', ''), kwargs.get('email', '')
        fornecedor.morada = kwargs.get('morada', '')
        return True

    def remover_fornecedor(self, fornecedor_id: int) -> bool:
        """Remove um fornecedor e todos os produtos associados a ele."""
        if fornecedor_id in self.fornecedores:
            # A remoção em cascata (ON DELETE CASCADE) na tabela 'produtos' cuidará dos produtos no DB.
            self.db.execute_query("DELETE FROM fornecedores WHERE id=?", (fornecedor_id,))
            del self.fornecedores[fornecedor_id]
            # Remove os produtos associados da memória.
            produtos_a_remover = [pid for pid, p in self.produtos.items() if p.fornecedor.id == fornecedor_id]
            for pid in produtos_a_remover:
                del self.produtos[pid]
            return True
        return False

    def adicionar_localizacao(self, **kwargs) -> Localizacao:
        """Adiciona uma nova localização."""
        query = "INSERT INTO localizacoes (nome, endereco) VALUES (?, ?)"
        params = (kwargs['nome'], kwargs.get('endereco', ''))
        try:
            novo_id = self.db.execute_query(query, params)
            nova_localizacao = Localizacao(id=novo_id, **kwargs)
            self.localizacoes[novo_id] = nova_localizacao
            return nova_localizacao
        except sqlite3.IntegrityError:
            # Captura erro de violação de constraint (UNIQUE no nome)
            raise ValueError(f"A localização com o nome '{kwargs['nome']}' já existe.")

    def atualizar_localizacao(self, localizacao_id: int, **kwargs) -> bool:
        """Atualiza os dados de uma localização."""
        if localizacao_id not in self.localizacoes: return False

        local_antiga = self.localizacoes[localizacao_id]
        nome_antigo, novo_nome = local_antiga.nome, kwargs['nome']

        query = "UPDATE localizacoes SET nome=?, endereco=? WHERE id=?"
        params = (novo_nome, kwargs.get('endereco', ''), localizacao_id)
        self.db.execute_query(query, params)

        local_antiga.nome, local_antiga.endereco = novo_nome, kwargs.get('endereco', '')

        # Se o nome mudou, atualiza a chave nos dicionários de estoque em memória.
        if nome_antigo != novo_nome:
            for produto in self.produtos.values():
                if nome_antigo in produto.estoque_por_local:
                    produto.estoque_por_local[novo_nome] = produto.estoque_por_local.pop(nome_antigo)
        return True

    def remover_localizacao(self, localizacao_id: int) -> bool:
        """Remove uma localização, apenas se não houver estoque nela."""
        if localizacao_id in self.localizacoes:
            # Verifica se existe algum produto com quantidade maior que zero nesta localização.
            query = "SELECT 1 FROM estoque WHERE localizacao_id = ? AND quantidade > 0 LIMIT 1"
            if self.db.execute_query(query, (localizacao_id,), fetch='one'):
                raise ValueError("Não é possível remover a localização pois ainda existe estoque nela.")

            self.db.execute_query("DELETE FROM localizacoes WHERE id=?", (localizacao_id,))
            del self.localizacoes[localizacao_id]
            return True
        return False

    def buscar_produto_por_codigo_barras(self, codigo_barras: str) -> Produto | None:
        """Busca um produto em memória pelo seu código de barras."""
        for produto in self.produtos.values():
            if produto.codigo_barras and produto.codigo_barras.strip() == codigo_barras.strip():
                return produto
        return None

    def adicionar_produto(self, fornecedor_id, **kwargs):
        """Adiciona um novo produto."""
        if not (fornecedor := self.fornecedores.get(fornecedor_id)):
            raise ValueError("Fornecedor não encontrado.")

        query = """INSERT INTO produtos (nome, descricao, categoria, codigo_barras, preco_compra, preco_venda, ponto_ressuprimento, fornecedor_id)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (
            kwargs['nome'], kwargs.get('descricao', ''), kwargs.get('categoria', ''),
            kwargs.get('codigo_barras', ''), kwargs['preco_compra'], kwargs['preco_venda'],
            kwargs['ponto_ressuprimento'], fornecedor_id
        )
        novo_id = self.db.execute_query(query, params)
        novo_produto = Produto(id=novo_id, fornecedor=fornecedor, **kwargs)
        self.produtos[novo_id] = novo_produto
        return novo_produto

    def atualizar_produto(self, produto_id, **kwargs):
        """Atualiza os dados de um produto."""
        if produto_id not in self.produtos: return False

        query = """UPDATE produtos SET nome=?, descricao=?, categoria=?, codigo_barras=?,
                                     preco_compra=?, preco_venda=?, ponto_ressuprimento=?, fornecedor_id=?
                                     WHERE id=?"""

        fornecedor_id = int(kwargs.get('fornecedor_id'))
        if not (fornecedor_obj := self.fornecedores.get(fornecedor_id)): return False

        params = (
            kwargs['nome'], kwargs['descricao'], kwargs['categoria'], kwargs['codigo_barras'],
            kwargs['preco_compra'], kwargs['preco_venda'], kwargs['ponto_ressuprimento'],
            fornecedor_id, produto_id
        )
        self.db.execute_query(query, params)

        # Atualiza o objeto em memória
        produto = self.produtos[produto_id]
        kwargs['fornecedor'] = fornecedor_obj
        del kwargs['fornecedor_id']
        for key, value in kwargs.items():
            if hasattr(produto, key):
                setattr(produto, key, value)
        return True

    def remover_produto(self, produto_id):
        """Remove um produto."""
        if produto_id in self.produtos:
            # A remoção em cascata cuidará das tabelas 'estoque', 'historico', etc.
            self.db.execute_query("DELETE FROM produtos WHERE id=?", (produto_id,))
            del self.produtos[produto_id]
            return True
        return False

    def movimentar_estoque(self, produto_id, localizacao_id, quantidade, tipo_movimento):
        """Realiza uma movimentação de estoque (entrada/saída) e a registra no histórico."""
        produto = self.produtos.get(produto_id)
        localizacao = self.localizacoes.get(localizacao_id)
        if not all([produto, localizacao]):
            raise ValueError("Produto ou Localização inválido.")

        estoque_anterior = produto.get_estoque_total()
        estoque_local_anterior = produto.estoque_por_local.get(localizacao.nome, 0)

        # Valida se há estoque suficiente para uma saída
        if quantidade < 0 and estoque_local_anterior < abs(quantidade):
            raise ValueError(f"Estoque insuficiente de '{produto.nome}' em '{localizacao.nome}'.")

        novo_estoque_local = estoque_local_anterior + quantidade
        query_estoque = """
        INSERT INTO estoque (produto_id, localizacao_id, quantidade) VALUES (?, ?, ?)
        ON CONFLICT(produto_id, localizacao_id) DO UPDATE SET quantidade = ?;
        """
        self.db.execute_query(query_estoque, (produto_id, localizacao_id, novo_estoque_local, novo_estoque_local))

        # Registra a movimentação no histórico
        agora = datetime.now()
        query_hist = "INSERT INTO historico_movimentos (produto_id, localizacao_id, tipo, quantidade, data) VALUES (?, ?, ?, ?, ?)"
        # --- ESTA É A LINHA CORRIGIDA ---
        self.db.execute_query(query_hist, (produto_id, localizacao_id, tipo_movimento, quantidade, agora.isoformat()))

        # Atualiza os dados em memória
        produto.estoque_por_local[localizacao.nome] = novo_estoque_local
        self.historico.append(HistoricoMovimento(produto, tipo_movimento, quantidade, localizacao, agora))

        # Verifica se o estoque total do produto caiu abaixo do ponto de ressuprimento.
        produto_para_alertar = None
        if estoque_anterior > produto.ponto_ressuprimento and produto.get_estoque_total() <= produto.ponto_ressuprimento:
            produto_para_alertar = produto

        return True, produto_para_alertar

    def transferir_estoque(self, produto_id: int, origem_id: int, destino_id: int, quantidade: int):
        """Transfere uma quantidade de um produto entre duas localizações."""
        if origem_id == destino_id:
            raise ValueError("A localização de origem e destino não podem ser as mesmas.")
        if quantidade <= 0:
            raise ValueError("A quantidade a transferir deve ser positiva.")

        origem, destino = self.localizacoes.get(origem_id), self.localizacoes.get(destino_id)
        if not all([origem, destino]):
            raise ValueError("Localização de origem ou destino inválida.")

        # Realiza duas movimentações: uma de saída e uma de entrada.
        self.movimentar_estoque(produto_id, origem_id, -quantidade, f"Transferência p/ {destino.nome}")
        self.movimentar_estoque(produto_id, destino_id, quantidade, f"Transferência de {origem.nome}")
        return True

    def criar_ordem_compra(self, fornecedor_id: int, itens_info: list[dict]) -> OrdemCompra:
        """Cria uma nova ordem de compra para um fornecedor."""
        if not (fornecedor := self.fornecedores.get(fornecedor_id)):
            raise ValueError("Fornecedor não encontrado.")
        if not itens_info:
            raise ValueError("A ordem de compra deve ter pelo menos um item.")

        agora = datetime.now()
        query_oc = "INSERT INTO ordens_compra (fornecedor_id, status, data_criacao) VALUES (?, ?, ?)"
        novo_id_oc = self.db.execute_query(query_oc, (fornecedor_id, "Pendente", agora.isoformat()))

        itens_oc_obj = []
        for item_info in itens_info:
            produto_id, quantidade = item_info['produto_id'], item_info['quantidade']
            if not (produto := self.produtos.get(produto_id)):
                raise ValueError(f"Produto com ID {produto_id} não encontrado.")
            if produto.fornecedor.id != fornecedor_id:
                raise ValueError(f"Produto '{produto.nome}' não pertence ao fornecedor '{fornecedor.nome}'.")

            preco_unitario = produto.preco_compra
            query_item = "INSERT INTO itens_ordem_compra (ordem_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)"
            self.db.execute_query(query_item, (novo_id_oc, produto_id, quantidade, preco_unitario))

            item_obj = ItemOrdemCompra(produto, quantidade, preco_unitario)
            itens_oc_obj.append(item_obj)

        nova_ordem = OrdemCompra(novo_id_oc, fornecedor, itens_oc_obj, "Pendente", agora)
        self.ordens_compra[novo_id_oc] = nova_ordem
        return nova_ordem

    def atualizar_status_ordem(self, ordem_id: int, novo_status: str, localizacao_id: int | None = None):
        """Atualiza o status de uma ordem de compra. Se o status for 'Recebida', movimenta o estoque."""
        if not (ordem := self.ordens_compra.get(ordem_id)):
            raise ValueError("Ordem de Compra não encontrada.")

        if novo_status == "Recebida":
            if ordem.status == "Recebida":
                raise ValueError("Esta ordem já foi recebida.")
            if not localizacao_id or not (localizacao := self.localizacoes.get(localizacao_id)):
                raise ValueError("A localização é obrigatória e válida para receber uma ordem.")

            # Para cada item na ordem, registra a entrada no estoque.
            for item in ordem.itens:
                self.movimentar_estoque(
                    produto_id=item.produto.id, localizacao_id=localizacao_id,
                    quantidade=item.quantidade, tipo_movimento=f"Entrada OC #{ordem.id}"
                )

        self.db.execute_query("UPDATE ordens_compra SET status = ? WHERE id = ?", (novo_status, ordem_id))
        ordem.status = novo_status # Atualiza o objeto em memória
        return True

    #region Reports
    def verificar_alertas_ressuprimento(self):
        """Retorna uma lista de produtos cujo estoque total está no ponto de ressuprimento ou abaixo."""
        return [p for p in self.produtos.values() if p.get_estoque_total() <= p.ponto_ressuprimento]

    def calcular_valor_total_estoque(self):
        """Calcula o valor total do inventário com base no preço de compra dos produtos."""
        return sum(p.get_estoque_total() * p.preco_compra for p in self.produtos.values())

    def gerar_relatorio_estoque_simplificado(self):
        """Gera um relatório textual com o status do estoque de todos os produtos."""
        report = f"""RELATÓRIO DE ESTOQUE (SIMPLIFICADO)
Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Valor Total do Estoque: R$ {self.calcular_valor_total_estoque():.2f}
{'='*80}\n\n"""
        for produto in sorted(self.produtos.values(), key=lambda p: p.nome):
            estoque_locais = "\n".join([f"           - {local}: {qtd} unidades" for local, qtd in produto.estoque_por_local.items() if qtd > 0])
            if not estoque_locais:
                estoque_locais = "           - Sem estoque registrado"

            report += f"""ID: {produto.id} - {produto.nome} ({produto.categoria})
  Estoque Total: {produto.get_estoque_total()} unidades
  Ponto de Ressuprimento: {produto.ponto_ressuprimento}
  Estoque por Local:
{estoque_locais}
{'-'*30}\n"""
        return report

    def gerar_relatorio_valor_total(self):
        """Gera um relatório simples com o valor total do inventário."""
        valor_total = self.calcular_valor_total_estoque()
        return f"""RELATÓRIO DE VALOR TOTAL DO INVENTÁRIO
Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
{'='*60}
O valor total do seu inventário (baseado no preço de compra) é: R$ {valor_total:.2f}
"""

    def gerar_relatorio_baixo_estoque(self):
        """Gera um relatório listando todos os produtos com baixo estoque."""
        produtos_baixo_estoque = self.verificar_alertas_ressuprimento()
        report = f"""RELATÓRIO DE PRODUTOS COM BAIXO ESTOQUE
Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
{'='*60}\n
"""
        if not produtos_baixo_estoque:
            return report + "Nenhum produto com baixo estoque no momento."

        for p in produtos_baixo_estoque:
            report += (f"ID: {p.id} - {p.nome}\n"
                       f"    Estoque Atual: {p.get_estoque_total()} | Mínimo Definido: {p.ponto_ressuprimento}\n\n")
        return report

    def gerar_relatorio_mais_vendidos(self):
        """Gera um ranking de produtos mais vendidos."""
        vendas = Counter()
        for v in self.vendas.values():
            for item in v.itens:
                vendas[item.produto.nome] += item.quantidade

        report = f"""RELATÓRIO DE PRODUTOS MAIS VENDIDOS
Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
{'='*60}\n
"""
        if not vendas:
            return report + "Nenhuma venda registrada até o momento."

        for i, (nome_produto, qtd) in enumerate(vendas.most_common(), 1):
            report += f"{i}º. {nome_produto} - {qtd} unidades vendidas\n"

        return report

    def gerar_relatorio_movimentacao_item(self, produto_id: int):
        """Gera um extrato de todas as movimentações de um produto específico."""
        if not (produto := self.produtos.get(produto_id)):
            return "Erro: Produto não encontrado."

        movimentos_produto = [m for m in self.historico if m.produto.id == produto_id]

        report = f"""HISTÓRICO DE MOVIMENTAÇÃO DO PRODUTO: {produto.nome.upper()} (ID: {produto.id})
Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
{'='*70}\n
"""
        if not movimentos_produto:
            return report + "Nenhuma movimentação registrada para este produto."

        for mov in sorted(movimentos_produto, key=lambda m: m.data, reverse=True):
            sinal = '+' if mov.quantidade > 0 else ''
            report += (f"Data: {mov.data.strftime('%d/%m/%Y %H:%M')} | "
                       f"Tipo: {mov.tipo:<25} | "
                       f"Qtd: {sinal}{mov.quantidade:<4} | "
                       f"Local: {mov.localizacao.nome}\n")
        return report

    def gerar_relatorio_vendas_periodo(self, data_inicio: datetime, data_fim: datetime):
        """Gera um relatório detalhado de vendas dentro de um período de datas."""
        vendas_periodo = [v for v in self.vendas.values() if data_inicio <= v.data <= data_fim]

        report = f"""RELATÓRIO DE VENDAS POR PERÍODO
Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}
{'='*70}\n
"""
        if not vendas_periodo:
            return report + "Nenhuma venda registrada no período selecionado."

        total_itens_vendidos, receita_total, lucro_total = 0, 0.0, 0.0

        for venda in sorted(vendas_periodo, key=lambda v: v.data):
            report += f"Venda #{venda.id} | Data: {venda.data.strftime('%d/%m/%Y %H:%M')} | Cliente: {venda.cliente}\n"
            for item in venda.itens:
                lucro_item = item.quantidade * (item.produto.preco_venda - item.produto.preco_compra)
                total_itens_vendidos += item.quantidade
                receita_total += item.subtotal
                lucro_total += lucro_item
                report += f"   - Produto: {item.produto.nome:<25} | Qtd: {item.quantidade}\n"
            report += f"   Subtotal Venda: R$ {venda.valor_total:.2f}\n{'-'*20}\n"

        report += f"\n{'-'*30}\nRESUMO DO PERÍODO\n{'-'*30}\n"
        report += f"Total de Itens Vendidos: {total_itens_vendidos}\n"
        report += f"Receita Bruta Total: R$ {receita_total:.2f}\n"
        report += f"Lucro Bruto Total: R$ {lucro_total:.2f}\n"

        return report
    
    def iniciar_devolucao(self, venda_id: int, itens_devolucao_info: list[dict], observacoes: str) -> Devolucao:
        """Inicia um novo processo de devolução no banco de dados e em memória."""
        if not (venda_original := self.vendas.get(venda_id)):
            raise ValueError("Venda original não encontrada.")
        
        if not itens_devolucao_info:
            raise ValueError("Nenhum item para devolução foi especificado.")

        # Validação: checa se a quantidade devolvida não excede a quantidade vendida
        for item_dev_info in itens_devolucao_info:
            produto_id = item_dev_info['produto_id']
            qtd_devolvida = item_dev_info['quantidade']
            item_vendido = next((item for item in venda_original.itens if item.produto.id == produto_id), None)
            if not item_vendido or qtd_devolvida > item_vendido.quantidade:
                raise ValueError(f"Quantidade de devolução para o produto ID {produto_id} excede a quantidade vendida.")

        agora = datetime.now()
        query_dev = "INSERT INTO devolucoes (venda_original_id, cliente_nome, status, data, observacoes) VALUES (?, ?, ?, ?, ?)"
        novo_id_dev = self.db.execute_query(query_dev, (venda_id, venda_original.cliente, "solicitada", agora.isoformat(), observacoes))

        itens_dev_obj = []
        for item_dev_info in itens_devolucao_info:
            produto = self.produtos[item_dev_info['produto_id']]
            query_item = "INSERT INTO itens_devolucao (devolucao_id, produto_id, quantidade, motivo_devolucao, condicao_produto) VALUES (?, ?, ?, ?, ?)"
            self.db.execute_query(query_item, (novo_id_dev, produto.id, item_dev_info['quantidade'], item_dev_info['motivo'], item_dev_info['condicao']))
            itens_dev_obj.append(ItemDevolucao(produto, item_dev_info['quantidade'], item_dev_info['motivo'], item_dev_info['condicao']))
        
        nova_devolucao = Devolucao(novo_id_dev, venda_original, venda_original.cliente, itens_dev_obj, "solicitada", agora, observacoes)
        self.devolucoes[novo_id_dev] = nova_devolucao
        return nova_devolucao

    def processar_devolucao_e_troca(self, devolucao_id: int, local_retorno_id: int, acao: str, itens_troca_info: list[dict] | None = None) -> tuple[Devolucao, float]:
        """Processa uma devolução, atualizando o estoque e, opcionalmente, gerando uma troca."""
        if not (devolucao := self.devolucoes.get(devolucao_id)):
            raise ValueError("Devolução não encontrada.")
        if devolucao.status != "solicitada":
            raise ValueError(f"A devolução #{devolucao_id} já foi processada. Status atual: {devolucao.status}.")
        if not (local_retorno := self.localizacoes.get(local_retorno_id)):
            raise ValueError("Localização de retorno do estoque inválida.")

        # Passo 1: Retorna os itens devolvidos ao estoque
        for item in devolucao.itens:
            # Usa o método existente de movimentação de estoque para entrada
            self.movimentar_estoque(
                produto_id=item.produto.id,
                localizacao_id=local_retorno_id,
                quantidade=item.quantidade,
                tipo_movimento=f"Devolução #{devolucao.id} - Retorno de Produto"
            )
        
        valor_credito = devolucao.valor_total_devolvido
        valor_troca_paga = 0.0

        # Passo 2: Lida com a ação (reembolso ou troca)
        if acao == 'troca' and itens_troca_info:
            # Processa a nova "venda" da troca, mas sem alterar o estoque temporário
            itens_nova_venda = []
            for item_troca_info in itens_troca_info:
                produto = self.produtos.get(item_troca_info['produto_id'])
                if not produto: raise ValueError(f"Produto de troca com ID {item_troca_info['produto_id']} não encontrado.")
                itens_nova_venda.append({'produto_id': produto.id, 'quantidade': item_troca_info['quantidade']})
            
            # Registra a nova venda da troca e calcula o valor a pagar/creditar
            nova_venda, _ = self.registrar_venda(itens_nova_venda, devolucao.cliente_nome, local_retorno_id)
            devolucao.nova_venda_troca = nova_venda
            
            valor_total_troca = nova_venda.valor_total
            valor_troca_paga = max(0, valor_total_troca - valor_credito)
            tipo_transacao = "pagamento_troca" if valor_troca_paga > 0 else "credito_troca"
            
            valor_final_transacao = valor_troca_paga if valor_troca_paga > 0 else (valor_credito - valor_total_troca)
            
            # Insere a transação no banco
            query_trans = "INSERT INTO transacoes (devolucao_id, tipo, valor, data) VALUES (?, ?, ?, ?)"
            trans_id = self.db.execute_query(query_trans, (devolucao.id, tipo_transacao, valor_final_transacao, datetime.now().isoformat()))
            devolucao.transacao = Transacao(trans_id, devolucao.id, tipo_transacao, valor_final_transacao)

        else: # Ação é 'reembolso'
            query_trans = "INSERT INTO transacoes (devolucao_id, tipo, valor, data) VALUES (?, ?, ?, ?)"
            trans_id = self.db.execute_query(query_trans, (devolucao.id, "reembolso", valor_credito, datetime.now().isoformat()))
            devolucao.transacao = Transacao(trans_id, devolucao.id, "reembolso", valor_credito)

        # Passo 3: Atualiza o status da devolução para 'concluida'
        self.db.execute_query("UPDATE devolucoes SET status = 'concluida' WHERE id = ?", (devolucao.id,))
        devolucao.status = 'concluida'
        
        return devolucao, valor_troca_paga

    def gerar_relatorio_devolucoes_por_motivo(self):
        """gera um relatório de devoluções agrupadas por motivo"""
        report = f"""RELATÓRIO DE DEVOLUÇÕES POR MOTIVO
Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
{'='*70}\n
"""
        motivos = Counter()
        for devolucao in self.devolucoes.values():
            for item in devolucao.itens:
                motivos[item.motivo_devolucao] += item.quantidade
        
        if not motivos:
            return report + "Nenhuma devolução registrada."

        for motivo, qtd in motivos.items():
            report += f"Motivo: {motivo:<30} | Quantidade de Itens: {qtd}\n"
        
        return report
    #endregion