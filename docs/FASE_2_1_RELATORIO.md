# Relatório da Fase 2.1

Data do fechamento: 24 de outubro de 2026. A fase evolui o projeto já existente. Não houve recriação do repositório, download do RPC nem treino.

## Alterações realizadas

O objetivo passou a incluir a comparação do preço informado com registros históricos, além do reconhecimento visual. A fase 1 permanece: ambiente Python 3.12.10, PyTorch em CPU, catálogo preliminar do RPC, esqueletos MobileNetV3-Large, ResNet18 e YOLO, oito notebooks, travas de treino e de download, e os testes originais.

Foram acrescentados o catálogo comercial, o esquema SQLite, o motor estatístico, o leitor inicial de etiquetas e o fluxo manual no Streamlit. O catálogo brasileiro e o banco de preços começam sem produtos e sem preços de mercado. A lista de 15 produtos continua aguardando aprovação. O exemplo de esquema não é um cadastro.

## Arquivos criados

- `src/database/__init__.py`, `models.py`, `schema.py`, `store.py`
- `src/catalog/__init__.py`, `identity.py`, `service.py`
- `src/pricing/__init__.py`, `money.py`, `statistics.py`, `policy.py`, `units.py`, `engine.py`
- `src/ocr/__init__.py`, `parse.py`, `preprocess.py`, `reader.py`
- `configs/pricing.yaml`
- `tests/test_commercial_prices.py`
- `tests/test_ocr_prices.py`
- `docs/10_catalogo_comercial.md`
- `docs/11_base_de_precos.md`
- `docs/12_analise_estatistica.md`
- `docs/13_ocr_etiquetas.md`
- `docs/14_fluxo_consumidor.md`
- `docs/15_fontes_e_confiabilidade.md`
- `data/brazilian_products/README.md`
- `data/brazilian_products/images/.gitkeep`
- `data/brazilian_products/labels/.gitkeep`
- `data/brazilian_products/metadata/exemplo_esquema.json`
- `data/brazilian_products/metadata/lista_aguardando_aprovacao.json`
- `data/prices/examples/README.md`
- `data/prices/imports/README.md`

## Arquivos modificados

- `app/streamlit_app.py` e `app/README.md`
- `configs/default.yaml` e `configs/experiments.yaml`
- `.gitignore`
- `requirements.txt` e `requirements.lock.txt` (`pytesseract==0.3.13`)
- `README.md`
- `docs/01_visao_geral.md`, `03_datasets.md`, `05_arquitetura.md`, `06_experimentos.md`, `07_metricas.md`, `08_limitacoes.md`, `09_cronograma.md`

Os módulos de classificação, detecção, híbrido, pré-processamento, avaliação e datasets da fase 1 não foram removidos. `experiments.run_training` e `experiments.run_download` permanecem falsos.

## Estrutura do banco

SQLite, com preço em `TEXT` canônico e cálculo em `Decimal`. Tabelas:

| Tabela | Conteúdo |
| --- | --- |
| `sources` | `manual`, `label_photo`, `consumer_report`, `authorized_public` |
| `products` | identidade comercial, código de barras opcional, imagem de referência e status |
| `establishments` | nome, cidade, UF, bairro opcional, identificador externo opcional e status |
| `price_records` | produto, estabelecimento, preço, data da observação, data de registro, fonte, tipo, condições e validação |
| `model_class_links` | associação entre classe de modelo e produto |

Tipos de preço: `regular`, `promotional`, `loyalty`, `other`. Validação: `pending`, `valid`, `invalid`. O arquivo `data/prices/market.sqlite` fica fora do Git. Abrir a interface cria o esquema. No fechamento, esse arquivo não continha produtos nem registros de preço; as quatro fontes são as únicas linhas semeadas pelo esquema.

## Funcionalidades implementadas e verificadas

