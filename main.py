# Oiiiii. Eu tentei comentar esse código o máximo possivel pra que ficasse mais facil de se entendê-lo
# Tambem tentei deixar os nomes de variáveis, funções e classes o mais descritivos possível
# Alguns dos comentários foram feitos pelo copilot, mas eu revisei todos eles 
# porém, sei que pode ter uma coisa ou outra que esteja meio estranha e confusa
# Por isso, se você tiver qualquer dúvida, pode me chamar no zap que eu respondo... em algum momento
# 82 98763-8329
# E me desculpa se voce encontrar qualquer atrocidade, é o meu jeitinho 😋


# main.py

# Importa as classes principais de cada módulo do sistema.
from config import DB_FILE
from database import DatabaseManager
from manager import GerenciadorEstoque
from cli import CliApp

# --- Bloco de Execução Principal ---

# esse "if __name__ == "__main__":" garante que o código dentro dele só será executado
# quando este arquivo for rodado diretamente 
# (e não quando for importado por outro arquivo)
if __name__ == "__main__":
    # 1. vai inicializar o gerenciador do banco de dados
    db = DatabaseManager(DB_FILE)
    # 2. conectar ao arquivo do banco de dados
    db.connect()
    # 3. garantir que todas as tabelas necessárias existam
    db.create_tables()

    # 4. inicializar o gerenciador da lógica de negócios, passando o gerenciador do DB
    gerenciador = GerenciadorEstoque(db)
    # 5. earregar todos os dados existentes do banco para a memória
    gerenciador.carregar_dados_do_banco()

    # 6. e verifica se o banco de dados está vazio (sem fornecedores)
    # se tiver, popula com dados iniciais para demonstração
    if not gerenciador.fornecedores:
        print("Banco de dados parece vazio. Populando com dados iniciais...")
        try:
            # adiciona localizações
            deposito = gerenciador.adicionar_localizacao(nome="Depósito Central", endereco="Rua Principal, 123")
            loja_a = gerenciador.adicionar_localizacao(nome="Loja A - Shopping", endereco="Shopping Center, Loja 15")

            # adiciona fornecedores
            asus = gerenciador.adicionar_fornecedor(
                nome="Carlos Silva", empresa="ASUS Brasil", telefone="11987654321",
                email="carlos.silva@asus.com.br", morada="Av. Paulista, 1000, Maceió, AL"
            )
            logitech = gerenciador.adicionar_fornecedor(
                nome="Ana Pereira", empresa="Logitech BR", telefone="21912345678",
                email="ana.pereira@logitech.com", morada="Rua da Praia, 50, Carneiros, AL"
            )
            dell = gerenciador.adicionar_fornecedor(
                nome="Maria Souza", empresa="Dell Brasil", telefone="51998761234",
                email="maria.souza@dell.com", morada="Av. Ipiranga, 6681, Inferno, PE"
            )

            # adiciona produtos
            p1 = gerenciador.adicionar_produto(nome="Notebook ROG Strix", descricao="Notebook Gamer 16GB RAM, RTX 4060", categoria="Eletrônicos", fornecedor_id=asus.id, codigo_barras="789123456001", preco_compra=5000, preco_venda=7500, ponto_ressuprimento=10)
            p2 = gerenciador.adicionar_produto(nome="Mouse G502 Hero", descricao="Mouse Gamer com RGB e 25k DPI", categoria="Periféricos", fornecedor_id=logitech.id, codigo_barras="789789789002", preco_compra=250, preco_venda=450, ponto_ressuprimento=20)
            p3 = gerenciador.adicionar_produto(nome="Monitor Alienware 27''", descricao="Monitor Gamer 240Hz, QHD, Fast IPS", categoria="Eletrônicos", fornecedor_id=dell.id, codigo_barras="789456123003", preco_compra=2200, preco_venda=3800, ponto_ressuprimento=5)
            p4 = gerenciador.adicionar_produto(nome="Half-Life: Episode 3", descricao="Jogo nunca antes existido", categoria="Jogos", fornecedor_id=logitech.id, codigo_barras="789789789005", preco_compra=450, preco_venda=700, ponto_ressuprimento=15)
            
            # movimenta o estoque inicial
            gerenciador.movimentar_estoque(p1.id, deposito.id, 15, "Carga Inicial")
            gerenciador.movimentar_estoque(p2.id, deposito.id, 50, "Carga Inicial")
            gerenciador.movimentar_estoque(p3.id, deposito.id, 8, "Carga Inicial")

            # Você deve ter percebido isso ja, mas só por desencargo de consciência é bom comentar
            # Essas três adições acima (localizações, fornecedores e produtos) são apenas e unicamente para se inicializar o banco de dados
            # e garantir que o sistema tenha dados para trabalhar
            # Você pode apagar eles se quiser, tá tranquilo
            # Um cheiro

            # faz uma transferência
            gerenciador.transferir_estoque(p1.id, deposito.id, loja_a.id, 5)

            # registra uma venda
            gerenciador.registrar_venda([{'produto_id': p1.id, 'quantidade': 2}], 'João da Silva', loja_a.id)

            print("Dados iniciais populados. Recarregando...")
            # recarrega os dados para que a memória reflita exatamente o que foi salvo no DB
            gerenciador.carregar_dados_do_banco()
        except Exception as e:
            print(f"Ocorreu um erro ao popular os dados iniciais: {e}")

    # 7. inicializa e executa a aplicação de terminal
    app = CliApp(gerenciador)
    try:
        # esse método método run() inicia o loop principal da interface
        app.run()
    except KeyboardInterrupt:
        # e aqui é permitido que o usuário saia do programa com Ctrl+C bem bonitinho
        print("\nSaindo a pedido do usuário...")
    finally:
        # esse diabo desse bloco SEMPRE vai ser executado no final, seja por saída normal ou por erro
        # gaarante que a conexão com o banco de dados seja fechada ao sair
        print("Fechando conexão com o banco de dados...")
        db.close()