# Fundamentação teórica

## Reconhecimento de produto e checkout automático

Wei et al. formulam o checkout automático como a previsão da lista de compras a partir da imagem dos produtos no balcão: presença e contagem de cada SKU. O problema reúne escala, diferença fina entre embalagens parecidas, poucas imagens de atualização de estoque e mudança de domínio entre a foto controlada do produto e a cena real de pagamento (Wei et al., 2019; 2022).

Esse enquadramento organiza o projeto. A classificação individual responde à foto controlada. A detecção responde à cena com vários objetos. O modelo híbrido separa as duas perguntas: onde está o objeto e qual é a classe do recorte.

## Redes convolucionais

Uma CNN aprende filtros locais e agrega evidência espacial por convolução, não linearidade e redução de resolução (LeCun, Bengio e Hinton, 2015). Em classificação de produto, a rede recebe a imagem inteira e devolve uma distribuição sobre as classes. A perda prevista para o treino futuro é a entropia cruzada categórica. A inicialização ImageNet é uma hipótese de transferência, não um resultado: ela será ligada de forma explícita na fase experimental e comparada, se houver tempo, com o treino a partir de pesos aleatórios.

## ResNet18

He, Zhang, Ren e Sun (2016) introduzem conexões residuais para treinar redes mais profundas sem degradar a otimização. O ResNet18 é uma instância compacta dessa família, com cerca de 11 milhões de parâmetros na classificação ImageNet original. No projeto ele é o classificador de referência: arquitetura consolidada, custo moderado e implementação estável no Torchvision. A última camada linear é substituída pelo número de classes do experimento.

## MobileNetV3

Howard et al. (2019) projetam o MobileNetV3 com busca de arquitetura, convoluções separáveis em profundidade e blocos com atenção por canal. A variante Large é a escolha do Modelo A porque preserva a motivação de eficiência e ainda oferece capacidade suficiente para embalagens parecidas. A última camada do classificador também é substituída. A comparação com o ResNet18 só é interpretável se os dois modelos virem as mesmas imagens, a mesma partição, a mesma semente e o mesmo orçamento de épocas.

## Detecção e YOLO

Detecção pede caixa e classe. A família YOLO trata a imagem em uma única passagem e prevê caixas, objetividade e classes (Redmon, Divvala, Girshick e Farhadi, 2016). O projeto usa a implementação Ultralytics e a variante nano (`yolo11n`) como ponto de partida, porque o ambiente de referência precisa funcionar em CPU. Variantes maiores ficam como extensão condicionada à existência de GPU, não como parte do protocolo inicial.

A métrica de detecção segue a lógica de precisão média em limiares de IoU popularizada pelo COCO (Lin et al., 2014): mAP@50 e mAP@50:95. O validador do Ultralytics será a fonte do número experimental. A função em `src/evaluation/detection.py` existe para auditoria e teste e usa a área sob a curva precision-recall com envelope de precisão; ela não reproduz sozinha a interpolação de 101 pontos do COCO.

## Híbrido

O Modelo D usa o detector como propositor de regiões e a CNN como classificador do recorte, com uma margem configurável em torno da caixa. A confiança combinada planejada é o produto da confiança do detector pela probabilidade da classe escolhida pela CNN. Essa composição é uma regra inicial, documentada em `configs/hybrid.yaml`, e pode ser revisada antes do E4 se a calibração dos dois escores se mostrar incompatível. A revisão precisa ficar registrada; não será apresentada como detalhe de implementação invisível.

## O que a literatura do RPC já mostrou

Os autores avaliaram detectores treinados só com imagens de produto isolado, com imagens sintetizadas por recorte e colagem e com uma tradução de domínio por CycleGAN. No artigo, o detector treinado apenas nos exemplares praticamente não resolve o checkout, e mesmo o melhor arranjo reportado por eles deixa erro relevante quando a cena fica densa. Na média dos três níveis de oclusão, o método Syn+Render dos autores alcança checkout accuracy de 56,68%, mAP50 de 96,57% e mmAP de 73,83% (Wei et al., 2019, Tabela 3). Esses valores são resultados dos autores, obtidos com FPN e síntese em grande escala. Este trabalho ainda não mediu nada disso e não pretende repetir o mesmo orçamento de síntese. A citação serve para justificar por que o protocolo precisa separar domínio controlado e cena de checkout, e por que um subconjunto didático continua sendo um problema difícil.

## Referências

He, K., Zhang, X., Ren, S., & Sun, J. (2016). Deep residual learning for image recognition. In *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition* (pp. 770–778).

Howard, A., Sandler, M., Chu, G., Chen, L.-C., Chen, B., Tan, M., Wang, W., Zhu, Y., Pang, R., Vasudevan, V., Le, Q. V., & Adam, H. (2019). Searching for MobileNetV3. In *Proceedings of the IEEE/CVF International Conference on Computer Vision* (pp. 1314–1324).

LeCun, Y., Bengio, Y., & Hinton, G. (2015). Deep learning. *Nature, 521*, 436–444.

Lin, T.-Y., Maire, M., Belongie, S., Hays, J., Perona, P., Ramanan, D., Dollár, P., & Zitnick, C. L. (2014). Microsoft COCO: Common objects in context. In *European Conference on Computer Vision* (pp. 740–755).

Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. (2016). You only look once: Unified, real-time object detection. In *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition* (pp. 779–788).

Wei, X.-S., Cui, Q., Yang, L., Wang, P., Liu, L., & Yang, J. (2019). RPC: A large-scale retail product checkout dataset. *arXiv:1901.07249*.

Wei, X.-S., Cui, Q., Yang, L., Wang, P., Liu, L., & Yang, J. (2022). RPC: A large-scale and fine-grained retail product checkout dataset. *Science China Information Sciences, 65*, 197101. https://doi.org/10.1007/s11432-022-3513-y
