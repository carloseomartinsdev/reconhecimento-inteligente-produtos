# Métricas

Nenhuma métrica desta seção foi calculada sobre o RPC ou sobre fotografias próprias. Os testes unitários usam vetores e caixas construídos no próprio teste para verificar a implementação.

## Classificação

Para um conjunto de rótulos verdadeiros e previstos:

- Acurácia: proporção de acertos.
- Precisão da classe: verdadeiros positivos divididos pelos previstos dessa classe.
- Recall da classe: verdadeiros positivos divididos pelos exemplos dessa classe.
- F1 da classe: média harmônica de precisão e recall.
- Versões macro: média aritmética entre classes, sem ponderar pelo suporte. A média macro é a leitura principal porque o subconjunto pode continuar desbalanceado.
- Matriz de confusão: linhas são a classe verdadeira e colunas são a classe prevista, na ordem de `labels`.

Classes ausentes no suporte usam `zero_division=0` no scikit-learn, para a métrica existir mesmo quando uma classe não foi prevista. O suporte por classe acompanha o relatório.

## Detecção

Uma previsão é verdadeira positiva quando o IoU com uma anotação da mesma imagem, ainda não casada, atinge o limiar. O casamento é guloso, da maior confiança para a menor. Cada anotação casa no máximo uma vez.

- Precisão: verdadeiros positivos / (verdadeiros positivos + falsos positivos), em um limiar de confiança.
- Recall: verdadeiros positivos / anotações.
- AP: área sob a curva precision-recall depois do envelope que faz a precisão ser não crescente no recall. Implementação em `average_precision`.
- mAP: média das AP das classes que possuem ao menos uma anotação. Classe sem anotação fica de fora da média e não entra como zero.
- mAP@50: AP com IoU 0,5.
- mAP@50:95: média das AP nos limiares 0,50, 0,55, …, 0,95. Esse agregado será o do validador Ultralytics na fase experimental.

A função interna não aplica a interpolação de 101 pontos do COCO. Por isso o número experimental oficial do E3 e do E4 será o do Ultralytics, e a função interna permanece como verificação transparente em testes e em amostras pequenas. Os dois valores não devem ser colocados na mesma célula de tabela sem essa distinção.

O checkout automático dos autores também usa cAcc, ACD, mCCD e mCIoU, métricas de lista de compras. Elas não são o alvo principal deste trabalho. Podem ser calculadas depois, a partir das contagens por classe, se a avaliação de cena produzir uma lista. Enquanto isso, não entram no protocolo obrigatório.

## Custo

- Tempo de inferência: média de `repeats` chamadas depois de `warmup`, em segundos, com `time.perf_counter`.
- Tamanho em parâmetros: soma dos elementos dos tensores treináveis e não treináveis, e o equivalente em bytes pelo `element_size`.
- Tamanho em disco: bytes do arquivo de pesos, quando o arquivo existir.
- Ambiente: versão do Python, versão do PyTorch, dispositivo selecionado e nome da GPU quando houver.

Uma medição de tempo só é comparável dentro do mesmo equipamento e do mesmo tamanho de lote. O relatório experimental deve nomear a máquina.

## O que não é métrica do projeto

Uma passagem forward sobre um tensor de zeros confirma a forma `(1, número de classes)`. Um AP igual a 1 em uma caixa idêntica à anotação confirma o código. Nenhum dos dois estima o desempenho em produto comercial.

## Indicadores de preço

Quantidade, mínimo, máximo, média, mediana, desvio padrão populacional, quartis e diferenças percentuais estão definidos em `docs/12_analise_estatistica.md`. Os testes verificam essas contas em séries sintéticas. E7 a E11 ainda não produziram métrica experimental.
