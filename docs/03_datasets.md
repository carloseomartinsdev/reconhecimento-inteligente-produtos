# Datasets

## Fonte consultada

A investigação usa a página oficial do RPC, consultada em 24 de outubro de 2026, o artigo arXiv:1901.07249 e a ficha do Kaggle `diyer22/retail-product-checkout-dataset`. Nenhum arquivo de imagem ou JSON do dataset foi baixado. Os números abaixo são os publicados por essas fontes. A conferência no disco fica para depois da autorização de download.

- Página oficial: https://rpc-dataset.github.io/
- Artigo: https://arxiv.org/abs/1901.07249 e https://doi.org/10.1007/s11432-022-3513-y
- Kaggle: https://www.kaggle.com/datasets/diyer22/retail-product-checkout-dataset

## Disponibilidade

O Kaggle lista o pacote como acessível, com 15,91 GB e 83,7 mil arquivos, nas pastas `train2019`, `val2019` e `test2019`, mais `instances_train2019.json`, `instances_val2019.json` e `instances_test2019.json`. A página oficial descreve o mesmo conjunto como cerca de 15 GB e indica o Baidu Drive como alternativa quando o Kaggle não estiver acessível. O link do Baidu não foi transcrito porque a página o apresenta fora do texto extraído; ele deve ser copiado diretamente de https://rpc-dataset.github.io/ se for necessário.

O download automático está desligado. `scripts/download_rpc.py --check` apenas relata a fonte. O download exige `--confirm-download` e `--i-accept-cc-by-nc-sa-4`, além do cliente Kaggle autenticado.

## Licença

A página oficial declara CC BY-NC-SA 4.0 e uso acadêmico. Uso fora desse regime depende de contato com Xiu-Shen Wei, conforme a própria página. O cartão de um espelho no Hugging Face traz, no bloco de metadados, a marca `cc-by-nc-sa-2.0`, enquanto o texto do mesmo cartão reafirma a licença 4.0 dos autores. Este projeto segue a página oficial: CC BY-NC-SA 4.0. O dataset não será versionado. Derivados que incorporem as imagens herdam a restrição não comercial e a obrigação de atribuição e compartilhamento sob a mesma licença.

## Escala publicada

| Partição | Papel | Imagens | Objetos | Objetos por imagem | Categorias por imagem |
| --- | --- | ---: | ---: | ---: | ---: |
| Treino | exemplar, um produto | 53.739 | 53.739 | 1 | 1 |
| Validação | checkout | 6.000 | 73.602 | 12,27 | 6,33 |
| Teste | checkout | 24.000 | 294.333 | 12,26 | 6,31 |

Total publicado: 83.739 imagens. Os objetos de checkout somam 367.935, o mesmo total obtido ao reunir os três níveis de densidade.

| Densidade | Imagens | Objetos | Objetos por imagem | Categorias por imagem | Faixa de categorias | Faixa de instâncias |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Easy | 10.000 | 71.496 | 7,15 | 3,81 | 3 a 5 | 3 a 10 |
| Medium | 10.000 | 122.961 | 12,30 | 6,27 | 5 a 8 | 10 a 15 |
| Hard | 10.000 | 173.478 | 17,35 | 8,87 | 8 a 10 | 15 a 20 |

As razões da tabela oficial foram conferidas contra as contagens inteiras: 73.602 / 6.000 arredonda para 12,27, 294.333 / 24.000 para 12,26, e as três densidades arredondam para 7,15, 12,30 e 17,35. Essa conferência valida a transcrição; ela não conta arquivos locais.

## Como as imagens foram feitas

O artigo descreve quatro câmeras para o exemplar: vista de topo, vista horizontal, 45° e 30°. O produto gira em uma base, com uma foto a cada 9°. São 4 × (360 / 9) = 160 vistas por face. Embalagens do tipo caixa ou saco são fotografadas dos dois lados. A resolução declarada do exemplar é 2592 × 1944. A imagem de checkout usa uma câmera superior sobre uma placa branca de 80 cm × 80 cm, com resolução 1800 × 1800.

O total de 53.739 exemplares não fecha uma conta uniforme de 160 ou 320 imagens por SKU. Há, em média, 268,7 imagens por uma das 200 classes, e a equação que reparte as classes entre 160 e 320 vistas não produz um número inteiro de classes. A distribuição por SKU precisa ser medida nos arquivos. O projeto não assume balanceamento.

O formato do contêiner não aparece na tabela da página oficial. Relatos técnicos do Kaggle e de usuários do dataset indicam JPEG nas três pastas. O validador confirmará o cabeçalho depois do download.

## Anotações