- Cadastro, consulta, atualização, pesquisa, busca por identificador e por código de barras, e vínculo de classe de modelo.
- Identidade por marca, variante, quantidade e unidade, sem unir embalagens de tamanhos diferentes e sem gerar GTIN.
- Registro de estabelecimento com UF brasileira e registro de preço com origem, tipo e validação.
- Recusa de preço em `float`, vazio, inválido, negativo, zero ou com mais de duas casas.
- Média, mediana, quartis, desvio padrão populacional e diferenças percentuais em `Decimal`.
- Classificação pela mediana, com as faixas de `configs/pricing.yaml`.
- Retorno `DADOS_INSUFICIENTES` sem classificação quando faltam região, registros, estabelecimentos, atualidade ou preço regular. A região pedida não é ampliada.
- Separação entre preço da embalagem e preço por unidade, esta última só com confirmação e entre produtos comparáveis.
- Extração de candidatos monetários a partir de texto, com confiança nula e confirmação obrigatória.
- Leitor de imagem que valida o arquivo e, sem o executável Tesseract, devolve `mecanismo: indisponivel` e nenhum preço inventado.
- Interface com início, escaneamento, pesquisa, consulta e informações. O escaneamento avisa que não há modelo treinado e não escolhe classe. A consulta manual de um produto recém-cadastrado, com preço `5,49` e região Campinas/SP, exibiu `DADOS_INSUFICIENTES`, o preço da embalagem e a região `Campinas/SP`.

## Testes executados

Comando: `.\.venv\Scripts\python.exe -m pytest --tb=no -q`, na raiz do projeto, em 24 de outubro de 2026.

Resultado: 47 testes aprovados, nenhum com falha. Os 31 testes da fase 1 continuam na suíte. Os 16 novos estão em `tests/test_commercial_prices.py` (11) e `tests/test_ocr_prices.py` (5). Cobrem identidade, cadastro, estabelecimento, preços inválidos e negativos, média, mediana, quartis, diferenças percentuais, limites de classificação, ausência de registros, dados desatualizados, promoção, comparação por unidade, normalização de OCR e o fluxo manual com o texto `R$ 5,49` confirmado antes da comparação. Os valores são sintéticos e ficam em banco temporário.

A interface foi exercida com `streamlit.testing.v1.AppTest`: navegação das cinco páginas, aviso de ausência de modelo na página de escaneamento, cadastro manual e comparação com amostra vazia. Não houve verificação em navegador gráfico; o servidor de browser da sessão não estava disponível. O processo Streamlit antigo da fase 1, na porta 8501, foi reiniciado ao final para carregar o fluxo novo.

## Limitações

- Não há modelo treinado e a interface não simula reconhecimento.
- Não há 15 produtos aprovados, fotografias brasileiras nem anotações.
- Não há série real de preços. A classificação obtida nos testes não descreve o mercado.
- O executável Tesseract não está instalado. O pacote Python `pytesseract` está. E7 não foi executado.
- E1 a E11 estão desenhados e sem resultado.
- O RPC não foi baixado e não é usado como fonte de preço.
- A política padrão ainda não pondera as fontes entre si; ela preserva a origem e usa só registros válidos e, por padrão, regulares.
- O rótulo “Dentro da média” é o nome da faixa central. A conta que escolhe a faixa usa a mediana.

## Pendências

- Aprovar a lista de 15 produtos antes de fotografar.
- Definir o protocolo de coleta de preços em fonte autorizada.
- Instalar o Tesseract e montar um conjunto rotulado de etiquetas para o E7.
- Treinar somente depois das partições, em fase posterior.
- Decidir a migração para PostgreSQL quando o SQLite deixar de bastar.

## Recomendações para a Fase 2.2

1. Fechar os 15 produtos com marca, variante, quantidade e unidade. Não inventar código de barras.
2. Fotografar segundo `data/custom/protocol.md` e gravar o manifesto antes de qualquer treino.
3. Coletar preços com fonte, data, estabelecimento, tipo e validação. Não raspar sites comerciais.
4. Manter dados sintéticos apenas em teste e não publicá-los como preço praticado.
5. Instalar o Tesseract e só então medir o E7. Até lá, a confirmação manual permanece obrigatória.
6. Executar E8, E9 e E10 em séries reais quando elas existirem, sem trocar a referência para a média antes de ver o experimento.
7. No E11, anotar em separado erro visual, erro de OCR, erro de associação comercial e erro estatístico.
8. Manter `run_training` e `run_download` desligados até a autorização explícita de cada um. O RPC, se for baixado, continua separado dos preços brasileiros.
9. Conservar o aviso de que a faixa estatística não apura superfaturamento ilegal.
