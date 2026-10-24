# Arquitetura do software

O código de experimento fica em `src/` e entra no `PYTHONPATH` pelos testes e pelos notebooks. Configuração, dado e peso ficam fora dos módulos.

```text
configs/          YAML de caminhos, modelos, experimentos e plano de subconjunto
src/datasets/     catálogo, referência publicada do RPC, manifesto e vazamento
src/preprocessing validação de arquivo, CLAHE, letterbox e transformações
src/classification  MobileNetV3-Large, ResNet18, inferência e trava de treino
src/detection/    plano YOLO e carga apenas de peso local
src/hybrid/       expansão de caixa, recorte e fusão de escores
src/evaluation/   métricas, anotações COCO/YOLO e tempo
src/catalog/      identidade comercial e cadastro de produtos
src/database/     esquema SQLite e persistência
src/pricing/      valores decimais, estatística e classificação
src/ocr/          pré-processamento e candidatos monetários
scripts/          download condicionado, catálogo e inspeção
app/              fluxo manual do consumidor no Streamlit
notebooks/        roteiros preparatórios da visão computacional
```

## Fluxo previsto

1. O manifesto aponta cada arquivo, sua origem, sua classe e seu grupo de captura.
2. O validador de imagem confirma leitura pelo Pillow e decodificação pelo OpenCV.
3. O validador de anotação confere categorias, imagens e caixas antes de qualquer treino de detector.
4. A partição é gravada em `data/splits/` e a checagem de vazamento precisa passar.
5. O treino, na fase seguinte, lê essa partição e grava pesos em `models/` e métricas em `results/metrics/`.
6. A inferência carrega um peso existente. Ela não dispara download.

## Modelos no código

`build_classifier` constrói MobileNetV3-Large ou ResNet18 com a cabeça trocada. `pretrained=False` é o padrão da fase 1 e não baixa pesos ImageNet. A fase experimental pode passar `pretrained=True`; esse download é pequeno e distinto do RPC, e deve ser registrado.

`load_local_yolo` abre um arquivo `.pt` somente se ele já estiver no disco. O nome de arquitetura planejado é `yolo11n`. O Ultralytics 8.4.186 instalado nesta fase também traz a família YOLO26. Ela não entra no protocolo inicial: trocar de família depois de ver resultado seria outro experimento. Se a fase 2 adotar YOLO26, a troca precisa ser registrada antes do primeiro treino.

`crop_hwc` recorta em coordenadas xyxy, com margem relativa à caixa e corte nos limites da imagem. `fuse_scores` multiplica as duas confianças.

## Catálogo, banco e preços

`catalog.identity` forma a chave comercial com marca, variante, quantidade e unidade. Quantidades diferentes não são unificadas. `catalog.service` cadastra, consulta, atualiza, pesquisa e associa uma classe de modelo a um produto.

`database.store` grava produtos, estabelecimentos, fontes e registros de preço em SQLite. O preço é `TEXT` no formato decimal canônico. A aplicação só calcula com `Decimal`. A migração futura para PostgreSQL troca a conexão e o tipo da coluna por `NUMERIC`; o marcador de parâmetro desta etapa continua `?`.

`pricing.engine` filtra a região pedida, a idade, o status de validação e, por padrão, os preços que não são regulares. Se a amostra não atende `configs/pricing.yaml`, o status é `DADOS_INSUFICIENTES` e não há classificação. A região não é ampliada. A comparação por R$/kg, R$/L ou R$/unidade só ocorre quando o usuário a confirma e os produtos compartilham marca, variante e unidade de base.

`ocr.reader` valida a imagem, pré-processa com OpenCV e, se o executável Tesseract existir, pede o texto ao `pytesseract`. A confiança fica nula quando o mecanismo não a fornece. Todo candidato exige confirmação. Um número na imagem não é, por si, o preço do produto reconhecido.

## Interface

`app/streamlit_app.py` abre Início, Escanear produto, Pesquisar produto, Consultar preços e Informações sobre o projeto. A página de escaneamento valida arquivo ou câmera e avisa que não há modelo treinado; a classe não é simulada. O restante do fluxo usa a seleção manual do catálogo, o preço digitado ou o texto da etiqueta, e o relatório do motor. A página de informações continua a informar que não há métrica experimental de visão.

## Testes

Os testes em `tests/` cobrem a fase 1 — configuração, semente, catálogo do RPC, vazamento, imagem sintética, anotação sintética, pré-processamento, forma da saída dos dois classificadores, travas de treino, a recusa de um peso YOLO ausente e métricas sobre vetores conhecidos — e a fase 2.1: identidade comercial, cadastro, estabelecimentos, preços inválidos, estatística, limites, amostra insuficiente, promoção, comparação por unidade, normalização de OCR e o fluxo manual com texto confirmado. Os valores monetários dos testes são sintéticos. Eles não leem o RPC nem uma série real de mercado.
