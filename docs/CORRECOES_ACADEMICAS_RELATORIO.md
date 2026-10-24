# Relatório de execução — correções acadêmicas

Data da execução: 24 de outubro de 2026.  
Ambiente: Windows 10, CPU, Python 3.12.10, PyTorch 2.14.1+cpu, torchvision 0.29.1+cpu, Streamlit 1.66.1.

## Correções realizadas

1. **Dataset.** O experimento usa as 77 imagens de frente ou de embalagem, de 37 produtos e 9 categorias. Quarenta e duas imagens de verso, ingredientes ou tabela nutricional foram excluídas do treino e permanecem no manifesto. O resumo está em `results/metrics/dataset_summary.json`. Os gráficos de distribuição e os exemplos estão em `results/figures/`.

2. **Pré-processamento.** O treino aplica RGB, redimensionamento, rotação de até 12 graus, brilho, contraste, translação, escala, recorte 224 × 224, tensor e normalização ImageNet. A figura `results/figures/preprocessamento.png` mostra original, 224 × 224, tensor normalizado reconvertido e um exemplo de aumento.

3. **Transfer learning.** MobileNetV3-Large e ResNet18 foram treinados com pesos ImageNet. A etapa A treina só a cabeça. A etapa B descongela os três últimos blocos do MobileNet ou a `layer4` do ResNet, com taxa 0,0001. A fotografia de demonstração de arroz não entra na seleção. O checkpoint escolhido é o de maior F1 de validação: `models/brazilian/experiment_best.pt`. O arquivo `models/brazilian/classifier.pt` não foi substituído.

4. **Divisão.** Semente 42, identificador `academico-grupos-s42`. Treino 54, validação 12, teste 11. Grupos de origem não se misturam. Manteiga não tem teste porque só há dois grupos. Arquivos em `data/splits/`.

5. **Métricas.** Acurácia, precisão, recall, F1 macro, perdas, matriz de confusão, tempos e parâmetros treináveis foram calculados pela execução real de `scripts/run_academic_experiment.py`.

6. **Comparação.** As quatro corridas usam a mesma divisão e o mesmo protocolo. A discussão está no relatório acadêmico e no notebook `09`.

7. **Streamlit.** A tela de escanear prefere `experiment_best.pt`, guarda o modelo em cache, mostra as três categorias mais prováveis, os produtos da categoria e os preços demonstrativos. Há uma nota de que o aplicativo é uma demonstração acadêmica.

8. **Notebook.** `notebooks/09_experimento_final.ipynb` lê os artefatos da execução de 24 de outubro de 2026 e faz uma inferência real numa imagem de teste. Os notebooks `01` a `08` foram mantidos.

9. **Documentação.** README atualizado e `docs/RELATORIO_ACADEMICO_FINAL.md` criado. `configs/transfer.yaml` permanece com o treino bloqueado; o experimento acadêmico é um script separado, para não alterar a trava exigida pelos testes.

## Experimentos executados

Comando:

```powershell
.\.venv\Scripts\python.exe scripts\run_academic_experiment.py
```

| Item | Valor |
|---|---|
| Modelos | MobileNetV3-Large e ResNet18 |
| Pesos iniciais | ImageNet, torchvision DEFAULT |
| Etapas | A, cabeça; B, fine-tuning parcial a partir da melhor época de A |
| Imagem | 224 × 224 |
| Lote | 8 |
| Épocas máximas | 20 |
| Otimizador | AdamW |
| Taxa etapa A | 0,001 na cabeça |
| Taxa etapa B | 0,0001 |
| Parada antecipada | 5 épocas no F1 macro de validação |
| Semente | 42 |
| Dispositivo | CPU |
| Duração total | 140 s, incluindo o download do ResNet18 |

## Resultados

Valores lidos de `results/metrics/model_comparison.csv`.

