# Catálogo comercial

O catálogo descreve o produto que o consumidor compara. Ele não é o catálogo preliminar do RPC. As 200 classes de `configs/catalogs/rpc_classes.csv` continuam servindo aos experimentos de visão e não recebem preço.

## Campos

| Campo | Papel |
| --- | --- |
| ID | Identificador interno no formato `BR0001` |
| Nome | Nome comercial |
| Marca | Fabricante ou marca |
| Categoria | Categoria comercial |
| Variante | Sabor, tipo ou apresentação |
| Quantidade | Conteúdo da embalagem |
| Unidade | `g`, `kg`, `ml`, `L` ou `un` |
| Código de barras | GTIN/EAN opcional |
| Imagem de referência | Caminho associado, se houver |
| Status | Ativo ou inativo |

## Identidade

A identidade é a combinação de marca, variante, quantidade e unidade, normalizada em `commercial_key`. Duzentos mililitros e um litro da mesma marca e da mesma variante são produtos diferentes. O motor não os trata como equivalentes só porque a unidade de base coincide.

O código de barras, quando existe, precisa ter 8 dígitos ou de 12 a 14 dígitos. Ausência é permitida. O cadastro não fabrica um código. A busca por código usa o índice único das linhas em que ele não é nulo.

## Operações

`Catalog` oferece cadastro, consulta, atualização, busca por identificador, busca por código de barras, pesquisa por nome, marca ou categoria, e a associação entre uma classe de modelo e um produto. A associação fica em `model_class_links`, com chave `(model_name, class_label)`. Ela só terá uso quando existir um modelo treinado e uma classe conferida. Associar um rótulo não faz o reconhecimento passar a funcionar.

## Lista ainda não aprovada

A coleta começa depois da aprovação dos 15 produtos. `data/brazilian_products/metadata/exemplo_esquema.json` ilustra os campos, inclusive um nome comercial usado só como exemplo de formato, e declara que o objeto não está aprovado. Esse arquivo não é carregado para o banco. As pastas `images/` e `labels/` estão vazias, à espera das fotografias e das anotações.
