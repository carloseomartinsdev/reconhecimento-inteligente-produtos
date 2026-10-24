# Transfer learning

O pipeline está em `src/classification/transfer.py` e `configs/transfer.yaml`. O experimento E12 não foi executado. Um ajuste demonstrativo, separado dessa trava, está registrado em `docs/FASE_2_2_RELATORIO.md`.

## Pesos ImageNet

A referência é a enumeração `DEFAULT` do torchvision 0.29.1+cpu já instalado. Consultar o endereço não transfere o arquivo.

| Arquitetura | Arquivo indicado | Parâmetros publicados | Tamanho publicado |
| --- | --- | ---: | ---: |
| MobileNetV3-Large | `https://download.pytorch.org/models/mobilenet_v3_large-5c1a4163.pth` | 5.483.032 | 21,107 MB |
| ResNet18 | `https://download.pytorch.org/models/resnet18-f37072fd.pth` | 11.689.512 | 44,661 MB |

O pacote torchvision instalado declara licença BSD 3-Clause em `torchvision-0.29.1+cpu.dist-info/LICENSE`. A metadado da enumeração descreve a receita de treino do torchvision, não uma licença separada do arquivo `.pth`. O download continua desligado: `download_imagenet_weights: false`. `build_transfer_classifier(..., pretrained=True)` recusa a chamada sem `authorize_download=True`.

## Etapa A

A camada final passa a ter 50 saídas. O extrator fica congelado. No MobileNetV3-Large treinam os parâmetros de `classifier`. No ResNet18 treina `fc`.

## Etapa B

Descongelam-se os três últimos blocos de `features` no MobileNetV3-Large e o `layer4` no ResNet18. A taxa desses parâmetros é um décimo da taxa da cabeça (`0,0001` contra `0,001` na configuração). A comparação com a etapa A só existe depois de uma avaliação independente. Ela não foi feita.

## Aumento e divisão

`build_brazilian_train_transform` aplica rotação de até 12 graus, brilho, contraste, translação pequena e escala entre 0,92 e 1,08. O conjunto de avaliação usa apenas redimensionamento e normalização. Imagem aumentada não entra no manifesto.

`exploratory_group_split` mantém cada `grupo_origem` inteiro de um lado. Com quatro ou cinco fotos públicas por classe, o número que sair dessa divisão é exploratório. Não sustenta desempenho generalizável. O conjunto futuro de fotos próprias, em condições reais, continua previsto e vazio.

## Embeddings

`embedding_status` distingue pesos não carregados, download não autorizado e pesos autorizados. A extração usa o extrator já construído e não baixa arquivo. MobileNetV3, ResNet18 e embeddings só podem ser comparados quando receberem o mesmo `split_id`. Essa comparação não foi executada.

## Travas

`assert_ready_for_training` exige, ao mesmo tempo, `run_training`, relatório com `completo: true` e autorização de download. O relatório atual do dataset não está completo. O experimento E12 permanece desenhado.
