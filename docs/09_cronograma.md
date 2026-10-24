# Cronograma proposto

A disciplina não teve o calendário institucional transcrito para este repositório. As datas abaixo são uma proposta a partir do fechamento da fase 1 em 24 de outubro de 2026. Elas devem ser alinhadas ao prazo real do trabalho final.

| Fase | Período proposto | Entrega |
| --- | --- | --- |
| 1. Base | concluída em 24 out 2026 | estrutura, ambiente, investigação do RPC, catálogo preliminar, validadores, notebooks e documentação |
| 2.1. Comparação de preços | concluída em 24 out 2026 | catálogo comercial, SQLite, motor estatístico, OCR inicial, fluxo manual e testes; sem treino e sem preços de mercado |
| 2.2. Dataset brasileiro | parcial em 24 out 2026 | 37 produtos do Open Food Facts, 117 imagens válidas, pipeline de transfer learning sem treino |
| 3. Partições | 8 a 14 nov 2026 | subconjunto congelado; manifestos; checagem de vazamento; estatística descritiva nos notebooks 01 e 02 |
| 4. Classificação | 15 a 28 nov 2026 | E1 e E2, com pesos, matrizes e tempo de inferência |
| 5. Detecção e híbrido | 29 nov a 12 dez 2026 | E3 e E4 no subconjunto de checkout |
| 6. Robustez, texto e demonstração | 13 a 20 dez 2026 | E5 e E6, interface com predição real, relatório final e limitações atualizadas com os números obtidos |

O download do RPC, se ocorrer, continua condicionado à confirmação explícita. A fase 2.2 não o fez. Se o pacote de 16 GB não puder ser obtido, o cronograma da classificação migra para o dataset próprio e o RPC permanece como referência documental. Essa contingência está prevista nas limitações e evita improvisar outro dataset no meio do treino.

Cada fase experimental grava a partição antes de ajustar pesos. Trocar a partição depois de ver o teste invalida a comparação e exige novo identificador de experimento, não a reescrita do resultado anterior.
