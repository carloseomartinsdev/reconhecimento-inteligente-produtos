# OCR de etiquetas

O módulo `src/ocr/` prepara a leitura de um valor monetário em fotografia de etiqueta. Ele não decide que esse valor é o preço do produto identificado na outra imagem.

## Passos

1. Receber o caminho da imagem.
2. Validar o arquivo com o mesmo validador da fase 1.
3. Se o executável `tesseract` não estiver no `PATH`, devolver `mecanismo: indisponivel` e lista vazia de candidatos.
4. Se estiver, converter para tons de cinza, ampliar quando o menor lado for menor que 80 pixels, aplicar desfoque gaussiano e limiar adaptativo.
5. Pedir o texto ao `pytesseract`, com idioma `por` e, se esse idioma falhar, sem ele.
6. Localizar trechos `R$` e decimais no padrão brasileiro.
7. Normalizar o valor para texto com ponto e duas casas, por exemplo `5.49` a partir de `R$ 5,49`.
8. Devolver os candidatos, o texto original de cada um e `confianca: null`.

`requer_confirmacao` é sempre verdadeiro. A confiança não é inventada: o texto isolado, e também a chamada atual de `image_to_string`, não fornecem uma medida que este módulo considere apropriada.

Um trecho já coberto por `R$` não gera um segundo candidato só com o número interno. Dois valores distintos na mesma frase continuam distintos.

## O que a fotografia não prova

A etiqueta pode mostrar preço regular, preço promocional, preço por quilo, peso e código. O candidato é uma hipótese. A interface pede que a pessoa confirme o valor antes da comparação, e o registro, se for salvo, guarda a fonte `label_photo` só quando essa for a origem escolhida.

Nesta máquina o executável Tesseract não estava instalado. O teste correspondente verifica que uma imagem válida não produz preço inventado. O experimento E7 continua sem resultado.
