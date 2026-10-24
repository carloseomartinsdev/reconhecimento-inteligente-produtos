# Limitações

## Dados que ainda não estão no disco

As 83.739 imagens publicadas não foram contadas localmente. Qualquer diferença entre o pacote obtido no futuro e as tabelas da página oficial precisa ser registrada antes do treino. O formato JPEG, a codificação da densidade no nome do arquivo e os nomes comerciais em chinês dependem dessa leitura.

## Catálogo preliminar

Os 200 nomes em `rpc_classes.csv` vêm de um espelho, não do JSON oficial. A intercalação entre `drink` e `alcohol` e o rótulo do SKU 21 podem mudar na conferência. Até lá, o catálogo serve para planejamento e para os testes de integridade, não para afirmar a taxonomia fina do artigo.

## Licença e espelho

A licença adotada é a CC BY-NC-SA 4.0 da página oficial. O metadado `cc-by-nc-sa-2.0` visto no cartão do Hugging Face contradiz o texto do próprio cartão e não foi usado. O projeto não redistribui as imagens.

## Domínio

Exemplar e checkout diferem em resolução, fundo, número de objetos, oclusão e iluminação de captura. Um classificador treinado no exemplar não é, por isso, um classificador de cena. O desenho experimental separa as duas perguntas. Juntá-las numa única acurácia tornaria o número impossível de interpretar.

O ensaio curto publicado na *Science China Information Sciences* menciona três condições de iluminação nas imagens de checkout. A construção detalhada no arXiv e a contagem de 30.000 imagens não mostram três arquivos por arranjo: 10.000 imagens por densidade já fecham o total. Não dá para afirmar, com as fontes lidas, que cada cena tenha três exposições. Isso fica em aberto até os arquivos.

## Fine-grained e subconjunto

Vinte SKUs, se o plano de subconjunto for mantido, não representam os 200. O subconjunto torna o trabalho executável e enfraquece qualquer frase sobre “reconhecimento de produtos de varejo” em geral. A estratificação por metacategoria reduz o viés de escolher só garrafas ou só pacotes, mas não o elimina.

A conta de 160 vistas por face não se converte em 53.739 imagens balanceadas. Ignorar essa desigualdade faria o treino super-representar as classes fotografadas dos dois lados.

## Dataset próprio

Os 15 produtos locais provavelmente não coincidem com os SKUs do RPC. Sem correspondência documentada, não haverá experimento cruzado. Quarenta e cinco cenas é um mínimo de protocolo, não uma amostra grande para estimar mAP com intervalo estreito. O suporte por célula do E5 pode ser pequeno; a métrica estratificada terá de ser lida junto com esse suporte.

Fotos de um único operador e de poucos ambientes não cobrem câmeras, lojas nem países diferentes dos produtos.

## Modelos

MobileNetV3-Large e ResNet18 são classificadores de imagem inteira. Eles não localizam objeto. O YOLO nano é uma escolha de custo para CPU; não é a variante de maior capacidade da família. O híbrido herda o erro de caixa do detector: se a região vier cortada ou trocada, a CNN classifica o recorte errado. A fusão por produto dos escores supõe que as duas confianças sejam comparáveis, o que ainda não foi verificado.

A inicialização ImageNet pode ajudar e também pode carregar um viés de textura pouco relacionado a embalagens. Essa hipótese só se discute depois de uma corrida com e sem esses pesos.

## Implementação da métrica de detecção

A AP interna difere da AP de 101 pontos usada pelo ecossistema COCO e pelo Ultralytics. Usar a função interna como número oficial do E3 superestimaria ou subestimaria o resultado sem um critério estável. O protocolo já escolhe o validador do framework para o número reportado.

## Ambiente

A fase 1 foi instalada com o wheel CPU. Tempos medidos aqui não se transferem para uma GPU. O código seleciona CUDA quando o wheel e o hardware existem; o wheel instalado nesta máquina não inclui CUDA.

## Catálogo e preços

Não há lista aprovada de 15 produtos brasileiros nem fotografia associada. O exemplo em `exemplo_esquema.json` não é um cadastro. O banco entregue não contém série de mercado. Um preço digitado na interface, se o usuário o gravar, é uma observação com a fonte escolhida por ele; não passa a ser uma referência pública só por ter sido salvo.

A classificação usa a mediana e faixas configuráveis. Amostra pequena, poucos estabelecimentos, registros velhos, ausência de preço regular ou região não informada produzem `DADOS_INSUFICIENTES`. Ampliar a cidade para o estado, ou o estado para o país, sem dizer isso ao usuário, está fora do motor.

Preço da embalagem e preço por kg, litro ou unidade não entram na mesma conta. A comparação por unidade só ocorre com confirmação explícita e entre produtos da mesma marca, da mesma variante e da mesma unidade de base.

## OCR

O pacote `pytesseract` está instalado no ambiente. O executável Tesseract não estava disponível nesta máquina. Sem ele, a fotografia da etiqueta não gera candidato. A confiança não é preenchida quando o mecanismo não a mede. Um valor lido na imagem pode ser peso, código ou outro produto da mesma etiqueta.

## O que esta fase não sustenta

Não há acurácia, F1, mAP, matriz de confusão experimental nem conclusão sobre qual modelo é melhor. Os notebooks não treinam. A interface não reconhece produto; ela valida o arquivo enviado e pede a seleção manual. Não há resultado de E7 a E11. A classificação de um preço de teste não descreve o mercado brasileiro.
