# Dataset brasileiro

Estado em 24 de outubro de 2026: **parcial**. O relatório automático está em `data/brazilian_products/evaluation/relatorio_por_produto.json`. `completo` é falso.

## O que foi obtido

- Produtos com identidade comercial validada: 37.
- Imagens no manifesto: 119.
- Imagens que passaram na validação técnica: 117.
- Produtos com pelo menos 4 imagens válidas: 14.
- Meta mínima de 200 imagens e meta ideal de 250: não atingidas.
- Downloads recusados pelo servidor de imagens: 0 na primeira coleta. A busca seguinte não acrescentou arquivo.

Trinta e três arquivos tinham sido gravados na versão de 400 px e ficaram com um lado abaixo de 224 px. Foram substituídos pela fotografia original do mesmo `imgid`, com URL, SHA-256 e resolução atualizados. Não são fotos novas.

Depois disso, a validação recusou 1 imagem por resolução e 1 por semelhança visual. As outras 117 foram aceitas no critério técnico.

## Licença

Fonte única: Open Food Facts. Termos: https://world.openfoodfacts.org/terms-of-use

- Dados: ODbL e DbCL.
- Fotografias: CC BY-SA, conforme os termos da fonte.
- Atribuição exigida: ligação para a página do produto.
- Limite registrado no manifesto: a licença cobre a foto do contribuidor e não apaga direitos de marca ou de arte da embalagem.

Não entrou imagem de fabricante, de varejista nem de origem desconhecida. Não houve contorno de proteção de site.

## Manifesto

`metadata/image_manifest.csv` guarda produto, arquivo, fonte, URL, licença, autorização, data, SHA-256, resolução do arquivo, resolução original informada pela fonte, formato, grupo de origem e se o arquivo deriva da mesma fotografia. Cada arquivo corresponde a um id original. `mesmo_original` está `nao`.

`metadata/sources.json` descreve a fonte. `metadata/imagens_rejeitadas.json` lista falhas de download; nesta execução a lista está vazia.

## O que o validador não faz

Ele não olha a embalagem para dizer se o produto fotografado é o produto do código. `conteudo_revisado_manualmente` é falso em todos os itens. Por isso o dataset não é declarado completo, mesmo nos 14 produtos que já têm quatro ou cinco imagens tecnicamente válidas.
