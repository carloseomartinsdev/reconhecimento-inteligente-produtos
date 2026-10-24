# Reconhecimento inteligente de produtos comerciais

Projeto da disciplina de Visão Computacional: Técnicas e Aplicações, em um contexto de pós-graduação/MBA em Ciência de Dados. O aplicativo recebe a fotografia de uma embalagem, indica a categoria e mostra os produtos parecidos do catálogo com os preços registrados no banco local.

**Status: aplicativo de escaneamento em funcionamento**

## Objetivo

Identificar a categoria de um produto de cesta básica a partir da imagem da embalagem e consultar o preço correspondente no catálogo comercial.

## Dataset

- Catálogo comercial brasileiro coletado no [Open Food Facts](https://world.openfoodfacts.org/)
- Licença das fotografias: CC BY-SA
- Termos: https://world.openfoodfacts.org/terms-of-use
- 37 produtos validados e 117 imagens aceitas na validação técnica
- Manifesto: `data/brazilian_products/metadata/image_manifest.csv`
- Descrição do catálogo: [`docs/FASE_2_2_CATALOGO.md`](docs/FASE_2_2_CATALOGO.md) e [`docs/FASE_2_2_DATASET.md`](docs/FASE_2_2_DATASET.md)

O protocolo de visão computacional também considera o Retail Product Checkout, publicado em https://rpc-dataset.github.io/ sob a licença CC BY-NC-SA 4.0.

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
│   ├── brazilian_products/
│   └── prices/
├── docs/
├── notebooks/
├── scripts/
├── src/
└── tests/
```

## Instalação

Os comandos abaixo assumem Windows e PowerShell, a partir da pasta do projeto.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

As versões resolvidas nesta instalação estão em `requirements.lock.txt`.

## Como executar

A aplicação abre em http://localhost:8501, direto na tela de escanear.

```powershell
.\.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

Na abertura, o catálogo validado entra no SQLite e cada produto recebe preços de demonstração. O banco fica em `data/prices/market.sqlite`.

Testes:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Treino do classificador de categoria com as fotos do catálogo:

```powershell
.\.venv\Scripts\python.exe scripts\train_catalog_classifier.py
```

## Estágio atual

- Ambiente de visão computacional com MobileNetV3-Large, ResNet18 e o fluxo de detecção preparado nos notebooks `01` a `08`.
- Catálogo comercial, banco SQLite e comparação estatística de preços.
- Classificador de categoria treinado nas embalagens coletadas e ligado à tela de escanear.
- Aplicativo com as seções Escanear, Buscar, Preços e Sobre.
- 56 testes aprovados em 24 de outubro de 2026.

A documentação das fases está em [`docs/FASE_2_1_RELATORIO.md`](docs/FASE_2_1_RELATORIO.md), [`docs/FASE_2_2_RELATORIO.md`](docs/FASE_2_2_RELATORIO.md) e [`docs/FASE_2_2_TRANSFER_LEARNING.md`](docs/FASE_2_2_TRANSFER_LEARNING.md).

## Equipe

- [Carlos E. O. Martins](https://github.com/carloseomartinsdev)
- [Ana Caroline Amorim](https://github.com/amorinana)
