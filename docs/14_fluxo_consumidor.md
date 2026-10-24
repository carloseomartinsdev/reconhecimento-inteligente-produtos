# Fluxo do consumidor

A interface é `app/streamlit_app.py`. Ela exercita o caminho manual enquanto não existem pesos treinados.

## Tela inicial

Quatro destinos: escanear produto, pesquisar produto, consultar preços e informações sobre o projeto.

## Reconhecimento

A pessoa envia um arquivo ou captura pela câmera. O validador de imagem informa se o arquivo pôde ser lido. A página declara que não há modelo treinado e não escolhe uma classe. A continuação é uma lista dos produtos cadastrados. Se o catálogo estiver vazio, a orientação é cadastrar o produto na pesquisa.

Produto desconhecido, nesta fase, não recebe uma classe automática. Ele permanece fora da comparação até ser cadastrado com marca, variante, quantidade e unidade.

## Preço encontrado

O valor pode ser digitado, no formato `5,49` ou equivalente aceito por `parse_price`. Uma fotografia de etiqueta passa pelo leitor de OCR. Se houver candidatos, a pessoa confirma um deles; se o mecanismo estiver indisponível, digita o valor. Nada segue para o motor sem essa confirmação. O tipo de preço e a cidade e a UF da comparação são informados na mesma página.

## Resultado

Quando a amostra atende a política, a tela mostra o produto, o preço informado, a média, a mediana, o menor e o maior preço, as diferenças percentuais, a classificação, a quantidade de registros, a data da observação mais recente, a região considerada e as limitações. Quando não atende, mostra `DADOS_INSUFICIENTES`, os motivos e as mesmas limitações, sem classificação.

A limitação jurídica permanece visível nos dois casos: a faixa descreve a posição diante da mediana e não apura infração.

## Registro local

A página também permite cadastrar um estabelecimento e gravar uma observação já marcada como válida, com a fonte escolhida. Isso existe para que o fluxo possa ser ensaiado com dados do próprio operador. Não cria, sozinho, uma referência de mercado. Sem registros suficientes, a comparação continua insuficiente, e é esse o comportamento esperado de um catálogo recém-criado.