| Modelo | Etapa | Acurácia | Precisão | Recall | F1 | Treino (s) | Inferência (s) | Parâmetros |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| mobilenet_v3_large | A | 0,727 | 0,625 | 0,688 | 0,646 | 46,1 | 0,0294 | 1241609 |
| mobilenet_v3_large | B | 0,545 | 0,333 | 0,438 | 0,375 | 20,8 | 0,0307 | 2991849 |
| resnet18 | A | 0,364 | 0,113 | 0,250 | 0,155 | 33,3 | 0,0431 | 4617 |
| resnet18 | B | 0,455 | 0,354 | 0,500 | 0,396 | 25,0 | 0,0436 | 8398345 |

F1 de validação, critério de escolha: MobileNet A 0,867; MobileNet B 0,811; ResNet A 0,323; ResNet B 0,222.

Escolhido: MobileNetV3-Large, etapa A. F1 de teste 0,646. Oito acertos em onze imagens. Erros: Arroz → Farinhas e flocão, Açúcar → Arroz, Feijão → Farinhas e flocão.

Uma inferência do notebook na primeira imagem de teste (`images/BR0003/2.jpg`, categoria real Arroz) devolveu Farinhas e flocão 0,471, Óleo de soja 0,303 e Leite UHT 0,086. Esse erro já aparece na matriz.

## Testes

Comando:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Resultado em 24 de outubro de 2026: 61 aprovados, 0 falhas.

Os testes novos cobrem divisão sem vazamento de grupo, tensor 3 × 224 × 224, transformação de treino, soma das probabilidades e gravação de checkpoint. A suíte anterior continua exigindo `experiments.run_training = false`.

## Pendências

- Manteiga não tem conjunto de teste. Não foi inventada uma métrica para ela.
- O fine-tuning não melhorou o F1 de validação. Não houve nova busca de hiperparâmetros.
- A base não foi ampliada. Isso segue o escopo pedido.
- Não há validação cruzada. A divisão é única, com a limitação registrada.
- O Tesseract não está no PATH. O experimento de categoria não depende de OCR.

## Avaliação interna

Matriz de referência do próprio pedido. Não é a rubrica do professor. A nota máxima não foi dada onde a evidência é limitada.

| Critério | Peso | Nota | Justificativa | Evidência | Limitação |
|---|---:|---:|---|---|---|
| Técnicas de visão computacional | 2,0 | 1,7 | Classificação convolucional, aumento e inferência sobre fotos reais. | `src/classification/`, notebook 09, figuras. | A detecção de cena não faz parte deste experimento. |
| Transfer learning | 2,0 | 1,8 | Duas arquiteturas, pesos ImageNet, etapas A e B, escolha pela validação. | Checkpoints em `models/brazilian/` e `model_comparison.json`. | A etapa B piorou a validação. O teste tem 11 imagens. |
| Pré-processamento | 1,0 | 0,9 | RGB, 224, ImageNet, tensor e aumento moderado, com figura. | `src/classification/augment.py`, `preprocessamento.png`. | A figura mostra um exemplo, não todas as variações. |
| Avaliação experimental | 2,0 | 1,5 | Métricas, curvas, matriz e comparação saíram de uma execução real. | `results/metrics/model_comparison.csv`. | Macro-F1 instável. Manteiga ausente no teste. |
| Organização e reprodutibilidade | 1,0 | 0,9 | Semente, divisões, script e 61 testes. | `data/splits/academico_s42.json`, `pytest`. | Uma única divisão, sem repetição de sementes. |
| Documentação | 1,0 | 0,9 | Relatório, notebook e README alinhados aos números gravados. | `docs/RELATORIO_ACADEMICO_FINAL.md`, notebook 09. | Os documentos das fases anteriores descrevem o estágio da época. |
| Demonstração funcional | 1,0 | 0,8 | A tela de escanear abre no checkpoint experimental. Uma foto de teste de leite foi classificada como Leite UHT, com três scores, produtos da categoria e preços demonstrativos. | `app/streamlit_app.py`, execução local em 24/10/2026. | O reconhecimento continua limitado à base pequena. |

**Total estimado: 8,5 / 10,0.**

A nota não chega a 10 porque o teste é pequeno, o fine-tuning não melhorou o critério de seleção e a generalização fora do catálogo não foi medida.
