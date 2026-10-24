# Relatório da fase 1

Data: 24 de outubro de 2026. Esta fase não treinou modelos e não baixou o RPC.

## Estrutura

O projeto está em `reconhecimento-inteligente-produtos/`, com `app/`, `configs/`, `data/`, `docs/`, `notebooks/`, `src/`, `models/`, `experiments/`, `results/`, `tests/`, `scripts/`, `requirements.txt` e `README.md`. A pasta `scripts/` concentra o download condicionado, a inspeção e a extração do catálogo.

## Ambiente instalado

Python 3.12.10 em `.venv`. A máquina não expõe `nvidia-smi`; `torch.cuda.is_available()` retornou `False`. O wheel instalado é o de CPU.

| Pacote | Versão |
| --- | --- |
| torch | 2.14.1+cpu |
| torchvision | 0.29.1+cpu |
| opencv-python | 5.0.0.93 |
| ultralytics | 8.4.186 |
| numpy | 2.5.2 |
| pandas | 3.1.0 |
| scikit-learn | 1.9.1 |
| matplotlib | 3.11.2 |
| streamlit | 1.66.1 |
| pillow | 12.3.0 |
| pytest | 9.1.1 |

A lista completa está em `requirements.lock.txt`.

## Dataset

Fontes lidas em 24 de outubro de 2026: página oficial, arXiv:1901.07249 e a ficha do Kaggle. O pacote está publicado, com cerca de 15,91 GB no explorador do Kaggle, licença CC BY-NC-SA 4.0 na página oficial, 200 SKUs, 17 metacategorias e 83.739 imagens (53.739 exemplares, 6.000 de validação e 24.000 de teste).

Nesta máquina o inventário local está `absent`, com 0 arquivos de imagem. O catálogo preliminar tem 200 classes e 17 metacategorias; os nomes comerciais em chinês continuam vazios até a leitura do JSON oficial.

## Testes

`pytest` executou 31 testes, todos aprovados. Cobrem configuração, semente, catálogo, vazamento, imagem sintética, anotação sintética, pré-processamento, forma da saída de MobileNetV3-Large e ResNet18 sem pesos ImageNet, recusa de treino, recusa de peso YOLO ausente e métricas sobre vetores de teste.

Os oito notebooks preparatórios foram executados. As células de treino registraram que o treino não ocorreu. Uma passagem estrutural, com 8 classes de saída e sem peso ImageNet, contou 4.212.280 parâmetros no MobileNetV3-Large e 11.180.616 no ResNet18. Esses números descrevem essa instanciação; mudam com o número de classes e não são desempenho de reconhecimento.

A interface Streamlit respondeu em `http://127.0.0.1:8501`. As cinco páginas abrem. O envio de uma imagem sintética passou na validação de arquivo. A página de métricas informa que não há resultado experimental.

## Pendências

- Autorizar e baixar o RPC, depois conferir contagens, formato, densidade e o catálogo contra o JSON.
- Escolher os 15 produtos, fotografar segundo `data/custom/protocol.md` e anotar as cenas.
- Congelar o subconjunto e as partições antes de qualquer treino.
- Decidir, ainda antes do treino, se o detector permanece em `yolo11n` ou passa para YOLO26, família também presente no Ultralytics 8.4.186.
- Ligar a inicialização ImageNet somente na fase experimental, com o download pequeno registrado à parte.
- Em máquina com GPU, reinstalar o wheel CUDA correspondente; o código já seleciona CUDA quando ele existe.

## Recomendação para a fase 2

Começar pela confirmação do download e pela inspeção do JSON. Em seguida fechar a lista de SKUs do subconjunto e a lista dos 15 produtos locais. Só então materializar `data/splits/` e passar ao E1. Sem linhas utilizáveis em `class_mapping.csv`, o E6 permanece como dois experimentos separados.
