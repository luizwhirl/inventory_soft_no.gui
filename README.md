# Sistema de Gerenciamento de Estoque

Criei esse readme breve aqui só pra direcionar um pouco o satánas desse sistema, mas fique livre pra entrar em contato comigo e perguntar qualquer coisa.

As bibliotecas utilizadas foram o **SQLite** para a persistência de dados e, opcionalmente, **ReportLab** para gerar relatórios em PDF. A interface é inteiramente via linha de comando (CLI).

## Visão Geral

O sistema em si é um controle de inventário, tal como é solicitado na especificação do projeto. Portanto ele conta com os requerimentos solicitados pelo professor:

### **Product Catalog Management:**
Esse sisteminha infernal vai deixar que você possa adicionar, atualizar, categorizar e remover itens do inventário.
- **Interface:** O menu `Gerenciar Produtos` centraliza todas essas operações.
- **Adicionar/Atualizar:** O sistema guia o usuário através de prompts para preencher os dados de um novo produto ou para editar um item selecionado na lista. O sistema vai validar os campos obrigatórios como nome, fornecedor e preços.
- **Categorização:** Ao adicionar um produto, o sistema exibe as categorias existentes para referência, mas permite que uma nova seja digitada livremente.
- **Remoção:** É possível selecionar um produto de uma lista para removê-lo. Essa ação remove o produto do banco de dados e não pode ser desfeita.

### **Stock Level Tracking:**
- **Estoque:** O estoque de um produto não é um valor único, mas sim um dicionário que mapeia cada Localização (como "Depósito Central", "Loja A", etc.) à sua respectiva quantidade. O estoque total é, na verdade, uma soma das quantidades em todas as localizações.
- **Visualização detalhada:** Ao listar todos os produtos, o estoque por local é exibido para cada um. Ao realizar transferências ou entradas, o estoque atual no local é mostrado para dar contexto.
- **Atualização Automática:** Qualquer operação atualiza instantaneamente os dados tanto em memória quanto no banco de dados.

### **Reorder Alerts:**

- **Ponto de Ressupr.:** Ao cadastrar ou atualizar um produto, um "Ponto de Ressuprimento" deve ser definido. Esse valor é o nível mínimo de estoque que, ao ser atingido, dispara um alerta.
- **Geração de Alertas:** Durante uma operação de saída (venda) que faça o estoque do produto atingir ou ficar abaixo do ponto de ressuprimento, um alerta é gerado.
- **Painel de Alertas:** O menu principal exibe um aviso em destaque com a contagem de quantos produtos estão com estoque baixo. Há também um relatório específico para listar todos esses itens.

### **Supplier Management:**

O menu `Gerenciar Fornecedores` é basicamente o CRUD de, adivinha só: Fornecedores!

Aqui o sistema vai armazenar o nome do contato, empresa, telefone, email e endereço do indivíduo.

Como um produto não existe sem um fornecedor, a exclusão de um fornecedor resulta na exclusão automática de todos os produtos associados a ele.

eh mole

### **Purchase Order Creation:**
O sistema também permite a geração e gerenciamento de Ordens de Compra (OCs) para formalizar pedidos aos fornecedores. Eis o fluxo da coisa dentro do menu `Gerenciar Ordens de Compra (OC)` (essa coisa tá começando a ficar muito óbvia):

1.  Seleciona-se um fornecedor, e o sistema filtra para mostrar apenas os produtos dele.
2.  Os produtos e quantidades escolhidos são adicionados à OC.
3.  Ao salvar, a OC gerada é categorizada como "Pendente".
4.  Ao se receber os produtos, o usuário seleciona a OC e pode marcá-la como "Recebida".
5.  O sistema vai então solicitar a **Localização** onde o estoque deve ser adicionado, e a quantidade é atualizada automaticamente.

- É possível visualizar um recibo detalhado da OC e exportá-lo tanto para TXT quanto para PDF (o que vai precisar da biblioteca `reportlab`).
> Isso não é realmente necessário, o sistema vai funcionar normalmente sem isso. Porém é uma adição interessante para se usar.

### **Inventory Valuation:**

Adivinha o que é que isso aqui faz, duvido.

- **Cálculo:** O valor é calculado multiplicando a quantidade total de cada produto pelo seu `preco_compra`.
- **Exibição:** O valor total do estoque é exibido de forma proeminente no Menu Principal e também no cabeçalho de relatórios de inventário. A lógica desse cálculo está na função `calcular_valor_total_estoque()`, da classe `GerenciadorEstoque` em `manager.py`.

### **Sales and Purchase History:**
Todas as transações de entrada e saída são registradas, permitindo análise histórica.

O menu `Gerenciar Ordens de Compra` funciona como um histórico de compras, e os seus status permitem acompanhar o ciclo de vida de cada pedido. Para as vendas, o menu `Gerar Relatórios` permite criar um "Relatório de Vendas por Período", que lista todas as vendas realizadas, detalhando produtos, quantidades e valores daquela transação específica.

### **Multi-Location Management:**
Esse diabinho aqui vai deixar você adicionar, gerenciar e rastrear o estoque através de múltiplos locais físicos.
- O menu `Gerenciar Localizações e Transferências` permite o CRUD das localizações como armazéns, depósitos ou lojas.
- **Rastreamento Específico:** Como dito láaa no comecinho desse readme, o estoque de cada produto é rastreado individualmente para cada localização.
- Dentro do mesmo menu, é possível mover produtos entre localizações. O sistema vai validar se tem estoque o suficiente na origem e registra a operação para manter íntegro o histórico de movimentação.

### **Inventory Reports:**
Essa seção é dedicada para se gerar relatórios textuais detalhados sobre vários aspectos do inventário. Todos os relatórios disponíveis no menu `Gerar Relatórios` são:

