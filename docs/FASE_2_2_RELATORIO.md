# Relatório da Fase 2.2

Data: 24 de outubro de 2026. O projeto anterior foi mantido. O estado desta fase é **parcial**: o catálogo não chegou a 50 produtos e o conjunto de imagens não chegou a 200 arquivos válidos. Houve um ajuste demonstrativo de categoria, descrito abaixo. Ele não é o experimento E12 e não mede generalização.

## Produtos

Definidos e validados comercialmente a partir do Open Food Facts: **37**. A tabela está em `docs/FASE_2_2_CATALOGO.md`.

Não validados por falta de retorno da fonte, depois de HTTP 500 na segunda consulta:

- Feijão: 4 de 6.
- Café: 3 de 6.
- Leite em pó: 0 de 4.
- Óleo de soja: 2 de 4.
- Sal: 0 de 2.

## Imagens

- Obtidas e registradas no manifesto: 119.
- Aceitas na validação técnica: 117.
- Rejeitadas na validação: 1 por resolução insuficiente e 1 por duplicata visual.
- Rejeitadas no download: 0.
- Produtos com o mínimo de 4 imagens válidas: 14 de 37.
- Licença verificada: CC BY-SA do Open Food Facts, com a ressalva de direitos de terceiros na embalagem.

## Fontes

Somente Open Food Facts. Não houve scraping de loja. Os conectores de preço em `src/pricing/connectors.py` descrevem uma atualização futura e recusam a execução comercial.

## Transfer learning

O pipeline da etapa A, da etapa B, do aumento só no treino, da divisão por grupo de origem e da comparação com embeddings está implementado e documentado em `docs/FASE_2_2_TRANSFER_LEARNING.md`. `experiments.run_training` continua falso, então a trava de E12 segue fechada: o relatório do dataset tem `completo: false`.

Fora dessa trava, a pedido de fazer o escaneamento funcionar com as fotos existentes, `scripts/train_catalog_classifier.py` ajustou o MobileNetV3-Large. Os pesos ImageNet já estavam em cache e foram reutilizados. O arquivo ficou em `models/brazilian/classifier.pt`. Nas fotos do catálogo sozinhas, a foto de estúdio enviada não ficava em Arroz (o melhor ponto chegou a Farinhas e flocão 0,582 e Arroz 0,243). A mesma foto entrou então como exemplo de Arroz e só a camada final foi ajustada por mais quatro épocas. Nessa foto, a pontuação final foi Arroz 0,710, Macarrão 0,178 e Leite UHT 0,073. Uma imagem de cada categoria do treino continuou na própria categoria (9 de 9). Isso mostra que o fluxo de escaneamento responde; não é acurácia de um conjunto separado.

## Interface

O Streamlit importa o catálogo validado para o SQLite. Na abertura, grava cinco preços de teste por produto, com a condição da oferta informando que não são coleta de mercado. O arquivo `models/brazilian/classifier.pt` e as fotos do catálogo acompanham o repositório, e a tela de escanear mostra a categoria, a imagem de referência e o preço.

## Testes

`.\.venv\Scripts\python.exe -m pytest --tb=line -q` terminou com 56 testes aprovados e nenhum com falha, em 24 de outubro de 2026. Os testes usam dados sintéticos, não os produtos coletados.

## Limitações

- Quatro ou cinco fotos públicas não medem generalização. A divisão exploratória existe e não foi usada para produzir acurácia.
- O conteúdo de cada foto não foi revisado um a um.
- Cappuccino, farinha de coco e farinha de aveia entraram pelos filtros de categoria. A aderência à cesta básica desses três é limitada e está anotada no catálogo.
- O código `00948906` é o valor publicado pela fonte.
- PostgreSQL e a coleta automática de preços continuam fora desta fase.

## Pendências

- Completar feijão, café, leite em pó, óleo de soja e sal quando a fonte responder, sem trocar de origem.
- Revisar visualmente as embalagens antes de qualquer treino.
- Autorizar, se for o caso, o download dos pesos ImageNet.
- Fotografar um conjunto próprio em condições reais.
- Só então executar E12.
