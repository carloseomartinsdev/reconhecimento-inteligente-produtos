# Protocolo de fotografias próprias

Este protocolo descreve a coleta. Nenhuma fotografia foi produzida na fase 1. Os 15 produtos ainda serão escolhidos e registrados em `manifests/classes_template.csv`.

## Identidade de cada imagem

Toda imagem entra no manifesto com:

- `origin`: `custom` para fotografia própria e `public_rpc` para imagem do RPC.
- `class_id`: identificador estável definido antes da coleta.
- `session_id`: `AAAAMMDD_HHMM_local`, identificando uma ida de captura.
- `capture_group`: unidade que não pode ser quebrada entre treino, validação e teste. Uma rajada do mesmo enquadramento recebe o mesmo grupo.
- `angle`, `distance`, `lighting`, `background`: condições efetivamente usadas.
- `split`: preenchido só depois da coleta, por um script de partição.
- `sha256`: calculado na ingestão para impedir arquivo duplicado em duas partições.
- `parent_image_id`: vazio na foto original; obrigatório quando a linha for um recorte de uma cena.

## Produto isolado

Planejamento: 15 produtos e 60 imagens originais por produto.

As 60 imagens cobrem o produto cartesiano:

| Fator | Níveis |
| --- | --- |
| Ângulo | frontal; 45° à esquerda; 45° à direita; lateral; oblíqua superior |
| Distância | próxima, média, afastada. Referências de enquadramento: 30 cm, 60 cm e 100 cm, registrando a distância real |
| Iluminação | ambiente difusa; fonte lateral |
| Fundo | plano; complexo, sem outro produto do catálogo em foco |

5 × 3 × 2 × 2 = 60.

O produto ocupa a maior parte do quadro na distância próxima e continua identificável na distância afastada. A lateral mostra a face que costuma ser confundida com outro item da mesma embalagem. O fundo complexo pode ter textura, mesa ou objetos que não pertençam às 15 classes.

Nome sugerido do arquivo:

```text
data/custom/single/{class_id}/{session_id}/{class_id}_{capture_group}.jpg
```

## Cenas com vários produtos

Mínimo planejado: 45 cenas, 15 em cada densidade.

| Densidade | Produtos distintos | Oclusão e fundo |
| --- | --- | --- |
| easy | 2 ou 3 | pouca sobreposição, fundo plano |
| medium | 3 ou 4 | sobreposição parcial |
| hard | 5 ou 6 | sobreposição frequente e fundo complexo |

Cada cena é fotografada de cima, em analogia ao balcão do RPC, e também de um ângulo oblíquo, porque o uso real nem sempre terá a câmera a 90°. As duas vistas são grupos de captura diferentes. A iluminação da cena entra no manifesto.

A anotação de localização pode ser um JSON no formato COCO ou um arquivo YOLO normalizado. O validador em `src/evaluation/annotations.py` confere os dois. A caixa usa pixels `[x, y, largura, altura]` no COCO e `classe cx cy w h` normalizados no YOLO. O `class_id` da caixa precisa existir no catálogo próprio.

## Partição

Dentro de cada classe, os grupos de captura são distribuídos entre treino, validação e teste. Uma sessão longa pode abastecer mais de uma partição, desde que o mesmo `capture_group` permaneça inteiro em uma delas. Recortes herdam a partição da imagem de origem.

A proporção alvo, quando houver imagens suficientes, é 70% treino, 15% validação e 15% teste, estratificada por classe e, nas cenas, por densidade.

## O que fica fora do Git

Fotos, anotações preenchidas e manifestos com caminhos reais permanecem nas pastas ignoradas. Os arquivos deste diretório com cabeçalho e o plano de 15 vagas são a única parte versionada.
