"""Fluxo do consumidor e painel da fase de visão computacional.

O reconhecimento visual não é simulado. Sem pesos treinados, a pessoa confirma o produto.
Os preços exibidos saem do banco local; esta instalação não traz preços de mercado.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from catalog.identity import IdentityError
from catalog.import_brazilian import import_products
from catalog.service import Catalog
from database.store import Store, StoreError
from classification.candidates import load_checkpoint, top_candidates
from datasets.catalog import correspondence_status, load_class_mapping, load_rpc_catalog, summarize_catalog
from datasets.rpc_reference import inspect_local_rpc
from ocr.reader import read_label
from preprocessing.validate import validate_image
from pricing.engine import INSUFFICIENT, LEGAL_LIMITATION, PriceEngine
from pricing.money import MoneyError, format_price
from pricing.policy import PricePolicy
from pricing.statistics import median
from pricing.test_prices import TEST_OFFER, ensure_test_prices
from utils.config import load_config, resolve_path
from utils.device import device_description, get_device

REASON_TEXT = {
    "regiao_nao_informada": "Informe a UF da comparação. A cidade é opcional e, quando informada, limita a região.",
    "poucos_registros": "A quantidade de registros válidos ficou abaixo do mínimo configurado.",
    "poucos_estabelecimentos": "Os registros válidos vêm de poucos estabelecimentos independentes.",
    "registros_desatualizados": "Os registros da região são mais antigos que o prazo configurado.",
    "sem_preco_regular": "Não há preço regular suficiente. Promoção e fidelidade ficaram fora da referência.",
    "nenhum_registro_na_regiao": "Não há registro na região pedida. A busca não foi estendida.",
    "registros_nao_validados": "Os registros existentes ainda não foram marcados como válidos.",
    "comparacao_por_unidade_nao_confirmada": "A comparação por unidade só ocorre depois da confirmação.",
    "unidades_incompativeis": "As unidades de medida não permitem a comparação pedida.",
}

st.set_page_config(
    page_title="Escanear produto",
    page_icon="🛒",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def inject_app_style() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {display: none;}
        header[data-testid="stHeader"] {background: transparent;}
        footer {visibility: hidden;}
        .stApp {background: #efeae2;}
        .block-container {max-width: 440px; padding-top: 1rem; padding-bottom: 2.5rem;}
        h1 {font-size: 1.55rem !important; letter-spacing: -0.03em; margin-bottom: 0.2rem;}
        .app-mark {font-weight: 700; letter-spacing: -0.04em; font-size: 1.15rem; margin: 0 0 0.6rem 0;}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def load_context() -> dict:
    config = load_config(
        "default.yaml",
        "classification.yaml",
        "detection.yaml",
        "hybrid.yaml",
        "pricing.yaml",
        "transfer.yaml",
    )
    store = Store(resolve_path(config["paths"]["prices_db"]))
    import_products(store, resolve_path(config["paths"]["brazilian_metadata"]) / "products.json")
    ensure_test_prices(store)
    checkpoint_path = resolve_path(config["paths"]["brazilian_checkpoint"])
    rpc = load_rpc_catalog(resolve_path(config["paths"]["catalog_rpc"]))
    mapping = load_class_mapping(resolve_path(config["paths"]["class_mapping"]))
    return {
        "config": config,
        "store": store,
        "catalog": Catalog(store),
        "engine": PriceEngine(store, PricePolicy.from_mapping(config)),
        "summary": summarize_catalog(rpc),
        "mapping": correspondence_status(mapping),
        "inventory": inspect_local_rpc(resolve_path(config["paths"]["rpc_root"])),
        "device": device_description(get_device(config["runtime"]["prefer_gpu"])),
        "checkpoint": load_checkpoint(checkpoint_path),
    }


def save_upload(upload, folder: str) -> Path:
    destination = ROOT / "results" / "predictions" / folder
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / upload.name
    target.write_bytes(upload.getbuffer())
    return target


def product_label(product) -> str:
    return f"{product.id} — {product.name} — {product.brand} — {product.quantity} {product.unit} — {product.variant or 'sem variante'}"


def visual_checkpoint_path() -> Path:
    experimental = ROOT / "models" / "brazilian" / "experiment_best.pt"
    if experimental.exists():
        return experimental
    return ROOT / "models" / "brazilian" / "classifier.pt"


@st.cache_resource
def cached_classifier(path_text: str):
    checkpoint = load_checkpoint(Path(path_text))
    if checkpoint is None or checkpoint.get("task") != "categoria":
        return None
    labels = [str(label) for label in checkpoint["labels"]]
    model = build_classifier_from_checkpoint(checkpoint, labels)
    return model, labels, checkpoint


def build_classifier_from_checkpoint(checkpoint: dict, labels: list[str]):
    import torch

    from classification.transfer import build_transfer_classifier

    model = build_transfer_classifier(
        checkpoint["architecture"],
        num_classes=len(labels),
        stage="A",
        pretrained=False,
    )
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model


def classify_saved_image(path: Path, checkpoint: dict) -> list[dict[str, object]]:
    import torch
    from PIL import Image

    from preprocessing.transforms import build_eval_transform

    loaded = cached_classifier(str(visual_checkpoint_path()))
    if loaded is None:
        return []
    model, labels, _checkpoint = loaded
    with Image.open(path) as image:
        batch = build_eval_transform()(image.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        probabilities = torch.softmax(model(batch), dim=1)[0].tolist()
    return top_candidates(probabilities, labels, 3)


def render_prices(store: Store, product_id: str) -> None:
    places = {place.id: place for place in store.list_establishments(active_only=False)}
    records = [record for record in store.list_prices(product_id) if record.validation_status == "valid"]
    if not records:
        st.caption("Nenhum preço válido registrado para este produto.")
        return
    middle = median([record.price for record in records])
    st.markdown(f"Mediana **R$ {format_price(middle) if middle is not None else '—'}**")
    for record in sorted(records, key=lambda item: item.price)[:3]:
        place = places.get(record.establishment_id)
        shop = place.name if place is not None else "Estabelecimento"
        st.write(f"R$ {format_price(record.price)} · {shop}")
    if len(records) > 3:
        st.caption(f"Mais {len(records) - 3} registro(s) no banco.")
    if any(record.offer_conditions == TEST_OFFER for record in records):
        st.caption("Preço demonstrativo. Não é coleta de mercado.")


def open_prices(product_id: str) -> None:
    st.session_state["product_id"] = product_id
    st.session_state["nav"] = "Preços"


def visual_neighbors(path: Path) -> list[dict[str, object]]:
    from classification.similarity import embed_file, nearest_products

    model, index = similarity_index()
    query = embed_file(model, path)
    return nearest_products(query, index["vectors"], index["product_ids"], index["paths"], k=3)


@st.cache_resource
def similarity_index():
    from classification.similarity import load_encoder, load_or_build_index

    model = load_encoder()
    index = load_or_build_index(
        model,
        ROOT / "data" / "brazilian_products",
        ROOT / "data" / "processed" / "brazilian_embeddings.pt",
    )
    return model, index


def reference_image(product_id: str) -> Path | None:
    folder = ROOT / "data" / "brazilian_products" / "images" / product_id
    files = sorted(folder.glob("*.jpg"))
    return files[0] if files else None


def rank_category(path: Path, product_ids: set[str]) -> dict[str, float]:
    import torch

    from classification.similarity import embed_file

    _model, index = similarity_index()
    query = embed_file(_model, path)
    scores: dict[str, float] = {}
    vectors = index["vectors"]
    for product_id, vector in zip(index["product_ids"], vectors, strict=False):
        if str(product_id) not in product_ids:
            continue
        score = float(torch.dot(vector, query))
        current = scores.get(str(product_id))
        if current is None or score > current:
            scores[str(product_id)] = score
    return scores


def page_scan(context: dict) -> None:
    st.title("Escanear")
    st.caption(
        "Este aplicativo é uma demonstração acadêmica de técnicas de visão computacional. "
        "Os resultados são experimentais e foram obtidos utilizando um conjunto limitado de imagens."
    )
    checkpoint_path = visual_checkpoint_path()
    loaded = cached_classifier(str(checkpoint_path))
    if loaded is not None:
        _model, labels, checkpoint = loaded
        with st.expander("Modelo usado nesta tela"):
            st.write(f"Arquitetura: {checkpoint.get('architecture')}")
            st.write(f"Categorias de saída: {len(labels)}")
            st.write("Entrada: 224 × 224")
            st.write(f"Checkpoint: {checkpoint_path.name}")
            st.write(f"Etapa: {checkpoint.get('stage', 'demonstração')}")
    camera = st.camera_input("Capturar imagem", key="camera_produto")
    upload = st.file_uploader(
        "Ou escolher uma foto",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        key="upload_produto",
    )
    chosen = camera or upload
    if chosen is not None:
        path = save_upload(chosen, "_produtos")
        st.image(str(path), width="stretch")
        issues = [issue for issue in validate_image(path) if issue["level"] == "error"]
        if issues:
            st.dataframe(pd.DataFrame(issues), width="stretch")
        else:
            checkpoint_path = visual_checkpoint_path()
            checkpoint = load_checkpoint(checkpoint_path)
            if checkpoint is None or checkpoint.get("task") != "categoria":
                st.warning("O classificador de categoria ainda não foi gravado.")
            else:
                with st.spinner("Identificando a foto..."):
                    candidates = classify_saved_image(path, checkpoint)
                products = context["catalog"].list_active()
                by_category: dict[str, list] = {}
                for product in products:
                    by_category.setdefault(product.category, []).append(product)
                if candidates:
                    st.caption(
                        " · ".join(
                            f"{candidate['rotulo']} {float(candidate['probabilidade']):.0%}"
                            for candidate in candidates
                        )
                    )
                    category = str(candidates[0]["rotulo"])
                    shown = list(by_category.get(category, []))
                    scores = rank_category(path, {product.id for product in shown}) if shown else {}
                    shown.sort(key=lambda product: scores.get(product.id, 0.0), reverse=True)
                    st.subheader(category)
                    if shown:
                        st.session_state["product_id"] = shown[0].id
                    for product in shown:
                        with st.container(border=True):
                            image_path = reference_image(product.id)
                            if image_path is not None:
                                st.image(str(image_path), width="stretch")
                            st.markdown(f"**{product.name}**")
                            st.caption(
                                f"{product.brand} · {product.quantity} {product.unit} · "
                                f"{product.variant or 'sem variante'}"
                            )
                            render_prices(context["store"], product.id)
                            st.button(
                                "Comparar este produto",
                                key=f"match_{product.id}",
                                on_click=open_prices,
                                args=(product.id,),
                                width="stretch",
                            )
    with st.expander("Escolher outro produto"):
        products = context["catalog"].list_active()
        if not products:
            st.info("O catálogo comercial ainda não tem produtos.")
        else:
            labels = {product_label(product): product.id for product in products}
            selected = st.selectbox("Produto", list(labels), key="scan_select", label_visibility="collapsed")
            st.button(
                "Abrir este produto",
                key="scan_confirm",
                on_click=open_prices,
                args=(labels[selected],),
                width="stretch",
            )


def page_search(context: dict) -> None:
    st.title("Buscar")
    query = st.text_input("Nome, marca ou categoria", key="busca")
    if query:
        found = context["catalog"].search(query)
        if not found:
            st.info("Nenhum produto ativo corresponde à pesquisa.")
        for product in found:
            if st.button(product_label(product), key=f"pick_{product.id}"):
                st.session_state["product_id"] = product.id
                st.success("Produto selecionado para a consulta de preço.")
    with st.expander("Cadastrar produto"):
        with st.form("cadastro_produto"):
            name = st.text_input("Nome comercial")
            brand = st.text_input("Marca")
            category = st.text_input("Categoria")
            variant = st.text_input("Variante")
            quantity = st.text_input("Quantidade", value="1")
            unit = st.selectbox("Unidade", ["g", "kg", "ml", "L", "un"])
            barcode = st.text_input("Código de barras, se existir")
            submitted = st.form_submit_button("Cadastrar")
        if submitted:
            try:
                product = context["catalog"].register(
                    name=name,
                    brand=brand,
                    category=category,
                    variant=variant,
                    quantity=quantity,
                    unit=unit,
                    barcode=barcode or None,
                )
            except (IdentityError, StoreError) as exc:
                st.error(str(exc))
            else:
                st.session_state["product_id"] = product.id
                st.success(f"Produto {product.id} cadastrado. Nenhum código de barras foi gerado.")


def page_prices(context: dict) -> None:
    st.title("Preços")
    products = context["catalog"].list_active()
    if not products:
        st.info("Cadastre um produto antes de comparar um preço.")
        return
    labels = {product_label(product): product.id for product in products}
    current = st.session_state.get("product_id")
    options = list(labels)
    index = 0
    if current in labels.values():
        index = list(labels.values()).index(current)
    selected = st.selectbox("Produto", options, index=index, key="price_product")
    product_id = labels[selected]
    st.session_state["product_id"] = product_id
    typed = st.text_input("Preço encontrado, por exemplo 5,49", key="preco_digitado")
    price_type = st.selectbox(
        "Tipo do preço encontrado",
        ["regular", "promotional", "loyalty", "other"],
        format_func=lambda code: {
            "regular": "Regular",
            "promotional": "Promocional",
            "loyalty": "Condicionado a programa de fidelidade",
            "other": "Outros",
        }[code],
    )
    city = st.text_input("Cidade da comparação")
    state = st.text_input("UF", max_chars=2)
    unit_comparison = st.checkbox(
        "Comparar por unidade com outras embalagens da mesma marca e variante",
        value=False,
    )
    label_photo = st.file_uploader(
        "Fotografia da etiqueta",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        key="upload_etiqueta",
    )
    if label_photo is not None:
        path = save_upload(label_photo, "_etiquetas")
        st.image(str(path), width="stretch")
        reading = read_label(path)
        st.write("A leitura não assume que um número da imagem seja o preço do produto.")
        if reading["mecanismo"] == "indisponivel":
            st.info(str(reading.get("mensagem")))
        candidates = reading["candidatos"]
        if not candidates:
            st.info("Nenhum candidato monetário foi extraído. Digite o valor para confirmar.")
        for position, candidate in enumerate(candidates):
            st.write(
                f"Candidato: {candidate['texto_original']} → {candidate['valor']}. "
                f"Confiança: {candidate['confianca'] if candidate['confianca'] is not None else 'não informada'}."
            )
            if st.button(f"Confirmar {candidate['valor']}", key=f"ocr_{position}"):
                st.session_state["preco_confirmado"] = candidate["valor"]
                st.success("Valor confirmado. Ele ainda precisa ser enviado na comparação.")
    confirmed = st.session_state.get("preco_confirmado") or typed
    if st.button("Comparar preço confirmado", key="comparar"):
        if confirmed.strip() == "":
            st.error("Informe ou confirme um preço.")
        else:
            try:
                report = context["engine"].compare(
                    product_id=product_id,
                    informed_price=confirmed,
                    state=state,
                    city=city or None,
                    basis="unit" if unit_comparison else "package",
                    confirm_unit_comparison=unit_comparison,
                )
            except (MoneyError, StoreError, IdentityError) as exc:
                st.error(str(exc))
            else:
                show_report(report, context["catalog"].get(product_id))
    with st.expander("Registrar uma observação confirmada neste banco local"):
        places = context["store"].list_establishments()
        with st.form("novo_estabelecimento"):
            shop_name = st.text_input("Nome do estabelecimento")
            shop_city = st.text_input("Cidade do estabelecimento")
            shop_state = st.text_input("UF do estabelecimento", max_chars=2)
            shop_neighborhood = st.text_input("Bairro, se quiser informar")
            create_shop = st.form_submit_button("Cadastrar estabelecimento")
        if create_shop:
            try:
                context["store"].register_establishment(
                    name=shop_name,
                    city=shop_city,
                    state=shop_state,
                    neighborhood=shop_neighborhood or None,
                )
            except (StoreError, IdentityError) as exc:
                st.error(str(exc))
            else:
                st.success("Estabelecimento cadastrado.")
                st.rerun()
        if places:
            with st.form("nova_observacao"):
                place_labels = {f"{place.name} — {place.city}/{place.state}": place.id for place in places}
                place_choice = st.selectbox("Estabelecimento", list(place_labels))
                observed_price = st.text_input("Preço observado")
                observed_type = st.selectbox(
                    "Tipo",
                    ["regular", "promotional", "loyalty", "other"],
                    key="tipo_observacao",
                )
                conditions = st.text_input("Condições da oferta, se houver")
                source = st.selectbox(
                    "Fonte",
                    ["manual", "label_photo", "consumer_report", "authorized_public"],
                )
                save_observation = st.form_submit_button("Gravar observação válida")
            if save_observation:
                try:
                    context["store"].register_price(
                        product_id=product_id,
                        establishment_id=place_labels[place_choice],
                        price=observed_price,
                        observed_on=date.today(),
                        source_code=source,
                        price_type=observed_type,
                        offer_conditions=conditions,
                        validation_status="valid",
                    )
                except (MoneyError, StoreError) as exc:
                    st.error(str(exc))
                else:
                    st.success("Observação gravada como válida, com a fonte escolhida.")


def show_report(report, product) -> None:
    st.subheader(product.name)
    st.write(f"{product.brand} · {product.variant or 'sem variante'} · {product.quantity} {product.unit}")
    st.write(f"Preço informado da embalagem: R$ {format_price(report.package_price)}")
    if report.price_basis == "unidade":
        st.write(f"Preço por {report.unit_name}: {report.informed_price}")
    region = report.region_state or "não informada"
    if report.region_city:
        region = f"{report.region_city}/{region}"
    st.write(f"Região considerada: {region}")
    if report.status == INSUFFICIENT:
        st.warning("DADOS_INSUFICIENTES")
        for reason in report.reasons:
            st.write(REASON_TEXT.get(reason, reason))
        st.write(f"Registros utilizáveis na região: {report.count}")
        st.write(f"Estabelecimentos independentes: {report.establishment_count}")
    else:
        st.write(f"Classificação: {report.classification}")
        st.write(f"Mediana: {report.median}")
        st.write(f"Preço médio: {report.mean}")
        st.write(f"Menor preço: {report.minimum}")
        st.write(f"Maior preço: {report.maximum}")
        st.write(f"Desvio padrão dos registros: {report.population_std}")
        st.write(f"Primeiro quartil: {report.q1}")
        st.write(f"Terceiro quartil: {report.q3}")
        st.write(f"Diferença percentual em relação à mediana: {report.percent_vs_median}")
        st.write(f"Diferença percentual em relação à média: {report.percent_vs_mean}")
        st.write(f"Quantidade de registros: {report.count}")
        st.write(f"Estabelecimentos: {report.establishment_count}")
        st.write(f"Data mais recente entre os registros usados: {report.latest_observation}")
        promo = "Preços promocionais e de fidelidade ficaram fora da referência."
        if not report.promotional_excluded:
            promo = "A referência inclui preços promocionais e de fidelidade."
        st.write(promo)
    for limitation in report.limitations:
        st.caption(limitation)
    st.caption(f"Base da comparação: {report.price_basis}. Produtos considerados: {', '.join(report.product_ids) or 'nenhum'}.")


def page_info(context: dict) -> None:
    st.title("Sobre")
    st.write(
        "O RPC continua reservado aos experimentos de visão computacional. "
        "Ele não é fonte de preços brasileiros. O catálogo comercial começa vazio e a lista de 15 produtos "
        "será aprovada antes da coleta."
    )
    st.markdown("**Visão computacional**")
    summary = context["summary"]
    inventory = context["inventory"]
    st.write(f"Classes preliminares do RPC: {summary['n_categories']}")
    st.write(f"Imagens RPC neste disco: {inventory['local_image_files']}")
    st.write(f"Dispositivo: {context['device']['selected']} · PyTorch {context['device']['torch_version']}")
    st.write("MobileNetV3-Large, ResNet18, YOLO e o fluxo híbrido permanecem sem treino.")
    st.json(context["mapping"])
    metrics_dir = resolve_path(context["config"]["paths"]["results"]) / "metrics"
    files = sorted(metrics_dir.glob("*.json")) if metrics_dir.is_dir() else []
    if not files:
        st.info("Nenhuma métrica experimental foi produzida. Não há acurácia, mAP nem resultado de OCR para exibir.")
    else:
        for path in files:
            st.json(json.loads(path.read_text(encoding="utf-8")))
    policy = context["config"]["pricing"]
    st.markdown("**Limites atuais da comparação**")
    st.json(policy)
    st.caption(LEGAL_LIMITATION)


def main() -> None:
    inject_app_style()
    context = load_context()
    if "nav" not in st.session_state:
        st.session_state["nav"] = "Escanear"
    st.markdown('<p class="app-mark">Preço na gôndola</p>', unsafe_allow_html=True)
    sections = ["Escanear", "Buscar", "Preços", "Sobre"]
    columns = st.columns(len(sections))
    for column, section in zip(columns, sections, strict=True):
        with column:
            selected = st.session_state["nav"] == section
            if st.button(
                section,
                key=f"aba_{section}",
                type="primary" if selected else "secondary",
                width="stretch",
            ):
                st.session_state["nav"] = section
                st.rerun()
    page = st.session_state["nav"]
    if page == "Escanear":
        page_scan(context)
    elif page == "Buscar":
        page_search(context)
    elif page == "Preços":
        page_prices(context)
    else:
        page_info(context)


main()
