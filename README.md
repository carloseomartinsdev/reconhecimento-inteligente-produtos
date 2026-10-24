# Reconhecimento inteligente de produtos comerciais

Projeto da disciplina de Visão Computacional: Técnicas e Aplicações, em um contexto de pós-graduação/MBA em Ciência de Dados. O trabalho identifica um produto de cesta básica a partir de uma fotografia e mostra preços registrados localmente para os itens parecidos do catálogo.

**Status: Fase 2.2 parcial — demonstração de escaneamento**

O catálogo brasileiro não chegou a 50 produtos e o conjunto de imagens não chegou a 200 arquivos válidos. Há um classificador de categoria ajustado para a demonstração. Ele não é uma medida de generalização. Os preços exibidos no aplicativo são de teste e não são coleta de mercado.

## Objetivo

Permitir que uma fotografia de embalagem indique a categoria do produto e abra os itens correspondentes do catálogo, com o preço registrado no banco local e a comparação estatística quando houver registros suficientes.

## Dataset

- Catálogo comercial: produtos brasileiros de cesta básica obtidos no [Open Food Facts](https://world.openfoodfacts.org/)
- Licença das fotografias: CC BY-SA, com a ressalva de que a licença da foto não cobre a arte da embalagem
- Termos: https://world.openfoodfacts.org/terms-of-use
- Produtos validados: 37 de 50
- Imagens aceitas na validação técnica: 117 de 119 coletadas
- Produtos com pelo menos 4 imagens válidas: 14 de 37
- Manifesto: `data/brazilian_products/metadata/image_manifest.csv`
- Relatórios: [`docs/FASE_2_2_CATALOGO.md`](docs/FASE_2_2_CATALOGO.md), [`docs/FASE_2_2_DATASET.md`](docs/FASE_2_2_DATASET.md) e [`docs/FASE_2_2_RELATORIO.md`](docs/FASE_2_2_RELATORIO.md)

O RPC (Retail Product Checkout) permanece só como referência de protocolo. O pacote de imagens não foi baixado. A página oficial é https://rpc-dataset.github.io/ e a licença informada é CC BY-NC-SA 4.0.

As fotografias do catálogo, o banco SQLite e os pesos do classificador ficam de fora do Git. O `.gitignore` cobre essas pastas. Quem clonar o repositório recebe o código, o manifesto e a documentação. As imagens e o arquivo `models/brazilian/classifier.pt` precisam existir na máquina para o escaneamento mostrar foto de referência e categoria.

## Estrutura do projeto

```text
reconhecimento-inteligente-produtos/
├── README.md
├── requirements.txt
├── requirements.lock.txt
├── .gitignore
├── app/
│   └── streamlit_app.py
├── configs/
├── data/
│   ├── brazilian_products/   # metadados versionados; imagens locais
│   └── prices/               # SQLite local, fora do Git
├── docs/
├── notebooks/
├── scripts/
├── src/
└── tests/
```

## Instalação

Os comandos abaixo assumem Windows e PowerShell, a partir da pasta do projeto. Nesta máquina o PyTorch usado é o wheel de CPU.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

As versões resolvidas nesta instalação estão em `requirements.lock.txt`.

## Como executar

Aplicação, em http://localhost:8501. A tela inicial é Escanear.

```powershell
.\.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

Na primeira execução o aplicativo importa o catálogo validado e grava cinco preços de teste por produto. A condição da oferta informa que não são preços de mercado. O arquivo fica em `data/prices/market.sqlite`.

Testes:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

O ajuste demonstrativo do classificador, quando as imagens do catálogo já estão na pasta local:

```powershell
.\.venv\Scripts\python.exe scripts\train_catalog_classifier.py
```

## Estágio atual

- Fase 1: ambiente, protocolos de classificação, detecção e validação de imagem. O experimento E12 de transfer learning continua desenhado e não foi executado como avaliação independente.
- Fase 2.1: catálogo comercial, SQLite com preços em `Decimal` e motor estatístico. Amostra insuficiente permanece `DADOS_INSUFICIENTES`, sem classificação.
- Fase 2.2: 37 produtos e 117 imagens válidas. O dataset está marcado como incompleto.
- Demonstração: MobileNetV3-Large ajustado nas fotos de embalagem. Na fotografia de estúdio usada no teste local, a pontuação foi Arroz 0,710, Macarrão 0,178 e Leite UHT 0,073. Uma imagem de cada categoria do treino continuou na própria categoria. Isso não é acurácia de um conjunto separado.
- A suíte local tem 56 testes e terminou aprovada em 24 de outubro de 2026.

O detalhamento está em [`docs/FASE_2_2_RELATORIO.md`](docs/FASE_2_2_RELATORIO.md) e em [`docs/FASE_2_2_TRANSFER_LEARNING.md`](docs/FASE_2_2_TRANSFER_LEARNING.md).

## Equipe

- [Carlos E. O. Martins](https://github.com/carloseomartinsdev)
- [Ana Caroline Amorim](https://github.com/amorinana)
