from __future__ import annotations

from pathlib import Path

import pandas as pd

from datasets.catalog import correspondence_status, load_rpc_catalog, summarize_catalog
from datasets.manifest import (
    SCENE_COLUMNS,
    SINGLE_IMAGE_COLUMNS,
    leakage_report,
    missing_columns,
    validate_manifest_values,
)
from datasets.rpc_preliminary import META_CATEGORY_PT, iter_preliminary_classes
from datasets.rpc_reference import CAPTURE, PUBLISHED_CLUTTER, PUBLISHED_SPLITS, inspect_local_rpc, published_totals


def test_published_counts_are_internally_consistent() -> None:
    totals = published_totals()
    assert totals["images"] == CAPTURE["total_images"] == 83739
    assert totals["checkout_objects_from_splits"] == CAPTURE["checkout_objects"] == 367935
    assert totals["clutter_images"] == CAPTURE["checkout_images"] == 30000
    assert totals["clutter_objects"] == CAPTURE["checkout_objects"]
    assert round(PUBLISHED_SPLITS["val"]["objects"] / PUBLISHED_SPLITS["val"]["images"], 2) == 12.27
    assert round(PUBLISHED_SPLITS["test"]["objects"] / PUBLISHED_SPLITS["test"]["images"], 2) == 12.26
    assert round(PUBLISHED_CLUTTER["easy"]["objects"] / 10000, 2) == 7.15
    assert round(PUBLISHED_CLUTTER["medium"]["objects"] / 10000, 2) == 12.30
    assert round(PUBLISHED_CLUTTER["hard"]["objects"] / 10000, 2) == 17.35


def test_local_rpc_absence_is_reported(project_root: Path) -> None:
    report = inspect_local_rpc(project_root / "data" / "public" / "rpc")
    assert report["status"] == "absent"
    assert report["local_image_files"] == 0
    assert report["published_images"] == 83739


def test_preliminary_catalog_has_200_ids_and_17_groups() -> None:
    rows = iter_preliminary_classes()
    ids = [int(row["category_id"]) for row in rows]
    assert ids == list(range(1, 201))
    assert len(META_CATEGORY_PT) == 17
    assert len({row["supercategory"] for row in rows}) == 17
    assert rows[0]["name"] == "1_puffed_food"
    assert rows[20]["name"] == "21_dried_fruit"
    assert rows[78]["name"] == "79_alcohol"
    assert rows[80]["name"] == "81_drink"
    assert rows[199]["name"] == "200_stationery"


def test_catalog_file_matches_preliminary_source(project_root: Path) -> None:
    frame = load_rpc_catalog(project_root / "configs" / "catalogs" / "rpc_classes.csv")
    summary = summarize_catalog(frame)
    assert summary["n_categories"] == 200
    assert summary["n_supercategories"] == 17
    assert summary["chinese_names_filled"] == 0
    assert "preliminary_pending_official_json" in summary["verification_status"]
    expected_names = [row["name"] for row in iter_preliminary_classes()]
    assert frame["name"].tolist() == expected_names


def test_empty_mapping_keeps_experiments_separate(tmp_path: Path) -> None:
    mapping = tmp_path / "class_mapping.csv"
    mapping.write_text(
        "custom_class_id,custom_class_name,rpc_category_id,rpc_category_name,match_type,evidence,notes\n",
        encoding="utf-8",
    )
    from datasets.catalog import load_class_mapping

    status = correspondence_status(load_class_mapping(mapping))
    assert status["experiment"] == "separate"
    assert status["n_usable_matches"] == 0


def test_session_leakage_is_detected() -> None:
    frame = pd.DataFrame(
        [
            {"image_id": "a", "session_id": "s1", "split": "train", "sha256": "h1", "relative_path": "a.jpg", "capture_group": "g1", "parent_image_id": ""},
            {"image_id": "b", "session_id": "s1", "split": "test", "sha256": "h2", "relative_path": "b.jpg", "capture_group": "g2", "parent_image_id": ""},
        ]
    )
    report = leakage_report(frame, extra_group_columns=("session_id",))
    assert report["leakage_count"] >= 1
    assert any(item["group"] == "session_id" for item in report["findings"])
    assert leakage_report(frame)["leakage_count"] == 0


def test_clean_split_has_no_leakage() -> None:
    frame = pd.DataFrame(
        [
            {"image_id": "a", "session_id": "s1", "split": "train", "sha256": "h1", "relative_path": "a.jpg", "capture_group": "g1", "parent_image_id": ""},
            {"image_id": "b", "session_id": "s2", "split": "test", "sha256": "h2", "relative_path": "b.jpg", "capture_group": "g2", "parent_image_id": ""},
        ]
    )
    assert leakage_report(frame)["leakage_count"] == 0


def test_manifest_templates_have_required_columns(project_root: Path) -> None:
    single = pd.read_csv(project_root / "data" / "custom" / "manifests" / "images_template.csv")
    scenes = pd.read_csv(project_root / "data" / "custom" / "manifests" / "scenes_template.csv")
    assert missing_columns(single, SINGLE_IMAGE_COLUMNS) == []
    assert missing_columns(scenes, SCENE_COLUMNS) == []
    issues = validate_manifest_values(single.astype(str))
    assert any(issue["code"] == "empty_manifest" for issue in issues)
