# Relatório acadêmico — reconhecimento de produtos por imagem

## Resumo

Este trabalho aplica visão computacional à identificação da categoria de embalagens de alimentos. As fotografias vêm do Open Food Facts. O experimento treina duas redes pré-treinadas no ImageNet, MobileNetV3-Large e ResNet18, em duas etapas: extração de características e fine-tuning parcial. A seleção do modelo usa somente o F1 macro da validação. No teste, separado por grupos de origem, a etapa A do MobileNetV3-Large alcançou acurácia 0,727 e F1 macro 0,646 em 11 imagens. O estudo é exploratório, em ambiente controlado, e não mede desempenho de gôndola.

## 1. Introdução

Reconhecer um produto comercial pela fotografia da embalagem é uma tarefa de classificação de imagens. O rótulo visual concentra marca, cor e forma da embalagem. Uma rede convolucional pode aprender essas pistas a partir de exemplos, desde que as imagens de treino e de avaliação não sejam a mesma fotografia repetida.

O aplicativo do projeto recebe uma foto, indica a categoria e consulta preços demonstrativos no SQLite. A comparação de preços é complementar. O objeto da avaliação é o classificador visual.

## 2. Objetivos

### Objetivo geral

Demonstrar, com um conjunto real e pequeno, o uso de transfer learning para classificar categorias de produtos alimentícios a partir de fotografias de embalagens.

### Objetivos específicos

- Documentar a base experimental e as suas limitações.
- Aplicar pré-processamento e aumento moderado de dados.
- Treinar MobileNetV3-Large e ResNet18 com pesos do ImageNet.
- Comparar extração de características e fine-tuning parcial.
- Avaliar acurácia, precisão, recall, F1 macro e matriz de confusão em um conjunto não usado na escolha do modelo.
- Manter uma demonstração local no Streamlit.

## 3. Fundamentação teórica

Visão computacional trata a imagem como dado de entrada e produz uma decisão, aqui a categoria da embalagem.

Redes neurais convolucionais aplicam filtros locais e reduzem a imagem a um vetor de características. Esse vetor alimenta uma camada classificadora.

Transfer learning reaproveita um modelo treinado em outro problema. Os pesos iniciais deste experimento são os do ImageNet, distribuídos pelo torchvision.

Na extração de características o extrator permanece congelado. Só a cabeça classificadora, redimensionada para as categorias do estudo, recebe gradiente. O custo é menor e o risco de apagar o que a rede já sabia é menor.

No fine-tuning algumas camadas finais voltam a treinar, com taxa de aprendizado menor. A rede pode se ajustar ao domínio novo. Com poucas imagens, também pode memorizar o treino.

Data augmentation aplica transformações leves só durante o treino, para o modelo não depender de um enquadramento único. A embalagem precisa continuar reconhecível.

Classificação de imagens, neste trabalho, atribui uma categoria a cada fotografia. A saída é uma distribuição softmax sobre as categorias.

## 4. Metodologia

### Origem do dataset

O catálogo foi coletado no Open Food Facts em 24 de outubro de 2026, licença CC BY-SA. Há 37 produtos validados e 117 imagens aceitas na validação técnica. Onze categorias estavam previstas no catálogo. Nove aparecem com imagem utilizável. Leite em pó e sal não entraram no experimento porque não há fotos de frente aproveitáveis.

Quarenta e duas imagens de verso, ingredientes ou tabela nutricional foram excluídas do experimento. Os arquivos originais permanecem no manifesto. Nenhuma imagem foi substituída por dado fictício. O resumo está em `results/metrics/dataset_summary.json`.

| Grandeza | Valor |
|---|---:|
| Imagens utilizáveis | 77 |
| Produtos | 37 |
| Categorias | 9 |
| Resolução média | 565 × 755 px |
| Imagens excluídas do experimento | 42 |
| Categoria com menos de 4 imagens | Manteiga (2) |

### Pré-processamento