O Kaggle informa que a anotação segue o formato de detecção do COCO. Relatos de inspeção do JSON descrevem os blocos `images`, `annotations`, `categories` e um bloco auxiliar com nomes comerciais em chinês (`__raw_Chinese_name_df` ou nome equivalente). Cada anotação traz categoria e `bbox` no padrão `[x, y, largura, altura]`. O artigo também define três supervisões para o checkout: lista de compras, ponto central e caixa. A presença de `point_xy` será aceita pelo validador se o campo existir e será cobrada apenas quando estiver preenchida.

Os nomes de arquivo e a forma como a densidade fica codificada não foram vistos em um JSON local. O inspetor não inventa essa codificação: se o nome não contiver um marcador reconhecível, a densidade permanece desconhecida até a inspeção.

## Classes

São 200 SKUs em 17 metacategorias, segundo o artigo: puffed food, dried fruit, dried food, instant drink, instant noodles, dessert, drink, alcohol, milk, canned food, chocolate, gum, candy, seasoner, personal hygiene, tissue e stationery.

O catálogo versionado em `configs/catalogs/rpc_classes.csv` traduz essa estrutura para o padrão de nome `{id}_{supercategory}` publicado no cartão do espelho Hugging Face `benjamintli/retail-product-checkout`, lido em 24 de outubro de 2026. A contagem preliminar por metacategoria, obtida desse cartão e não da figura do artigo, é:

| Metacategoria | SKUs no catálogo preliminar |
| --- | ---: |
| puffed_food | 12 |
| dried_fruit | 9 |
| dried_food | 9 |
| instant_drink | 11 |
| instant_noodles | 12 |
| dessert | 17 |
| drink | 15 |
| alcohol | 11 |
| milk | 11 |
| canned_food | 14 |
| chocolate | 12 |
| gum | 8 |
| candy | 10 |
| seasoner | 12 |
| personal_hygiene | 10 |
| tissue | 20 |
| stationery | 7 |

Nessa lista, bebida e bebida alcoólica não formam blocos contíguos: os IDs 79 e 80 aparecem como alcohol, 81 a 87 voltam a drink, e 88 a 96 são alcohol. O ID 21 aparece como dried_fruit. As duas observações ficam sob verificação até o JSON oficial. Nomes comerciais em chinês não foram copiados porque não estão nesse cartão.

## Subconjunto

O plano, ainda não congelado, está em `configs/subset_plan.yaml`: até 20 SKUs estratificados por metacategoria para classificação, com teto de imagens por SKU e separação por grupo de câmera e ângulo; até 600 imagens de `val2019` para detecção, estratificadas por densidade se o rótulo for recuperável. O `test2019` permanece intocado até a avaliação final, se os arquivos forem obtidos.

## Dataset próprio

O protocolo operacional está em `data/custom/protocol.md`. Em resumo: 15 produtos, 60 fotos isoladas por produto no desenho 5 ângulos × 3 distâncias × 2 iluminações × 2 fundos, e no mínimo 45 cenas com dois a seis produtos em três densidades. As 15 vagas em `classes_template.csv` estão em branco.

## Integração entre as origens

Os produtos do RPC são SKUs de varejo coletados pelos autores, em grande parte identificados por nomes comerciais chineses. É improvável que os 15 produtos fotografados localmente coincidam com esses SKUs. Enquanto `data/custom/manifests/class_mapping.csv` não tiver linhas com `match_type` igual a `exact` ou `visual_similar`, os experimentos permanecem separados. Uma correspondência visual, se existir, precisará de evidência registrada na coluna `evidence`. Semelhança de formato, como “garrafa” ou “caixa”, não autoriza juntar as classes.

Cada linha de manifesto conserva `origin`. Recortes de uma imagem de checkout recebem `parent_image_id` e não podem migrar para outra partição.

## Dois conjuntos independentes

O RPC permanece como material de experimento acadêmico de classificação, detecção e comparação de arquiteturas. Ele não é fonte de preços brasileiros e não foi baixado nesta fase.

O conjunto brasileiro, em `data/brazilian_products/`, destina-se ao reconhecimento dos produtos de cesta básica e à associação com o catálogo comercial. A fase 2.2 gravou 37 produtos verificados no Open Food Facts e as fotografias com licença CC BY-SA. A lista não chegou a 50 e o relatório de validação não marca o conjunto como completo. `metadata/exemplo_esquema.json` continua sendo apenas um exemplo de campos. Código de barras não é inventado.

Os preços ficam em outro lugar, `data/prices/`, ligados ao produto pelo identificador comercial. Fotografia de embalagem e série de preços não se substituem.
