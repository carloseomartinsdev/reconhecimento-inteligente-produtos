# Fontes e confiabilidade

## Procedência

Cada preço guarda a fonte cadastrada no momento do registro:

| Código | Uso |
| --- | --- |
| `manual` | Valor digitado por quem opera o sistema |
| `label_photo` | Valor lido de uma etiqueta e confirmado |
| `consumer_report` | Relato enviado pelo consumidor |
| `authorized_public` | Série de uma fonte pública cujo uso seja permitido |

A procedência não é apagada nem substituída por “preço do sistema”. Um relato de consumidor e uma tabela pública autorizada podem coexistir; a política desta fase ainda não dá peso diferente a cada fonte dentro da mediana. Essa diferença de peso fica para um experimento posterior. O que já vale é que a origem permanece consultável.

Não houve coleta automática em sites comerciais nem integração externa.

## Validação

`pending` aguarda conferência e não entra na estatística. `invalid` também não entra. Só `valid` pode compor a referência. Marcar um registro como válido é uma decisão de quem registra; o motor não promove um valor pendente porque a amostra está pequena.

## Critérios que bloqueiam a classificação

- Região ausente.
- Menos registros válidos do que `min_records`.
- Menos estabelecimentos do que `min_establishments`.
- Registros mais antigos do que `max_age_days`.
- Ausência de preço regular quando a política exclui promoção e fidelidade.
- Comparação por unidade pedida sem confirmação, ou entre unidades de base diferentes.
- Identidade comercial diferente: outra marca, outra variante ou outra quantidade de embalagem não entra na conta da embalagem.

A região considerada é exatamente a UF e, se informada, a cidade. O relatório diz que a região não foi ampliada.

## Limitações que o consumidor precisa ver

A mediana de poucos estabelecimentos não representa o mercado. Um preço promocional misturado sem aviso desloca a referência; por isso a política padrão o deixa de fora e o relatório indica essa exclusão. Produto não cadastrado não tem comparação. Produto fotografado sem modelo treinado não está reconhecido. Valor de OCR sem confirmação não é preço informado.

Nenhuma dessas saídas sustenta a frase de que o estabelecimento pratica superfaturamento ilegal.

## Dados demonstrativos

Os testes em `tests/test_commercial_prices.py` e `tests/test_ocr_prices.py` constroem produtos, lojas e preços dentro do diretório temporário do pytest. Os nomes e os valores são sintéticos. Eles verificam o código. Não devem ser citados como preços praticados.