A imagem é convertida para RGB. No treino ela é redimensionada para 110% de 224, rotacionada em até 12 graus, tem brilho e contraste alterados em até 0,15, sofre translação de até 4% e escala entre 0,92 e 1,08, e depois é recortada em 224 × 224. A conversão para tensor e a normalização usam a média e o desvio do ImageNet: (0,485, 0,456, 0,406) e (0,229, 0,224, 0,225).

Validação, teste e o aplicativo usam apenas redimensionamento para 224 × 224, tensor e a mesma normalização. O aumento não gera arquivos novos.

### Divisão dos dados

A divisão `academico-grupos-s42` usa a semente 42. O grupo é o par código de barras e identificador da imagem original. Fotos derivadas do mesmo original ficam no mesmo conjunto. Dentro de cada categoria, cerca de 15% dos grupos vai ao teste, 15% à validação e o restante ao treino, desde que existam ao menos três grupos.

| Conjunto | Imagens |
|---|---:|
| Treino | 54 |
| Validação | 12 |
| Teste | 11 |

Manteiga tem dois grupos. Um ficou no treino e outro na validação. Não há imagem de teste dessa categoria. Os identificadores estão em `data/splits/`.

### Arquiteturas

MobileNetV3-Large é o modelo principal. ResNet18 é a comparação. Os dois carregam `MobileNet_V3_Large_Weights.DEFAULT` e `ResNet18_Weights.DEFAULT`.

Na etapa A o extrator fica congelado e a cabeça passa a ter nove saídas. Na etapa B o MobileNetV3-Large descongela os três últimos blocos e o ResNet18 descongela a `layer4`. A etapa B continua dos melhores pesos da etapa A da mesma arquitetura.

### Treinamento

| Parâmetro | Valor |
|---|---|
| Imagem | 224 × 224 |
| Lote | 8 |
| Épocas máximas | 20 |
| Otimizador | AdamW |
| Taxa da cabeça na etapa A | 0,001 |
| Taxa na etapa B | 0,0001 |
| Parada antecipada | 5 épocas sem melhora do F1 macro de validação |
| Semente | 42 |
| Dispositivo | CPU |

O checkpoint escolhido é o de maior F1 de validação entre as quatro corridas. O teste não entra nessa escolha. A fotografia de demonstração de arroz, usada num treino anterior do aplicativo, não entra neste experimento. O arquivo `models/brazilian/classifier.pt` permanece como esse checkpoint de demonstração. O arquivo experimental escolhido é `models/brazilian/experiment_best.pt`.

O arquivo `configs/transfer.yaml` continua com `run_training: false` e `num_classes: 50`. Esses valores descrevem a trava da fase anterior. O experimento acadêmico é o script `scripts/run_academic_experiment.py` e usa as nove categorias representadas.

### Avaliação

Para cada corrida o script calcula, no teste, acurácia, precisão macro, recall macro e F1 macro sobre as categorias presentes. Também grava a perda e a acurácia de treino e de validação, a matriz de confusão com todas as categorias, o tempo de treino, o tempo médio de inferência e a quantidade de parâmetros treináveis.

## 5. Resultados

A execução ocorreu em 24 de outubro de 2026, em Windows, Python 3.12.10, PyTorch 2.14.1+cpu e torchvision 0.29.1+cpu. O relógio da execução completa, incluindo o download dos pesos do ResNet18, foi de 140 segundos.

| Modelo | Etapa | Acurácia | Precisão | Recall | F1 | F1 validação | Treino (s) | Inferência (s) | Parâmetros treináveis |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MobileNetV3-Large | A | 0,727 | 0,625 | 0,688 | 0,646 | 0,867 | 46,1 | 0,0294 | 1.241.609 |
| MobileNetV3-Large | B | 0,545 | 0,333 | 0,438 | 0,375 | 0,811 | 20,8 | 0,0307 | 2.991.849 |
| ResNet18 | A | 0,364 | 0,113 | 0,250 | 0,155 | 0,323 | 33,3 | 0,0431 | 4.617 |
| ResNet18 | B | 0,455 | 0,354 | 0,500 | 0,396 | 0,222 | 25,0 | 0,0436 | 8.398.345 |

