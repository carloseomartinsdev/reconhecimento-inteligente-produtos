# Catálogos

`rpc_classes.csv` é uma lista preliminar de 200 SKUs. Os nomes vieram do cartão público do espelho Hugging Face `benjamintli/retail-product-checkout`, consultado em 24 de outubro de 2026, no padrão `{id}_{supercategory}`.

A lista ainda precisa ser conferida com `instances_train2019.json` ou `instances_val2019.json`. Os nomes comerciais em chinês, presentes no campo auxiliar do JSON oficial, estão vazios até essa extração.

`scripts/extract_rpc_catalog.py --json caminho\do\instances_val2019.json` mostra as diferenças sem apagar o arquivo preliminar.
