# Reconhecimento inteligente de produtos comerciais

Projeto da disciplina de Visão Computacional: Técnicas e Aplicações, em um contexto de pós-graduação/MBA em Ciência de Dados. O aplicativo recebe a fotografia de uma embalagem, indica a categoria e mostra os produtos parecidos do catálogo com os preços registrados no banco local.

**Status: demonstração acadêmica em funcionamento, com experimento de transfer learning registrado**

## Objetivo

Identificar a categoria de um produto de cesta básica a partir da imagem da embalagem e consultar o preço correspondente no catálogo comercial.

## Dataset

- Catálogo comercial brasileiro coletado no [Open Food Facts](https://world.openfoodfacts.org/)
- Licença das fotografias: CC BY-SA
- Termos: https://world.openfoodfacts.org/terms-of-use
- 37 produtos validados e 117 imagens aceitas na validação técnica
- O experimento usa 77 imagens de frente ou de embalagem, em 9 categorias. É um estudo exploratório, em ambiente controlado, com a base pequena de propósito
- Manifesto: `data/brazilian_products/metadata/image_manifest.csv`
- Resumo medido: `results/metrics/dataset_summary.json`
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
│   ├── prices/
│   └── splits/
├── docs/
├── models/
│   └── brazilian/
├── notebooks/
├── results/
│   ├── figures/
│   └── metrics/
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

A aplicação abre em http://localhost:8501, direto na tela de escanear. As fotos do catálogo acompanham o projeto. A tela usa `models/brazilian/experiment_best.pt`, escolhido pelo F1 de validação. O arquivo `models/brazilian/classifier.pt` permanece como o checkpoint anterior de demonstração.

```powershell
.\.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

Na abertura, o catálogo validado entra no SQLite e cada produto recebe preços de demonstração. O banco fica em `data/prices/market.sqlite`.

Testes:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Experimento acadêmico, com MobileNetV3-Large e ResNet18, etapas de extração de características e fine-tuning:

```powershell
.\.venv\Scripts\python.exe scripts\run_academic_experiment.py
```

O notebook `notebooks/09_experimento_final.ipynb` lê os resultados já gravados. A métrica comparativa fica em `results/metrics/model_comparison.csv`.

O script `scripts/train_catalog_classifier.py` continua disponível para a demonstração anterior e não é o protocolo do experimento.

## Estágio atual

- MobileNetV3-Large e ResNet18 treinados com pesos ImageNet. A etapa A do MobileNetV3-Large foi a escolhida pela validação.
- Catálogo comercial, banco SQLite e preços demonstrativos.
- Aplicativo com as seções Escanear, Buscar, Preços e Sobre.
- 61 testes aprovados em 24 de outubro de 2026.

O relatório do experimento está em [`docs/RELATORIO_ACADEMICO_FINAL.md`](docs/RELATORIO_ACADEMICO_FINAL.md). O registro das correções está em [`docs/CORRECOES_ACADEMICAS_RELATORIO.md`](docs/CORRECOES_ACADEMICAS_RELATORIO.md). A documentação das fases anteriores permanece em [`docs/FASE_2_1_RELATORIO.md`](docs/FASE_2_1_RELATORIO.md) e [`docs/FASE_2_2_RELATORIO.md`](docs/FASE_2_2_RELATORIO.md).

## Equipe

- [Carlos E. O. Martins](https://github.com/carloseomartinsdev)
- [Ana Caroline Amorim](https://github.com/amorinana)