- **Inventário Completo (Simplificado):** Lista todos os produtos com seu estoque total e detalhamento por local.
- **Valor Total do Inventário:** Exibe o valor total do estoque com base no custo.
- **Produtos com Baixo Estoque:** Lista somente os itens que atingiram o ponto de ressuprimento.
- **Produtos Mais Vendidos:** Ranking de produtos baseado na quantidade total vendida.
- **Histórico de Movimentação por Item:** Extrato detalhado de entradas, saídas e transferências para um produto específico.
- **Relatório de Vendas por Período:** Analisa as vendas, receita e lucro dentro de um intervalo de datas inseridas pelo usuário.

### **Barcode Scanning:**

A funcionalidade de scanner é simulada através de uma opção de menu específica.

Leitores de código de barras normalmente respondem ao computador como um teclado comum. A leitura é feita como se o número do código de barras fosse digitado e a tecla "Enter" pressionada. Portanto, é justamente nisso que esse código se baseia.

Para utilizar essa funcionalidade, vá em `Gerenciar Produtos -> 5. Buscar produto por Código de Barras` e digite (ou use um leitor para "digitar") o código. O sistema então buscará e exibirá o produto correspondente.

## Separação do código
O código está organizado em módulos para separar as responsabilidades:

- `main.py`: Ponto de entrada. Inicializa o banco de dados, o gerenciador e a interface de linha de comando.
- `config.py`: Contém constantes e configurações do projeto, tipo o nome do arquivo do banco de dados.
- `database.py`: Gerencia toda a interação com o banco de dados SQLite.
- `models.py`: Define a estrutura de todos os objetos de negócio (Produto, Fornecedor, Venda, etc.) usando `dataclasses`.
- `manager.py`: O cérebro da aplicação, é aqui que está o desgraçado do `GerenciadorEstoque`. Possui toda a lógica de negócio e manipulação dos dados, sem interagir diretamente com a interface.
- `cli.py`: Contém a classe `CliApp`, responsável por toda a construção e gerenciamento da interface de linha de comando (CLI). Constrói os menus, captura os inputs do usuário e chama os métodos do `GerenciadorEstoque`.

## Funcionalidades extras

 ### Gestão de devoluções e trocas 
Dá procedência ao processo de devoluçãoes de clientes ou trocas de produtos de uma forma eficiente. Ao um produto ser devolvido, o estoque deve é atualizado, e em caso de troca, o produto trocado precisa ser registrado.
 
-  O usuário pode analisar a situação do produto para então decidir se deve trocar ou reembolsar o cliente
-  No caso de um reembolso, o sistema calcula o valor total a ser devolvido.
- Caso seja uma devolução, o produto volta ao estoque 
> O que não deveria ser o caso. Cabe mudança 

## Implementações futuras

### Histórico em tempo real de movimentação
 Uma movimentação de determinado produto ainda não pode ser especifícada para se mostrar todo o histórico. Portanto, seria interessante a adição dessa funcionaldiade

 - **Visualização de histórico:** Visualizão de histórico por produto, fornecedor, localidade, etc. 




### Sistema de validade e lote (?)
> Ainda não decidi qual o foco do inventário

### Relatórios Personalizados
Apesar de já existirem os relatórios pré-definidos, seria interessante que o usuário pudesse criar seus próprios relatórios, selecionando os campos, filtros e agrupamentos que desejar

#### Objetos

- `Campo Relatório`: - 
- `RelatorioPersonalizado`:
- `FiltroRelatório`: Representa a condição do filtro (por exemplo: Categoria = "Eletrônicos) 

### Gestão/Montagem de Kitting

Podemos permitir que o usuário crie "kits" de produtos (tipo um kit informática que inclui teclado, mouse e monitor). Ao se vender esse kit, o estoque dos componentes individuais é automaticamente ajustado.
> Acho que é bom refinar essa ideia. O kit pode também ocupar uma única unidade dentro do sistema.

- `KitProduto`: Representa o kit de produtos, com atributos como o nomeKit, descriçao, preçoVendaKit, e uma lista de ComponenteKit (que por sua vez deve conter os produtos DO INVENTÁRIO contidos nesse kit)
- `ComponenteKit`: Produto individual que faz parte de um kit, com atributos como produto (que no caso vai ser referência ao **objeto Produto** e **quantidadeComponente**).

## Como Executar o Projeto

### Pré-requisitos

- **Python 3.x**
- **ReportLab (Opcional):** Necessário apenas para a funcionalidade de exportar recibos de Ordens de Compra para PDF. O programa funcionará normalmente sem ele, apenas com a opção de PDF desabilitada.
> *Essa função de exportar os recibos em txt ou pdf foi só uma outra funçãozinha divertida que eu inseri, mas de novo, não é algo essencial pro programa. Esse sistema tá cheio dessas coisinhas, na verdade.*

### Instalação de Dependências

Para habilitar a exportação para PDF, instale a biblioteca `reportlab`:

```bash
pip install reportlab
```

### Execução

Para executar esse diabo, basta clonar o repositório no seu ambiente e executar o arquivo `main.py` a partir do seu terminal:

```bash
python main.py
```

### Primeira Execução

- Na primeira vez que o programa for executado, ele criará um arquivo de banco de dados chamado `estoque_database.db` no mesmo diretório.
- O sistema detectará que o banco está vazio e o populará com dados de exemplo (fornecedores, localizações, produtos, etc.) para que as funcionalidades possam ser testadas imediatamente.

#### Xero!
![xerinhos](https://www.picgifs.com/comment-gifs/k/kisses-for-you/animaatjes-kisses-for-you-726237.gif)
