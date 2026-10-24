# Interface Streamlit

`streamlit_app.py` conduz o fluxo manual do consumidor.

- **Início** apresenta escanear, pesquisar, consultar preços e as informações do projeto.
- **Escanear produto** aceita arquivo ou câmera, valida a imagem e declara que não há modelo treinado. Nenhuma classe é simulada. O produto é escolhido na lista cadastrada.
- **Pesquisar produto** consulta nome, marca ou categoria e cadastra um produto. O código de barras só é gravado se for informado e tiver 8 ou de 12 a 14 dígitos. O sistema não gera GTIN.
- **Consultar preços** recebe o valor digitado, ou uma fotografia de etiqueta, pede confirmação e chama o motor. O relatório mostra produto, preço, estatísticas, classificação, contagem, data, região e limitações. Amostra insuficiente aparece como `DADOS_INSUFICIENTES`, sem classificação.
- **Informações** mantém o resumo do RPC, o dispositivo e o aviso de que não há métrica experimental.

O preço é texto, não um campo numérico de ponto flutuante. Estabelecimentos e observações podem ser registrados pela própria tela; a fonte fica associada ao registro. Esses dados são do operador local e não substituem uma série pública.

A detecção com caixas depende de pesos em `models/`, que ainda não existem.
