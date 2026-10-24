# Base de preços

O banco desta etapa é SQLite, no caminho `data/prices/market.sqlite` definido em `configs/default.yaml`. O arquivo é local e está no `.gitignore`. A aplicação cria o esquema na primeira abertura. A entrega da fase 2.1 não inclui um banco preenchido com preços.

## Representação monetária

A coluna `price` é `TEXT`, no formato canônico com duas casas, por exemplo `5.49`. A aplicação converte esse texto para `decimal.Decimal` e rejeita `float`. Valor vazio, não numérico, negativo, zero ou com mais de duas casas decimais não é gravado. O arredondamento de meia casa não é usado para “consertar” um terceiro dígito: esse valor é recusado.

PostgreSQL fica para uma fase posterior. A troca prevista é a conexão e o tipo `NUMERIC`, com `Decimal` ainda na aplicação. As consultas desta etapa usam o marcador `?`.

## Entidades

**Fontes.** Quatro procedências são criadas com o esquema: coleta manual (`manual`), fotografia de etiqueta (`label_photo`), informação enviada pelo consumidor (`consumer_report`) e fonte pública autorizada (`authorized_public`). O registro de preço aponta para uma delas. A origem não é reescrita depois.

**Produtos.** Campos comerciais descritos em `docs/10_catalogo_comercial.md`, com `commercial_key` única.

**Estabelecimentos.** Identificador, nome, cidade, estado, bairro opcional, identificador externo opcional e status. O estado precisa ser uma UF brasileira. O identificador externo, se informado, é único.

**Registros de preços.** Produto, estabelecimento, preço, data da observação, data de registro, fonte, tipo de preço, condições da oferta e status de validação. Os tipos são `regular`, `promotional`, `loyalty` e `other`. Os status são `pending`, `valid` e `invalid`. A data de observação não pode ser futura em relação ao dia de referência.

**Vínculo de classe.** Liga o nome de um modelo e o rótulo de uma classe ao produto. Não contém preço.

## O que não entra no banco

Não há importação de sites comerciais. `data/prices/imports/` e `data/prices/examples/` não trazem tabela de preços. Um exemplo de esquema de produto não é uma observação de preço. Dados sintéticos existem apenas dentro dos testes, em arquivos temporários, e não são copiados para `market.sqlite`.
