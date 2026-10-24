# Experimentos

Os experimentos E1 a E6, de visão computacional, e E7 a E11, de preço e fluxo, estão desenhados e ainda não foram executados. Não há tabela de resultado neste documento. Os fatores estão também em `configs/experiments.yaml`, com `status: desenhado` nos experimentos novos.

## E1 — MobileNetV3-Large e ResNet18

Protocolo P-CLS-exemplar. As duas arquiteturas recebem a mesma partição, o preset `baseline_imagenet`, a semente 42, o mesmo número máximo de épocas e a mesma decisão sobre pesos ImageNet. A leitura usa acurácia, precisão, recall e F1 macro, além da matriz de confusão. A matriz é o lugar em que embalagens da mesma metacategoria devem aparecer se a confusão for fina.

O tamanho do modelo e o tempo de inferência entram no relatório do E1 como descrição do custo, não como critério para descartar o modelo mais lento sem mostrar o F1.

## E2 — Pré-processamento

Uma arquitetura fica escolhida depois do E1 e permanece fixa. Variam apenas os presets: `baseline_imagenet`, `letterbox`, `clahe`, `equalize` e `identity_scale`. A métrica principal é o F1 macro no mesmo conjunto de validação. Se a diferença ficar dentro da variação de uma repetição com outra semente, o relatório deve dizer isso; uma única corrida não sustenta preferência forte.

## E3 — YOLO

Protocolo P-DET-checkout, arquitetura nano, imagens de 640 px. Métricas: mAP@50, mAP@50:95, precisão e recall no limiar de confiança do validador, tempo de inferência e tamanho do arquivo de pesos. Se a densidade estiver recuperável nos nomes ou no JSON, o mAP também sai separado em easy, medium e hard.

Um ensaio secundário, se houver tempo, treina o mesmo YOLO só com exemplares e avalia no checkout, para observar o deslocamento de domínio descrito pelos autores. Esse número não substitui o E3 principal.

## E4 — YOLO e híbrido

As mesmas imagens e as mesmas caixas propostas pelo detector. No híbrido, o rótulo da caixa é substituído pela CNN e a confiança combinada segue a regra do config. Reporta-se mAP das duas saídas e a acurácia da CNN nos recortes cuja caixa casa com a anotação em IoU de pelo menos 0,5. O tempo do híbrido inclui o recorte e a segunda rede.

A CNN do híbrido é o Modelo A ou o Modelo B já treinado. Ela não é retreinada nas imagens de teste.

## E5 — Robustez

Sobre o dataset próprio, a acurácia e o F1 macro são estratificados por ângulo, distância, iluminação e fundo. Nas cenas, o mAP@50 é estratificado por densidade. Células com poucas imagens são mostradas com o suporte ao lado da métrica. Sem suporte, a célula não vira conclusão.

## E6 — Generalização entre origens

`correspondence_status` lê o mapeamento de classes. Sem correspondência utilizável, o experimento produz duas avaliações fechadas: modelos treinados e testados no subconjunto público, e modelos treinados e testados nas fotos próprias. Não há acurácia cruzada nesse caso.

Se alguma linha for marcada `exact` ou `visual_similar` com evidência, a avaliação cruzada fica restrita a essas classes. O restante continua separado. O relatório precisa publicar a lista dos pares aceitos.

## E7 — Precisão do OCR

Avaliar a extração de valores em fotografias de etiquetas, separando candidato correto, candidato ausente e texto que não é preço. A taxa de confirmação manual entra no registro. Enquanto o executável Tesseract não estiver instalado, o experimento não tem o que medir: o leitor devolve mecanismo indisponível e não inventa texto.

## E8 — Média versus mediana

Investigar, sobre séries sintéticas e depois sobre séries reais, o quanto um valor extremo muda a média e deixa a mediana estável, e se a classificação mudaria caso a referência fosse a média. A referência adotada no motor é a mediana. Este experimento não substitui essa escolha antes de ser executado.

## E9 — Atualização dos preços

Variar a idade máxima dos registros e observar o tamanho da amostra e a mudança de classificação. Um registro antigo não entra na comparação quando ultrapassa o limite configurado.

## E10 — Qualidade da comparação

Variar a quantidade de registros, o número de estabelecimentos e a presença de preços promocionais. A taxa de `DADOS_INSUFICIENTES` é uma saída prevista, não uma falha a esconder.

## E11 — Fluxo integrado

Percorrer imagem, produto, preço e comparação, anotando em separado erro de reconhecimento visual, erro de leitura de preço, erro de associação comercial e erro de cálculo estatístico. Sem modelos treinados, a perna visual deste experimento ainda não pode ser medida. O fluxo manual, com produto escolhido pelo usuário, não conta como reconhecimento.

## Registro de cada corrida

Cada execução futura grava a configuração resolvida, a semente, o identificador da partição, o dispositivo, as versões dos pacotes e o caminho do peso. O JSON de métricas só é escrito ao final de uma avaliação real e passa a aparecer na página Streamlit.
