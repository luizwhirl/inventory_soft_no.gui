# database.py
# Contém a classe DatabaseManager para gerenciar todas as interações com o banco de dados SQLite.

import sqlite3
import sys

# --- Classe de Gerenciamento do Banco de Dados ---

class DatabaseManager:
    """aqui a gente vai gerenciar nossa conexão com o diabo do banco de dados"""
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.cursor = None

    def connect(self):
        """Estabelece a conexão com o banco de dados SQLite"""
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.execute("PRAGMA foreign_keys = ON;") # pra garantir que as chaves estrangeiras funcionem
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            sys.exit(1)

    def close(self):
        """fecha o satanas da conexão com o banco de dados, isso se estiver aberta ainda"""
        if self.conn:
            self.conn.close()

    def execute_query(self, query, params=(), fetch=None):
        """se for preciso, executa uma query no banco de dados e retorna o resultado"""
        try:
            self.cursor.execute(query, params)
            if fetch == 'one':
                return self.cursor.fetchone()
            if fetch == 'all':
                return self.cursor.fetchall()
            # se não for uma query de busca , faz o commit das alterações
            self.conn.commit()
            # retorna o ID da última linha inserida, o que pode ser útil para obter o ID de novos registros
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Erro ao executar query: {e}")
            print(f"Query: {query}")
            # retonra None em caso de erro para que a lógica da aplicação possa tratar
            return None


    def create_tables(self):
        """cria todas as tabelas necessárias no banco de dados, isso se elasainda não existirem"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS fornecedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                empresa TEXT,
                telefone TEXT,
                email TEXT,
                morada TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS localizacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                endereco TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT,
                categoria TEXT,
                codigo_barras TEXT,
                preco_compra REAL NOT NULL,
                preco_venda REAL NOT NULL,
                ponto_ressuprimento INTEGER NOT NULL,
                fornecedor_id INTEGER NOT NULL,
                FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS estoque (
                produto_id INTEGER NOT NULL,
                localizacao_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                PRIMARY KEY (produto_id, localizacao_id),
                FOREIGN KEY (produto_id) REFERENCES produtos (id) ON DELETE CASCADE,
                FOREIGN KEY (localizacao_id) REFERENCES localizacoes (id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS historico_movimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                localizacao_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                data TEXT NOT NULL,
                FOREIGN KEY (produto_id) REFERENCES produtos (id) ON DELETE CASCADE,
                FOREIGN KEY (localizacao_id) REFERENCES localizacoes (id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS ordens_compra (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fornecedor_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                data_criacao TEXT NOT NULL,
                FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS itens_ordem_compra (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ordem_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_unitario REAL NOT NULL,
                FOREIGN KEY (ordem_id) REFERENCES ordens_compra(id) ON DELETE CASCADE,
                FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_nome TEXT NOT NULL,
                data TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS itens_venda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_venda_unitario REAL NOT NULL,
                FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE,
                FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
            );
            """
        ]
        # exeutando cada uma das queries de criação de tabela
        # Zzzzz
        for query in queries:
            self.execute_query(query)