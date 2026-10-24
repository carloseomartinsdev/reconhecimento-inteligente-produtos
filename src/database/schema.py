"""Esquema SQLite.

Os preços ficam em TEXT, no formato decimal canônico, para não passar por REAL.
A troca futura para PostgreSQL substitui a conexão e o tipo da coluna por NUMERIC,
mantendo Decimal na aplicação. O marcador de parâmetro desta etapa é '?'.
"""

from __future__ import annotations

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    variant TEXT NOT NULL DEFAULT '',
    quantity TEXT NOT NULL,
    unit TEXT NOT NULL,
    packaging TEXT NOT NULL DEFAULT '',
    barcode TEXT,
    reference_image TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    commercial_key TEXT NOT NULL UNIQUE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode
    ON products(barcode) WHERE barcode IS NOT NULL;

CREATE TABLE IF NOT EXISTS establishments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    neighborhood TEXT,
    external_id TEXT,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_establishments_external
    ON establishments(external_id) WHERE external_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS price_records (
    id INTEGER PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(id),
    establishment_id INTEGER NOT NULL REFERENCES establishments(id),
    price TEXT NOT NULL,
    observed_on TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES sources(id),
    price_type TEXT NOT NULL,
    offer_conditions TEXT NOT NULL DEFAULT '',
    validation_status TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_prices_product_date
    ON price_records(product_id, observed_on);

CREATE TABLE IF NOT EXISTS model_class_links (
    model_name TEXT NOT NULL,
    class_label TEXT NOT NULL,
    product_id TEXT NOT NULL REFERENCES products(id),
    PRIMARY KEY (model_name, class_label)
);
"""

SOURCE_SEEDS = (
    ("manual", "Coleta manual", "Valor digitado por quem opera o sistema."),
    ("label_photo", "Fotografia de etiqueta", "Valor lido de uma etiqueta e confirmado."),
    ("consumer_report", "Informação enviada pelo consumidor", "Relato de preço enviado pelo consumidor."),
    ("authorized_public", "Fonte pública autorizada", "Série obtida de uma fonte pública com uso permitido."),
)


def init_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(products)")}
    if "packaging" not in columns:
        connection.execute("ALTER TABLE products ADD COLUMN packaging TEXT NOT NULL DEFAULT ''")
    connection.executemany(
        """
        INSERT INTO sources (code, name, description)
        VALUES (?, ?, ?)
        ON CONFLICT(code) DO NOTHING
        """,
        SOURCE_SEEDS,
    )
    connection.commit()
