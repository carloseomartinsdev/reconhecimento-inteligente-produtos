# Metodologia

## Quatro protocolos

Os modelos não compartilham uma única partição, porque as imagens não vêm da mesma distribuição.

**P-CLS-exemplar.** Classificação individual sobre imagens de um produto. No RPC, a fonte são os exemplares, não as cenas de checkout. A partição oficial do dataset coloca todos os exemplares no treino e reserva validação e teste para o checkout; usá-la como se fosse uma divisão i.i.d. confundiria arquitetura com mudança de domínio. O E1 e o E2 usam uma partição interna dos exemplares. O E6 trata o salto até o checkout ou até as fotos próprias como outra pergunta.

**P-DET-checkout.** Detecção em cenas com vários objetos. A partição de trabalho sai de um subconjunto de `val2019`, com o teste oficial guardado para a leitura final. Treinar o YOLO só nos exemplares repetiria o cenário em que os autores observaram falha de domínio. Esse cenário pode ser um ensaio secundário, separado do número principal do E3.

**P-HYB-checkout.** O híbrido é avaliado nas mesmas imagens do detector. A CNN de recorte não treina em recortes de imagens que pertençam à partição de teste.

**P-CUSTOM.** Fotografias próprias, com os fatores de captura no manifesto. Serve ao E5 e à perna local do E6.

## Unidade que não pode vazar

O bloqueio padrão impede que o mesmo `image_id`, o mesmo caminho, o mesmo `sha256`, o mesmo `parent_image_id` ou o mesmo `capture_group` apareçam em duas partições entre treino, validação e teste.

`capture_group` reúne vistas que são quase duplicatas: rajada do mesmo enquadramento ou, no RPC, o conjunto de ângulos vizinhos da mesma câmera e do mesmo SKU que se decida manter junto. A regra concreta de vizinhança angular será escrita no manifest no momento da partição, a partir dos nomes reais dos arquivos.

`session_id` documenta a coleta. Uma sessão de fotografias pode alimentar mais de uma partição quando os grupos de captura são independentes. Se a política escolhida para um manifesto for “uma sessão inteira em uma partição”, a checagem de `session_id` é ligada por `extra_group_columns`. Ela não é o padrão, porque as 60 fotos de um produto tendem a nascer na mesma ida ao cenário.

Linhas `unlabeled` e `ignored` não entram na checagem. Elas também não entram em treino.

## Estratificação e semente

A semente padrão é 42, aplicada a `random`, NumPy, PyTorch e, se existir, CUDA. As operações cuDNN determinísticas ficam ligadas quando `runtime.deterministic` é verdadeiro. Isso torna o sorteio da partição repetível; não elimina toda diferença numérica entre CPU e GPU em convoluções.

Dentro de cada classe, a divisão alvo é 70% treino, 15% validação e 15% teste, sobre grupos de captura. Nas cenas, a densidade também entra na estratificação. Classes com menos grupos do que o necessário para preencher as três partições são registradas e ficam de fora do experimento, em vez de serem copiadas para o teste.

## Pré-processamento

O preset `baseline_imagenet` redimensiona para 224 × 224, o que altera a proporção, e normaliza com a média e o desvio do ImageNet. `letterbox` preserva a proporção e completa a borda. `equalize` e `clahe` atuam na luminância antes do redimensionamento. `identity_scale` é o redimensionamento direto, usado como referência do efeito geométrico. A augmentação de treino prevista é espelhamento horizontal e jitter de cor. Ela fica fora do conjunto de validação e de teste.

Nenhum desses presets teve desempenho medido.

## Execução

O código pede GPU e usa CPU quando `torch.cuda.is_available()` é falso. O ambiente instalado na fase 1 é o wheel CPU do PyTorch, porque esta máquina não apresentou `nvidia-smi`. Um wheel CUDA pode substituí-lo em outra máquina sem mudar os protocolos. Os tamanhos de lote previstos estão separados em `batch_size.cpu` e `batch_size.gpu` nas configurações.

Hiperparâmetros iniciais, ainda não ajustados: AdamW com taxa 3×10⁻⁴ e weight decay 10⁻⁴; até 20 épocas e paciência 5 para classificação; até 50 épocas e paciência 10 para o YOLO; imagem de classificação em 224 px; imagem de detecção em 640 px. Eles estão nos YAML para que a fase experimental não os escolha em silêncio.

## Separação entre treino e inferência

`classification/train.py`, `detection/yolo.py` e `hybrid/pipeline.py` recusam o treino na fase 1. A inferência de classificação é uma função à parte e, nos testes, só recebe um tensor nulo para verificar a forma da saída. Isso não produz rótulo de produto.