O modelo escolhido pela validação foi MobileNetV3-Large, etapa A, na época 20, com F1 de validação 0,867. O F1 de teste correspondente é 0,646. Oito das onze imagens de teste foram classificadas corretamente.

Erros desse checkpoint no teste:

- uma das duas fotos de Arroz foi para Farinhas e flocão;
- a foto de Açúcar foi para Arroz;
- a foto de Feijão foi para Farinhas e flocão.

Café, Farinhas e flocão, Leite UHT, Macarrão e Óleo de soja acertaram as imagens que tinham no teste. Manteiga não tinha imagem de teste.

As curvas, a matriz e a comparação estão em `results/figures/`. A tabela completa está em `results/metrics/model_comparison.csv`.

## 6. Discussão

A maior acurácia e o maior F1 de teste foram da etapa A do MobileNetV3-Large. A distância para a etapa A do ResNet18 também aparece na validação (0,867 contra 0,323). Não é uma diferença de poucas casas decimais. Ainda assim, onze imagens de teste tornam o valor absoluto instável: cada erro vale cerca de nove pontos de acurácia.

O maior tempo de treino foi o da etapa A do MobileNetV3-Large, 46,1 segundos, porque ela percorreu as 20 épocas. O menor tempo médio de inferência foi o dessa mesma corrida, 0,0294 segundos por imagem, à frente das duas corridas do ResNet18.

O fine-tuning não melhorou o critério de seleção. O F1 de validação caiu 0,056 no MobileNetV3-Large e 0,101 no ResNet18. No ResNet18 o F1 de teste subiu ao mesmo tempo em que o de validação caiu. Essa discordância é esperada com doze imagens de validação e onze de teste, e é exatamente o motivo de não escolher o modelo pelo teste.

No MobileNetV3-Large a acurácia de treino chegou a 1,0 enquanto a de validação ficou em 0,92 na melhor época. Há folga para sobreajuste. A etapa B piorou o teste, o que combina com uma cabeça que já havia decorado o treino pequeno.

Para o ambiente controlado do projeto, a etapa A do MobileNetV3-Large é a arquitetura mais adequada entre as quatro corridas: melhor validação, inferência mais rápida e execução em CPU. Isso não a torna superior em qualquer outro catálogo.

## 7. Limitações

- A base é pequena: 77 imagens utilizáveis, 54 no treino.
- O ambiente é controlado. As fotos são de catálogo, não de gôndola.
- A diversidade visual é baixa. Vários produtos têm uma única foto de frente.
- O treino atinge acurácia alta e a validação não acompanha no mesmo ritmo.
- Manteiga não tem teste. O F1 macro ignora essa categoria na conta principal e a matriz mostra a linha vazia.
- Não houve validação em loja, iluminação variável ou produtos fora do catálogo.
- Os preços do aplicativo são demonstrativos.

## 8. Conclusão

O trabalho mostra um fluxo verificável de visão computacional: imagens reais, pré-processamento compatível com ImageNet, aumento moderado, duas redes pré-treinadas, duas etapas de treino e métricas num conjunto separado. O melhor resultado desta divisão foi a extração de características com MobileNetV3-Large. O fine-tuning parcial não melhorou a validação. O número obtido no teste descreve onze fotografias e não autoriza uma afirmação de prontidão comercial.

## 9. Referências

- Howard, A. et al. Searching for MobileNetV3. In: ICCV, 2019. https://arxiv.org/abs/1905.02244
- He, K. et al. Deep Residual Learning for Image Recognition. In: CVPR, 2016. https://arxiv.org/abs/1512.03385
- Russakovsky, O. et al. ImageNet Large Scale Visual Recognition Challenge. International Journal of Computer Vision, 2015. https://arxiv.org/abs/1409.0575
- Loshchilov, I.; Hutter, F. Decoupled Weight Decay Regularization. In: ICLR, 2019. https://arxiv.org/abs/1711.05101
- PyTorch. Documentação. https://pytorch.org/docs/stable/index.html
- Torchvision. Modelos de classificação. https://pytorch.org/vision/stable/models.html
- Open Food Facts. Termos de uso. https://world.openfoodfacts.org/terms-of-use
