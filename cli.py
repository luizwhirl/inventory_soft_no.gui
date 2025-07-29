# cli.py
# Contém a classe CliApp, responsável por toda a construção e gerenciamento
# da interface de linha de comando (CLI)
# É tipo uma GUI, só que ruim
# daí vem o nome "peba" do repositório

import os
from datetime import datetime, time

from manager import GerenciadorEstoque
from models import Produto, Localizacao, OrdemCompra # Para type hints e checagens de instância
from config import REPORTLAB_DISPONIVEL # Flag para saber se pode gerar PDF

# Condicional para importar o ReportLab apenas se disponível.
if REPORTLAB_DISPONIVEL:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch

# --- Classe da Interface de Linha de Comando ---

class CliApp:
    """Gerencia toda a interface de linha de comando."""

    def __init__(self, gerenciador: GerenciadorEstoque):
        self.gerenciador = gerenciador
        # O dicionário 'self.barcode_buffer' simula a espera pelo Enter do scanner
        self.barcode_buffer = ""

    # --- Funções Auxiliares de UI ---
    def _limpar_tela(self):
        """Limpa o console."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _esperar_enter(self):
        """Pausa a execução até o usuário pressionar Enter."""
        input("\nPressione Enter para continuar...")

    def _imprimir_cabecalho(self, titulo: str):
        """Imprime um cabeçalho formatado."""
        self._limpar_tela()
        print("=" * (len(titulo) + 4))
        print(f"| {titulo} |")
        print("=" * (len(titulo) + 4))
        print()

    def _obter_input(self, prompt: str, obrigatorio=True, tipo='str') -> str | int | float | None:
        """Pede um input ao usuário com validação."""
        while True:
            valor = input(prompt).strip()
            if not valor and obrigatorio:
                print("Erro: Este campo é obrigatório.")
                continue
            if not valor and not obrigatorio:
                return None

            if tipo == 'int':
                try:
                    return int(valor)
                except ValueError:
                    print("Erro: Por favor, insira um número inteiro válido.")
            elif tipo == 'float':
                try:
                    # Permite usar tanto ponto quanto vírgula como separador decimal.
                    return float(valor.replace(',', '.'))
                except ValueError:
                    print("Erro: Por favor, insira um número válido (ex: 12.34).")
            else: # str
                return valor

    def _selecionar_em_lista(self, titulo: str, dicionario: dict, contexto_produto: Produto | None = None, prompt_personalizado: str | None = None) -> int | None:
        """
        Exibe uma lista de itens de um dicionário e pede para o usuário selecionar um pelo ID.
        Se um 'contexto_produto' for fornecido e a lista for de Localizações, exibe o estoque
        desse produto em cada localização.
        """
        print(f"\n--- {titulo} ---")
        if not dicionario:
            print("Nenhum item disponível.")
            return None

        # Itera sobre os valores do dicionário, ordenados pelo ID.
        for item_obj in sorted(dicionario.values(), key=lambda item: item.id):
            # Verifica se o item é uma Localização e se temos um produto como contexto
            if isinstance(item_obj, Localizacao) and contexto_produto:
                estoque_no_local = contexto_produto.estoque_por_local.get(item_obj.nome, 0)
                print(f"{item_obj.id} - {item_obj.nome} ({estoque_no_local} un.)")
            else:
                # Comportamento padrão para Produtos e outros objetos
                print(str(item_obj))

        while True:
            prompt = prompt_personalizado if prompt_personalizado is not None else "Digite o ID do item desejado (ou 0 para cancelar): "
            id_selecionado = self._obter_input(prompt, tipo='int')
            if id_selecionado == 0:
                return None
            if id_selecionado in dicionario:
                return id_selecionado
            print("ID inválido. Tente novamente.")

    # --- Funções de Menu ---
    def run(self):
        """Inicia o loop principal da aplicação CLI."""
        while True:
            self._imprimir_cabecalho("Sistema de Gerenciamento de Estoque")

            # Dashboard rápido
            alertas = self.gerenciador.verificar_alertas_ressuprimento()
            print(f"Itens Únicos: {len(self.gerenciador.produtos)}")
            print(f"Valor Total do Estoque: R$ {self.gerenciador.calcular_valor_total_estoque():,.2f}")
            if alertas:
                print(f"\nATENÇÃO: Existem {len(alertas)} produtos com baixo estoque!")

            print("\n--- MENU PRINCIPAL ---")
            print("1. Gerenciar Produtos")
            print("2. Gerenciar Fornecedores")
            print("3. Gerenciar Localizações e Transferências")
            print("4. Registrar Venda")
            print("5. Gerenciar Ordens de Compra")
            print("6. Gerar Relatórios")
            print("7. Sair")

            escolha = self._obter_input("\nEscolha uma opção: ")

            if escolha == '1': self._menu_produtos()
            elif escolha == '2': self._menu_fornecedores()
            elif escolha == '3': self._menu_localizacoes_transferencias()
            elif escolha == '4': self._registrar_venda()
            elif escolha == '5': self._menu_ordens_compra()
            elif escolha == '6': self._menu_relatorios()
            elif escolha == '7':
                print("Saindo do sistema...")
                break
            else:
                print("Opção inválida!")
                self._esperar_enter()

    def _menu_produtos(self):
        """Exibe o submenu para gerenciamento de produtos."""
        while True:
            self._imprimir_cabecalho("Gerenciar Produtos")
            print("1. Listar todos os produtos")
            print("2. Adicionar novo produto")
            print("3. Atualizar produto existente")
            print("4. Remover produto")
            print("5. Buscar produto por Código de Barras")
            print("6. Registrar Entrada Manual de Estoque")
            print("0. Voltar ao Menu Principal")

            escolha = self._obter_input("\nEscolha uma opção: ")

            if escolha == '1': self._listar_produtos()
            elif escolha == '2': self._adicionar_produto()
            elif escolha == '3': self._atualizar_produto()
            elif escolha == '4': self._remover_produto()
            elif escolha == '5': self._buscar_por_barcode()
            elif escolha == '6': self._registrar_entrada_manual()
            elif escolha == '0': break
            else: print("Opção inválida!")
            self._esperar_enter()

    def _menu_fornecedores(self):
        """Exibe o submenu para gerenciamento de fornecedores."""
        while True:
            self._imprimir_cabecalho("Gerenciar Fornecedores")
            print("1. Listar todos os fornecedores")
            print("2. Adicionar novo fornecedor")
            print("3. Atualizar fornecedor existente")
            print("4. Remover fornecedor")
            print("0. Voltar ao Menu Principal")

            escolha = self._obter_input("\nEscolha uma opção: ")

            if escolha == '1': self._listar_fornecedores()
            elif escolha == '2': self._adicionar_fornecedor()
            elif escolha == '3': self._atualizar_fornecedor()
            elif escolha == '4': self._remover_fornecedor()
            elif escolha == '0': break
            else: print("Opção inválida!")
            self._esperar_enter()

    def _menu_localizacoes_transferencias(self):
        """Exibe o submenu para gerenciamento de localizações e transferências."""
        while True:
            self._imprimir_cabecalho("Gerenciar Localizações e Transferências")
            print("1. Listar todas as localizações")
            print("2. Adicionar nova localização")
            print("3. Atualizar localização existente")
            print("4. Remover localização")
            print("5. Realizar Transferência de Estoque")
            print("0. Voltar ao Menu Principal")

            escolha = self._obter_input("\nEscolha uma opção: ")

            if escolha == '1': self._listar_localizacoes()
            elif escolha == '2': self._adicionar_localizacao()
            elif escolha == '3': self._atualizar_localizacao()
            elif escolha == '4': self._remover_localizacao()
            elif escolha == '5': self._realizar_transferencia()
            elif escolha == '0': break
            else: print("Opção inválida!")
            self._esperar_enter()

    def _menu_ordens_compra(self):
        """Exibe o submenu para gerenciamento de Ordens de Compra."""
        while True:
            self._imprimir_cabecalho("Gerenciar Ordens de Compra (OC)")
            print("1. Listar todas as OCs")
            print("2. Criar nova OC")
            print("3. Atualizar status de uma OC")
            print("4. Visualizar/Salvar recibo de uma OC")
            print("0. Voltar ao Menu Principal")

            escolha = self._obter_input("\nEscolha uma opção: ")

            if escolha == '1': self._listar_ocs()
            elif escolha == '2': self._criar_oc()
            elif escolha == '3': self._atualizar_status_oc()
            elif escolha == '4': self._visualizar_salvar_oc()
            elif escolha == '0': break
            else: print("Opção inválida!")
            self._esperar_enter()

    def _menu_relatorios(self):
        """Exibe o submenu para geração de relatórios."""
        while True:
            self._imprimir_cabecalho("Gerar Relatórios")
            tipos = [
                "Inventário Completo (Simplificado)", "Valor Total do Inventário",
                "Produtos com Baixo Estoque", "Produtos Mais Vendidos",
                "Histórico de Movimentação por Item", "Relatório de Vendas por Período"
            ]
            for i, tipo in enumerate(tipos, 1):
                print(f"{i}. {tipo}")
            print("0. Voltar")

            escolha = self._obter_input("\nEscolha o tipo de relatório: ", tipo='int')
            if escolha == 0: break
            if 1 <= escolha <= len(tipos):
                self._gerar_relatorio_detalhado(tipos[escolha - 1])
                self._esperar_enter()
            else:
                print("Opção inválida!")
                self._esperar_enter()

    # --- Implementação das Ações ---

    # Produtos
    def _listar_produtos(self):
        """Exibe uma lista detalhada de todos os produtos cadastrados."""
        self._imprimir_cabecalho("Lista de Produtos")
        produtos = self.gerenciador.produtos
        if not produtos:
            print("Nenhum produto cadastrado.")
            return

        separador = "-" * 40
        for p in sorted(produtos.values(), key=lambda x: x.id):
            print(separador)
            print(f"ID: {p.id}")
            print(f"Nome: {p.nome}")
            print(f"Categoria: {p.categoria}")
            print(f"Fornecedor: {p.fornecedor.nome} ({p.fornecedor.empresa})")
            print(f"Preço Venda: R$ {p.preco_venda:,.2f}")
            print(f"Estoque Total: {p.get_estoque_total()} unidades")

            print("Estoque por Local:")
            # Usamos .items() para pegar tanto a chave (local) quanto o valor (quantidade)
            estoque_local_items = p.estoque_por_local.items()
            # Verificamos se há algum local com estoque maior que zero
            if any(qtd > 0 for _, qtd in estoque_local_items):
                for loc, qtd in estoque_local_items:
                    if qtd > 0:
                        print(f"   - {loc}: {qtd} unidades")
            else:
                print("   - Nenhum estoque registrado.")
        print(separador)

    def _adicionar_produto(self):
        """Guia o usuário no processo de adicionar um novo produto."""
        self._imprimir_cabecalho("Adicionar Novo Produto")
        try:
            nome = self._obter_input("Nome (deixe em branco para cancelar): ", obrigatorio=False)
            if not nome:
                print("\nAdição cancelada.")
                return

            descricao = self._obter_input("Descrição: ")

            print("\nCategorias existentes:", ", ".join(self.gerenciador.get_todas_categorias()))
            categoria = self._obter_input("Categoria (pode ser uma nova): ")

            fornecedor_id = self._selecionar_em_lista("Selecione o Fornecedor", self.gerenciador.fornecedores)
            if fornecedor_id is None:
                print("\nAdição cancelada.")
                return

            codigo_barras = self._obter_input("Código de Barras: ", obrigatorio=False)
            preco_compra = self._obter_input("Preço de Compra: ", tipo='float')
            preco_venda = self._obter_input("Preço de Venda: ", tipo='float')
            ponto_ressuprimento = self._obter_input("Ponto de Ressuprimento (estoque mínimo): ", tipo='int')

            novo_produto = self.gerenciador.adicionar_produto(
                fornecedor_id=fornecedor_id, nome=nome, descricao=descricao, categoria=categoria,
                codigo_barras=codigo_barras or "N/A", preco_compra=preco_compra, preco_venda=preco_venda,
                ponto_ressuprimento=ponto_ressuprimento
            )
            print(f"\nProduto '{novo_produto.nome}' adicionado com sucesso!")

            # Pergunta se deseja adicionar um estoque inicial para o novo produto.
            qtd_inicial = self._obter_input("Deseja adicionar uma quantidade inicial? (Digite a qtd ou 0 para pular): ", tipo='int')
            if qtd_inicial and qtd_inicial > 0:
                local_id = self._selecionar_em_lista(
                    "Selecione a Localização para a entrada inicial",
                    self.gerenciador.localizacoes,
                    contexto_produto=novo_produto
                )
                if local_id:
                    self.gerenciador.movimentar_estoque(novo_produto.id, local_id, qtd_inicial, "Carga Inicial")
                    print(f"{qtd_inicial} unidades adicionadas ao estoque.")

        except Exception as e:
            print(f"\nErro ao adicionar produto: {e}")

    def _atualizar_produto(self):
        """Guia o usuário na atualização de um produto existente."""
        self._imprimir_cabecalho("Atualizar Produto")
        produto_id = self._selecionar_em_lista("Selecione o produto para atualizar", self.gerenciador.produtos)
        if produto_id is None: return

        try:
            p = self.gerenciador.produtos[produto_id]
            print("\nDeixe em branco para manter o valor atual.")

            nome = self._obter_input(f"Nome [{p.nome}]: ", obrigatorio=False) or p.nome
            descricao = self._obter_input(f"Descrição [{p.descricao}]: ", obrigatorio=False) or p.descricao
            categoria = self._obter_input(f"Categoria [{p.categoria}]: ", obrigatorio=False) or p.categoria

            fornecedor_id = self._selecionar_em_lista(
                "Selecione o novo fornecedor (ou 0 para manter)",
                self.gerenciador.fornecedores,
                prompt_personalizado="Digite o ID do item desejado: " # tava passando sufoco sem esse prompt aqui
            ) or p.fornecedor.id 

            codigo_barras = self._obter_input(f"Cód. Barras [{p.codigo_barras}]: ", obrigatorio=False) or p.codigo_barras
            preco_compra = self._obter_input(f"Preço Compra [R${p.preco_compra:.2f}]: ", obrigatorio=False, tipo='float') or p.preco_compra
            preco_venda = self._obter_input(f"Preço Venda [R${p.preco_venda:.2f}]: ", obrigatorio=False, tipo='float') or p.preco_venda
            ponto_ressuprimento = self._obter_input(f"Ponto Ressupr. [{p.ponto_ressuprimento}]: ", obrigatorio=False, tipo='int') or p.ponto_ressuprimento

            dados = {
                'nome': nome, 'descricao': descricao, 'categoria': categoria, 'codigo_barras': codigo_barras,
                'preco_compra': preco_compra, 'preco_venda': preco_venda, 'ponto_ressuprimento': ponto_ressuprimento,
                'fornecedor_id': fornecedor_id
            }
            self.gerenciador.atualizar_produto(produto_id, **dados)
            print("\nProduto atualizado com sucesso!")

        except Exception as e:
            print(f"\nErro ao atualizar produto: {e}")

    def _remover_produto(self):
        """Guia o usuário na remoção de um produto."""
        self._imprimir_cabecalho("Remover Produto")
        produto_id = self._selecionar_em_lista("Selecione o produto para remover", self.gerenciador.produtos)
        if produto_id is None: return

        produto_nome = self.gerenciador.produtos[produto_id].nome
        confirmacao = self._obter_input(f"Tem certeza que deseja remover '{produto_nome}'? Esta ação é irreversível. (s/n): ")
        if confirmacao and confirmacao.lower() == 's':
            if self.gerenciador.remover_produto(produto_id):
                print("Produto removido com sucesso.")
            else:
                print("Erro: Produto não encontrado.")
        else:
            print("Remoção cancelada.")

    def _buscar_por_barcode(self):
        """Busca um produto pelo código de barras e exibe suas informações."""
        self._imprimir_cabecalho("Buscar por Código de Barras")
        barcode = self._obter_input("Aponte o leitor e pressione Enter, ou digite o código de barras: ")
        produto = self.gerenciador.buscar_produto_por_codigo_barras(barcode)
        if produto:
            print("\n--- Produto Encontrado ---")
            print(f"ID: {produto.id}, Nome: {produto.nome}, Estoque Total: {produto.get_estoque_total()}")
        else:
            print("\nProduto não encontrado com este código de barras.")

    def _registrar_entrada_manual(self):
        """Permite registrar uma entrada de estoque manual para um produto."""
        self._imprimir_cabecalho("Registrar Entrada Manual de Estoque")
        produto_id = self._selecionar_em_lista("Selecione o produto", self.gerenciador.produtos)
        if produto_id is None: return

        produto_selecionado = self.gerenciador.produtos[produto_id]

        local_id = self._selecionar_em_lista(
            "Selecione a localização de entrada",
            self.gerenciador.localizacoes,
            contexto_produto=produto_selecionado
        )
        if local_id is None: return

        try:
            quantidade = self._obter_input("Digite a quantidade a ser adicionada: ", tipo='int')
            if quantidade is None or quantidade <= 0:
                print("Quantidade deve ser positiva.")
                return

            self.gerenciador.movimentar_estoque(produto_id, local_id, quantidade, "Entrada Manual")
            print("\nEntrada de estoque registrada com sucesso!")
        except Exception as e:
            print(f"\nErro ao registrar entrada: {e}")


    # Fornecedores
    def _listar_fornecedores(self):
        """Exibe uma lista de todos os fornecedores."""
        self._imprimir_cabecalho("Lista de Fornecedores")
        fornecedores = self.gerenciador.fornecedores
        if not fornecedores:
            print("Nenhum fornecedor cadastrado.")
            return

        separador = "-" * 40
        for f in sorted(fornecedores.values(), key=lambda x: x.id):
            print(separador)
            print(f"ID: {f.id}")
            print(f"Empresa: {f.empresa or 'N/A'}")
            print(f"Contato: {f.nome}")
            print(f"Telefone: {f.telefone or 'N/A'}")
            print(f"Email: {f.email or 'N/A'}")
            print(f"Endereço: {f.morada or 'N/A'}")
        print(separador)

    def _adicionar_fornecedor(self):
        """Guia o usuário no processo de adicionar um novo fornecedor."""
        self._imprimir_cabecalho("Adicionar Novo Fornecedor")
        try:
            nome = self._obter_input("Nome do Contato (deixe em branco para cancelar): ", obrigatorio=False)
            if not nome:
                print("\nAdição cancelada.")
                return

            empresa = self._obter_input("Empresa: ")
            telefone = self._obter_input("Telefone: ", obrigatorio=False)
            email = self._obter_input("Email: ", obrigatorio=False)
            morada = self._obter_input("Morada/Endereço: ", obrigatorio=False)

            self.gerenciador.adicionar_fornecedor(nome=nome, empresa=empresa, telefone=telefone, email=email, morada=morada)
            print("\nFornecedor adicionado com sucesso!")
        except Exception as e:
            print(f"\nErro ao adicionar fornecedor: {e}")

    def _atualizar_fornecedor(self):
        """Guia o usuário na atualização de um fornecedor."""
        self._imprimir_cabecalho("Atualizar Fornecedor")
        fornecedor_id = self._selecionar_em_lista("Selecione o fornecedor para atualizar", self.gerenciador.fornecedores)
        if fornecedor_id is None: return

        try:
            f = self.gerenciador.fornecedores[fornecedor_id]
            print("\nDeixe em branco para manter o valor atual.")
            nome = self._obter_input(f"Nome [{f.nome}]: ", obrigatorio=False) or f.nome
            empresa = self._obter_input(f"Empresa [{f.empresa}]: ", obrigatorio=False) or f.empresa
            telefone = self._obter_input(f"Telefone [{f.telefone}]: ", obrigatorio=False) or f.telefone
            email = self._obter_input(f"Email [{f.email}]: ", obrigatorio=False) or f.email
            morada = self._obter_input(f"Morada [{f.morada}]: ", obrigatorio=False) or f.morada

            self.gerenciador.atualizar_fornecedor(fornecedor_id, nome=nome, empresa=empresa, telefone=telefone, email=email, morada=morada)
            print("\nFornecedor atualizado com sucesso!")
        except Exception as e:
            print(f"\nErro ao atualizar fornecedor: {e}")

    def _remover_fornecedor(self):
        """Guia o usuário na remoção de um fornecedor (e seus produtos)."""
        self._imprimir_cabecalho("Remover Fornecedor")
        fornecedor_id = self._selecionar_em_lista("Selecione o fornecedor para remover", self.gerenciador.fornecedores)
        if fornecedor_id is None: return

        f = self.gerenciador.fornecedores[fornecedor_id]
        print("\nAVISO: Remover um fornecedor também removerá TODOS os produtos associados a ele.")
        confirmacao = self._obter_input(f"Tem certeza que deseja remover '{f.nome} ({f.empresa})'? (s/n): ")
        if confirmacao and confirmacao.lower() == 's':
            if self.gerenciador.remover_fornecedor(fornecedor_id):
                print("Fornecedor e seus produtos foram removidos.")
            else:
                print("Erro: Fornecedor não encontrado.")
        else:
            print("Remoção cancelada.")

    # Localizações e Transferências
    def _listar_localizacoes(self):
        """Exibe uma lista de todas as localizações."""
        self._imprimir_cabecalho("Lista de Localizações")
        locs = self.gerenciador.localizacoes
        if not locs:
            print("Nenhuma localização cadastrada.")
            return

        separador = "-" * 40
        for l in sorted(locs.values(), key=lambda x: x.id):
            print(separador)
            print(f"ID: {l.id}")
            print(f"Nome: {l.nome}")
            print(f"Endereço: {l.endereco or 'N/A'}")
        print(separador)

    def _adicionar_localizacao(self):
        """Guia o usuário para adicionar uma nova localização."""
        self._imprimir_cabecalho("Adicionar Nova Localização")
        try:
            nome = self._obter_input("Nome da Loja/Depósito (deixe em branco para cancelar): ", obrigatorio=False)
            if not nome:
                print("\nAdição cancelada.")
                return

            endereco = self._obter_input("Endereço: ", obrigatorio=False)
            self.gerenciador.adicionar_localizacao(nome=nome, endereco=endereco or "")
            print("\nLocalização adicionada com sucesso!")
        except Exception as e:
            print(f"\nErro: {e}")

    def _atualizar_localizacao(self):
        """Guia o usuário para atualizar uma localização."""
        self._imprimir_cabecalho("Atualizar Localização")
        loc_id = self._selecionar_em_lista("Selecione a localização para atualizar", self.gerenciador.localizacoes)
        if loc_id is None: return

        try:
            l = self.gerenciador.localizacoes[loc_id]
            print("\nDeixe em branco para manter o valor atual.")
            nome = self._obter_input(f"Nome [{l.nome}]: ", obrigatorio=False) or l.nome
            endereco = self._obter_input(f"Endereço [{l.endereco}]: ", obrigatorio=False) or l.endereco
            self.gerenciador.atualizar_localizacao(loc_id, nome=nome, endereco=endereco)
            print("\nLocalização atualizada com sucesso!")
        except Exception as e:
            print(f"\nErro: {e}")

    def _remover_localizacao(self):
        """Guia o usuário na remoção de uma localização."""
        self._imprimir_cabecalho("Remover Localização")
        loc_id = self._selecionar_em_lista("Selecione a localização para remover", self.gerenciador.localizacoes)
        if loc_id is None: return

        try:
            loc_nome = self.gerenciador.localizacoes[loc_id].nome
            confirmacao = self._obter_input(f"Tem certeza que deseja remover '{loc_nome}'? (s/n): ")
            if confirmacao and confirmacao.lower() == 's':
                self.gerenciador.remover_localizacao(loc_id)
                print("Localização removida.")
            else:
                print("\nRemoção cancelada.")
        except Exception as e:
            print(f"\nErro: {e}")

    def _realizar_transferencia(self):
        """Guia o usuário no processo de transferir estoque entre localizações."""
        self._imprimir_cabecalho("Transferir Estoque")
        try:
            produto_id = self._selecionar_em_lista("Selecione o produto a ser transferido", self.gerenciador.produtos)
            if produto_id is None: return

            produto_selecionado = self.gerenciador.produtos[produto_id]

            print("\n--- Localização de ORIGEM ---")
            origem_id = self._selecionar_em_lista(
                "Selecione a localização de origem",
                self.gerenciador.localizacoes,
                contexto_produto=produto_selecionado
            )
            if origem_id is None: return

            print("\n--- Localização de DESTINO ---")
            destino_id = self._selecionar_em_lista(
                "Selecione a localização de destino",
                self.gerenciador.localizacoes,
                contexto_produto=produto_selecionado
            )
            if destino_id is None: return

            quantidade = self._obter_input("Quantidade a transferir: ", tipo='int')

            self.gerenciador.transferir_estoque(produto_id, origem_id, destino_id, quantidade)
            print("\nTransferência realizada com sucesso!")
        except Exception as e:
            print(f"\nErro na transferência: {e}")

    # Vendas
    def _registrar_venda(self):
        """Gerencia a interface para registrar uma nova venda, item por item."""
        self._imprimir_cabecalho("Registrar Nova Venda")
        try:
            local_id = self._selecionar_em_lista("Selecione o local de saída do estoque", self.gerenciador.localizacoes)
            if local_id is None:
                print("\nOperação cancelada.")
                self._esperar_enter()
                return

            nome_cliente = self._obter_input("Nome do Cliente: ")
            local_selecionado = self.gerenciador.localizacoes[local_id]

            # Dicionário para gerenciar o estado do estoque *durante* esta venda.
            # Isso evita alterações no estoque real até a confirmação final.
            estoque_temporario = {
                p_id: p.estoque_por_local.get(local_selecionado.nome, 0)
                for p_id, p in self.gerenciador.produtos.items()
            }
            itens_venda = []

            while True:
                self._imprimir_cabecalho(f"Venda em andamento - Local: {local_selecionado.nome}")
                print(f"Cliente: {nome_cliente}")

                # Exibe o carrinho de compras atual
                total_parcial = 0
                if itens_venda:
                    print("\n--- Carrinho Atual ---")
                    for item in itens_venda:
                        produto_carrinho = self.gerenciador.produtos[item['produto_id']]
                        subtotal_item = item['quantidade'] * produto_carrinho.preco_venda
                        total_parcial += subtotal_item
                        print(f"   - {item['quantidade']}x {produto_carrinho.nome} @ R$ {produto_carrinho.preco_venda:,.2f}")
                    print(f"----------------------")
                    print(f"Subtotal: R$ {total_parcial:,.2f}")
                else:
                    print("\nCarrinho vazio.")

                print("\n--- Adicionar Produto ---")
                print("Produtos disponíveis neste local):")
                ids_disponiveis = [pid for pid, qtd in estoque_temporario.items() if qtd > 0]

                if not ids_disponiveis:
                    print("Nenhum produto com estoque restante neste local.")
                else:
                    # Ordena por nome para melhor visualização
                    for produto_id in sorted(ids_disponiveis, key=lambda pid: self.gerenciador.produtos[pid].nome):
                        produto = self.gerenciador.produtos[produto_id]
                        print(f"   {produto.id} - {produto.nome} ({estoque_temporario[produto_id]})")

                id_selecionado = self._obter_input("\nDigite o ID do produto (ou 0 para finalizar e confirmar): ", tipo='int')

                if id_selecionado == 0:
                    break  # Sai do loop para finalizar a venda

                if id_selecionado not in self.gerenciador.produtos:
                    print("ID inválido. Tente novamente.")
                    self._esperar_enter()
                    continue

                produto = self.gerenciador.produtos[id_selecionado]
                estoque_disponivel_item = estoque_temporario.get(id_selecionado, 0)

                if estoque_disponivel_item <= 0:
                    print("Este produto não tem mais estoque disponível para esta venda.")
                    self._esperar_enter()
                    continue

                # Loop para obter uma quantidade válida
                while True:
                    qtd_desejada = self._obter_input(f"Quantidade para '{produto.nome}' (Disponível: {estoque_disponivel_item}): ", tipo='int')
                    if qtd_desejada is None or qtd_desejada <= 0:
                        print("Quantidade inválida. Deve ser um número maior que zero.")
                        continue
                    if qtd_desejada > estoque_disponivel_item:
                        print(f"Estoque insuficiente. Apenas {estoque_disponivel_item} unidades disponíveis.")
                    else:
                        break  # Quantidade válida

                # Subtrai do estoque temporário
                estoque_temporario[id_selecionado] -= qtd_desejada

                # Adiciona ao carrinho (ou atualiza a quantidade se já existir)
                item_existente = next((item for item in itens_venda if item['produto_id'] == id_selecionado), None)
                if item_existente:
                    item_existente['quantidade'] += qtd_desejada
                else:
                    itens_venda.append({'produto_id': id_selecionado, 'quantidade': qtd_desejada})

                print(f"'{produto.nome}' adicionado ao carrinho.")
                self._esperar_enter()

            if not itens_venda:
                print("\nNenhum item adicionado. Venda cancelada.")
                self._esperar_enter()
                return

            # Confirmação final
            confirmacao = self._obter_input("\nConfirmar e registrar esta venda? (s/n): ")
            if confirmacao and confirmacao.lower() == 's':
                # Ação real: persistir a venda no banco
                _, produtos_alertados = self.gerenciador.registrar_venda(itens_venda, nome_cliente, local_id)
                print("\nVenda registrada com sucesso!")
                if produtos_alertados:
                    print("\nAlerta de baixo estoque para:", ", ".join([p.nome for p in produtos_alertados]))
            else:
                # Ação abortada: o estoque temporário é simplesmente descartado.
                print("\nVenda cancelada. O estoque não foi alterado.")

        except Exception as e:
            print(f"\nErro ao registrar venda: {e}")
        finally:
            self._esperar_enter()


    # Ordens de Compra (OC)
    def _listar_ocs(self):
        """Exibe uma lista de todas as Ordens de Compra."""
        self._imprimir_cabecalho("Lista de Ordens de Compra")
        ocs = self.gerenciador.ordens_compra
        if not ocs:
            print("Nenhuma Ordem de Compra registrada.")
            return

        separador = "-" * 80
        # Mostra as mais recentes primeiro
        for oc in sorted(ocs.values(), key=lambda o: o.id, reverse=True):
            print(str(oc))


    def _criar_oc(self):
        """Guia o usuário na criação de uma nova Ordem de Compra."""
        self._imprimir_cabecalho("Criar Nova Ordem de Compra")
        try:
            fornecedor_id = self._selecionar_em_lista("Selecione o fornecedor da OC", self.gerenciador.fornecedores)
            if fornecedor_id is None:
                print("\nCriação de OC cancelada.")
                return

            fornecedor = self.gerenciador.fornecedores[fornecedor_id]
            # Filtra produtos para mostrar apenas os do fornecedor selecionado.
            produtos_fornecedor = {pid: p for pid, p in self.gerenciador.produtos.items() if p.fornecedor.id == fornecedor_id}

            itens_oc = []
            while True:
                print(f"\n--- Adicionar Item à OC (Fornecedor: {fornecedor.empresa}) ---")
                produto_id = self._selecionar_em_lista("Selecione o produto", produtos_fornecedor)
                if produto_id is None: break

                quantidade = self._obter_input("Quantidade a comprar: ", tipo='int')
                itens_oc.append({'produto_id': produto_id, 'quantidade': quantidade})
                print(f"Item '{self.gerenciador.produtos[produto_id].nome}' adicionado.")

                continuar = self._obter_input("Adicionar outro item? (s/n): ")
                if continuar and continuar.lower() != 's': break

            if not itens_oc:
                print("\nNenhum item. OC cancelada.")
                return

            confirmacao = self._obter_input("\nConfirmar e criar esta OC? (s/n): ")
            if confirmacao and confirmacao.lower() == 's':
                self.gerenciador.criar_ordem_compra(fornecedor_id, itens_oc)
                print("\nOrdem de Compra criada com sucesso!")
            else:
                print("\nCriação de OC cancelada.")

        except Exception as e:
            print(f"\nErro ao criar OC: {e}")

    def _atualizar_status_oc(self):
        """Guia o usuário para atualizar o status de uma OC."""
        self._imprimir_cabecalho("Atualizar Status de OC")
        oc_id = self._selecionar_em_lista("Selecione a OC para atualizar", self.gerenciador.ordens_compra)
        if oc_id is None: return

        oc = self.gerenciador.ordens_compra[oc_id]
        print(f"\nStatus atual da OC #{oc.id}: {oc.status}")
        print("Opções de Status: Pendente, Recebida, Cancelada")
        novo_status = self._obter_input("Digite o novo status: ").capitalize()

        try:
            local_id = None
            if novo_status and novo_status == 'Recebida':
                if oc.status == 'Recebida':
                    print("Esta OC já foi recebida.")
                    return
                local_id = self._selecionar_em_lista("Selecione a localização de entrada do estoque", self.gerenciador.localizacoes)
                if local_id is None:
                    print("\nAtualização cancelada.")
                    return

            if novo_status:
                self.gerenciador.atualizar_status_ordem(oc_id, novo_status, localizacao_id=local_id)
                print(f"\nStatus da OC #{oc_id} atualizado para '{novo_status}' com sucesso!")
            else:
                print("\nNenhum status inserido. Operação cancelada.")

        except Exception as e:
            print(f"\nErro ao atualizar status: {e}")

    def _visualizar_salvar_oc(self):
        """Exibe o recibo de uma OC e oferece opções para salvá-lo."""
        self._imprimir_cabecalho("Visualizar/Salvar Recibo de OC")
        oc_id = self._selecionar_em_lista("Selecione a OC", self.gerenciador.ordens_compra)
        if oc_id is None: return

        oc = self.gerenciador.ordens_compra[oc_id]
        texto_recibo = self._gerar_texto_recibo_oc(oc)

        self._limpar_tela()
        print(texto_recibo)

        print("\n--- Opções ---")
        print("1. Salvar como TXT")
        if REPORTLAB_DISPONIVEL:
            print("2. Salvar como PDF")
        print("0. Voltar")

        escolha = self._obter_input("Escolha uma opção: ")

        if escolha == '1':
            self._salvar_oc_txt(oc, texto_recibo)
        elif escolha == '2' and REPORTLAB_DISPONIVEL:
            self._salvar_oc_pdf(oc)

    def _gerar_texto_recibo_oc(self, ordem: OrdemCompra) -> str:
        """Formata os dados de uma Ordem de Compra em um texto legível."""
        linhas = [
            "==========================================",
            "          ORDEM DE COMPRA (RECIBO)          ",
            "==========================================",
            f"Número do Pedido: {ordem.id}",
            f"Data de Emissão: {ordem.data_criacao.strftime('%d/%m/%Y %H:%M:%S')}",
            f"Status: {ordem.status}",
            "\n--- DADOS DO FORNECEDOR ---",
            f"Empresa: {ordem.fornecedor.empresa}",
            f"Nome do Contato: {ordem.fornecedor.nome}",
            f"Telefone: {ordem.fornecedor.telefone}",
            f"Email: {ordem.fornecedor.email}",
            f"Morada: {ordem.fornecedor.morada}",
            "\n--- ITENS DO PEDIDO ---"
        ]

        header = f'{"ID":<5}{"Produto":<30}{"Qtd":>5} {"Preço Un.":>15} {"Subtotal":>15}'
        linhas.append(header)
        linhas.append("-" * len(header))

        for item in ordem.itens:
            linha_item = (f"{item.produto.id:<5}"
                          f"{item.produto.nome[:29]:<30}"
                          f"{item.quantidade:>5} "
                          f"{f'R$ {item.preco_unitario:,.2f}':>15}"
                          f"{f'R$ {item.subtotal:,.2f}':>15}")
            linhas.append(linha_item)

        linhas.append("-" * len(header))
        linhas.append(f"{'VALOR TOTAL:':>56} {f'R$ {ordem.valor_total:,.2f}':>15}")

        return "\n".join(linhas)

    def _salvar_oc_txt(self, ordem: OrdemCompra, texto_recibo: str):
        """Salva o recibo de uma OC em um arquivo de texto."""
        filename = self._obter_input("Nome do arquivo (ex: pedido_1.txt): ", obrigatorio=False) or f"Ordem_de_Compra_{ordem.id}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(texto_recibo)
            print(f"\nRecibo salvo com sucesso em '{filename}'")
        except Exception as e:
            print(f"\nErro ao salvar arquivo: {e}")

    def _salvar_oc_pdf(self, ordem: OrdemCompra):
        """Salva o recibo de uma OC em um arquivo PDF usando ReportLab."""
        filename = self._obter_input("Nome do arquivo (ex: pedido_1.pdf): ", obrigatorio=False) or f"Ordem_de_Compra_{ordem.id}.pdf"
        try:
            c = canvas.Canvas(filename, pagesize=letter)
            width, height = letter
            y = height - inch
            c.setFont("Helvetica-Bold", 16)
            c.drawString(inch, y, f"ORDEM DE COMPRA #{ordem.id}")
            y -= 0.5 * inch
            c.setFont("Helvetica", 10)
            c.drawString(inch, y, f"Data de Emissão: {ordem.data_criacao.strftime('%d/%m/%Y')}")
            c.drawString(width - 2.5*inch, y, f"Status: {ordem.status}")
            y -= 0.3 * inch
            c.line(inch, y, width - inch, y)
            y -= 0.3 * inch
            c.setFont("Helvetica-Bold", 11)
            c.drawString(inch, y, "Dados do Fornecedor:")
            y -= 0.2 * inch
            c.setFont("Helvetica", 10)
            c.drawString(inch, y, f"Empresa: {ordem.fornecedor.empresa} (Contato: {ordem.fornecedor.nome})"); y -= 0.2 * inch
            c.drawString(inch, y, f"Telefone: {ordem.fornecedor.telefone} | Email: {ordem.fornecedor.email}"); y -= 0.2 * inch
            c.drawString(inch, y, f"Morada: {ordem.fornecedor.morada}"); y -= 0.4 * inch
            c.line(inch, y, width - inch, y); y -= 0.3 * inch
            c.setFont("Helvetica-Bold", 11)
            c.drawString(inch, y, "Itens do Pedido:"); y -= 0.25 * inch
            c.setFont("Helvetica-Bold", 10)
            c.drawString(inch, y, "ID"); c.drawString(inch + 0.5*inch, y, "Produto")
            c.drawRightString(width - 3*inch, y, "Qtd."); c.drawRightString(width - 2*inch, y, "Preço Un.")
            c.drawRightString(width - inch, y, "Subtotal"); y -= 0.2 * inch
            c.setFont("Helvetica", 10)
            for item in ordem.itens:
                if y < inch: c.showPage(); y = height - inch; c.setFont("Helvetica", 10) # Adiciona nova página se necessário
                c.drawString(inch, y, str(item.produto.id))
                c.drawString(inch + 0.5*inch, y, item.produto.nome)
                c.drawRightString(width - 3*inch, y, str(item.quantidade))
                c.drawRightString(width - 2*inch, y, f"R$ {item.preco_unitario:,.2f}")
                c.drawRightString(width - inch, y, f"R$ {item.subtotal:,.2f}")
                y -= 0.2 * inch
            y -= 0.2 * inch
            c.line(inch, y, width - inch, y); y -= 0.3 * inch
            c.setFont("Helvetica-Bold", 12)
            c.drawRightString(width - inch, y, f"VALOR TOTAL: R$ {ordem.valor_total:,.2f}")
            c.save()
            print(f"\nRecibo PDF salvo com sucesso em '{filename}'")
        except Exception as e:
            print(f"\nErro ao salvar PDF: {e}")

    # Relatórios
    def _gerar_relatorio_detalhado(self, tipo_relatorio):
        """Chama a função de geração de relatório correspondente no gerenciador e exibe o resultado."""
        self._imprimir_cabecalho(f"Relatório: {tipo_relatorio}")
        report_text = ""
        try:
            if tipo_relatorio == "Inventário Completo (Simplificado)":
                report_text = self.gerenciador.gerar_relatorio_estoque_simplificado()
            elif tipo_relatorio == "Valor Total do Inventário":
                report_text = self.gerenciador.gerar_relatorio_valor_total()
            elif tipo_relatorio == "Produtos com Baixo Estoque":
                report_text = self.gerenciador.gerar_relatorio_baixo_estoque()
            elif tipo_relatorio == "Produtos Mais Vendidos":
                report_text = self.gerenciador.gerar_relatorio_mais_vendidos()
            elif tipo_relatorio == "Histórico de Movimentação por Item":
                produto_id = self._selecionar_em_lista("Selecione o produto", self.gerenciador.produtos)
                if produto_id: report_text = self.gerenciador.gerar_relatorio_movimentacao_item(produto_id)
                else: return # Cancela se nenhum produto for selecionado
            elif tipo_relatorio == "Relatório de Vendas por Período":
                str_inicio = self._obter_input("Data de Início (DD/MM/AAAA): ")
                str_fim = self._obter_input("Data de Fim (DD/MM/AAAA): ")
                if str_inicio and str_fim:
                    # Converte as strings de data para objetos datetime
                    data_inicio = datetime.strptime(str_inicio, "%d/%m/%Y")
                    # Define a hora do fim para o final do dia para incluir todas as vendas do dia.
                    data_fim = datetime.combine(datetime.strptime(str_fim, "%d/%m/%Y"), time.max)
                    report_text = self.gerenciador.gerar_relatorio_vendas_periodo(data_inicio, data_fim)
                else: return # Cancela se as datas não forem inseridas

            print(report_text)
        except Exception as e:
            print(f"Erro ao gerar relatório: {e}")