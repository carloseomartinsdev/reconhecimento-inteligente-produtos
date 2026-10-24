# Análise estatística

O motor está em `src/pricing/engine.py`. A política padrão está em `configs/pricing.yaml` e pode ser trocada para um experimento sem alterar o código. A referência da classificação é a mediana.

## Filtros

Entram na conta apenas registros com `validation_status` igual a `valid`, do produto em escopo, observados na UF informada e, se a cidade for informada, nessa cidade. A idade máxima padrão é 90 dias. Com `regular_only` verdadeiro, preços `promotional` e `loyalty` ficam de fora; o tipo `other` também não é tratado como regular.

Se a cidade vier preenchida, a busca não sobe para o restante do estado. Se a UF não vier, o retorno é `DADOS_INSUFICIENTES` com o motivo `regiao_nao_informada`.

## Indicadores

Sobre a amostra aceita, o motor calcula quantidade de registros, quantidade de estabelecimentos, mínimo, máximo, média, mediana, desvio padrão populacional, primeiro quartil, terceiro quartil, diferença percentual em relação à média e diferença percentual em relação à mediana.

A mediana, em amostra par, é a média dos dois valores centrais. O quartil usa interpolação linear na posição `(n - 1) * p`. O desvio padrão só existe com pelo menos dois valores; a variância divide por `n`, não por `n - 1`. Todas as contas usam `Decimal`.

A diferença percentual é `(informado - referência) / referência * 100`.

## Classificação

O percentual em relação à mediana cai em uma das faixas:

| Diferença percentual | Classificação |
| --- | --- |
| Inferior a -10% | Excelente preço |
| De -10% até menos de -3% | Bom preço |
| De -3% até +5%, inclusive | Dentro da média |
| Acima de +5% até +15%, inclusive | Acima da média |
| Superior a +15% | Muito acima da média |

O nome “Dentro da média” é o rótulo definido para a faixa central. O número que escolhe a faixa é a diferença contra a mediana, não contra a média. A média continua no relatório para leitura. A classificação não é uma conclusão legal; o texto fixo do motor diz que ela não apura infração, superfaturamento ilegal ou prática abusiva.

## Confiabilidade

Os mínimos padrão são 5 registros válidos e 3 estabelecimentos. Se a amostra filtrada não os atinge, ou se não resta preço regular, ou se os registros existentes estão fora da idade ou da região, o status é `DADOS_INSUFICIENTES`. Nesse caso não há média, mediana nem classificação. A contagem do que restou depois do filtro pode ser mostrada, junto com o motivo: `nenhum_registro_na_regiao`, `registros_nao_validados`, `registros_desatualizados`, `sem_preco_regular`, `poucos_registros`, `poucos_estabelecimentos` ou `unidades_incompativeis`.

## Preço por unidade

A base padrão é a embalagem: só entram registros daquele `product_id`, e o valor comparado é o preço do pacote.

A base `unit` exige `confirm_unit_comparison`. O escopo passa a incluir produtos ativos da mesma marca e da mesma variante cuja quantidade possa ser convertida para a mesma unidade de base: grama para quilograma, mililitro para litro, unidade permanece unidade. O preço informado e cada registro são divididos pela quantidade nessa unidade. R$/kg, R$/L e R$/unidade não se misturam com o preço da embalagem na mesma estatística. Sem a confirmação, o motivo é `comparacao_por_unidade_nao_confirmada` e não há classificação.
