# Visão geral

Trabalho final da disciplina Visão Computacional: Técnicas e Aplicações, em um curso de pós-graduação em Ciência de Dados. O sistema deve reconhecer produtos comerciais em imagem e informar se um preço encontrado está abaixo, dentro ou acima de uma referência calculada sobre registros históricos. A classificação é estatística. Ela não afirma que um estabelecimento pratica superfaturamento ilegal.

## Objetivo

O reconhecimento visual permanece organizado em quatro modelos:

| Modelo | Tarefa | Método |
| --- | --- | --- |
| A | Classificação da imagem inteira | MobileNetV3-Large |
| B | Classificação da imagem inteira | ResNet18 |
| C | Localização e classe | YOLO, implementação Ultralytics |
| D | Localização e classe | YOLO propõe a caixa; MobileNetV3-Large ou ResNet18 classifica o recorte |

MobileNetV3-Large é a variante padrão do Modelo A. A variante Small permanece disponível como alternativa de latência, fora da comparação principal, para não misturar duas capacidades no mesmo par.

O classificador do Modelo D será o mesmo peso obtido em A ou em B. A comparação com o YOLO passa a isolar a troca do rótulo da caixa, em vez de introduzir uma terceira rede.

A comparação de preço acrescenta um catálogo comercial, um banco SQLite, um motor estatístico e uma leitura inicial de etiquetas. O consumidor informa o produto e o preço; o sistema devolve a posição desse preço em relação à mediana dos registros válidos, ou informa que os dados não bastam.

## Fase 1

A fase 1 entregou a organização do projeto, o ambiente Python 3.12, a investigação do dataset público, o catálogo preliminar de classes do RPC, o protocolo do dataset próprio, os validadores, os notebooks preparatórios e a documentação metodológica. Esses componentes permanecem. Nenhum modelo foi treinado.

## Fase 2.1

Esta fase acrescenta a estrutura de comparação de preços sem iniciar treino nem download do RPC. O catálogo comercial ficou sem produtos naquela etapa. O banco não contém preços de mercado. Os testes usam valores sintéticos e os identificam como tal.

## Fase 2.2

A fase 2.2 abre o dataset brasileiro de cesta básica e o pipeline de transfer learning. Em 24 de outubro de 2026 o catálogo tem 37 produtos verificados no Open Food Facts, não os 50 pedidos, e as imagens válidas não chegam a 200. O estado está parcial. Os pesos ImageNet não foram baixados e o treino não rodou. O detalhe está em `docs/FASE_2_2_RELATORIO.md`.

## Decisões já fechadas

- O código usa caminhos relativos a partir da raiz do repositório e parâmetros em `configs/`.
- A semente padrão é 42.
- O dispositivo é CUDA quando o PyTorch enxerga uma GPU e CPU nos demais casos.
- Treino e inferência estão em módulos separados. As funções de treino recusam execução enquanto `experiments.run_training` for falso.
- Imagens, anotações volumosas e pesos ficam fora do Git.
- O subconjunto do RPC será definido e gravado antes do primeiro treino. O plano está em `configs/subset_plan.yaml` e ainda não está congelado.

## Como ler o restante

`02` situa os modelos na literatura. `03` descreve o RPC e a coleta própria, separados do catálogo brasileiro. `04` fixa partições e vazamento. `05` descreve os módulos. `06` e `07` definem os experimentos e as métricas de visão antes de qualquer número. `08` registra limites conhecidos. `09` propõe a sequência das fases seguintes. `10` a `15` descrevem catálogo, preços, estatística, OCR, fluxo do consumidor e confiabilidade das fontes. `FASE_2_2_CATALOGO`, `FASE_2_2_DATASET`, `FASE_2_2_TRANSFER_LEARNING` e `FASE_2_2_RELATORIO` registram a coleta parcial e o pipeline ainda sem treino.
