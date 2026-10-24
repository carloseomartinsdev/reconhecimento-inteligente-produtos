from __future__ import annotations

from pathlib import Path

import torch

from utils.config import load_config, project_root, resolve_path
from utils.device import get_device
from utils.seed import seeded_generator, set_seed


def test_project_root_is_repository() -> None:
    root = project_root()
    assert (root / "pyproject.toml").is_file()
    assert (root / "src").is_dir()


def test_default_config_uses_relative_paths_and_seed() -> None:
    config = load_config("default.yaml")
    assert config["project"]["seed"] == 42
    assert config["experiments"]["run_training"] is False
    assert config["experiments"]["run_download"] is False
    root = project_root()
    catalog = resolve_path(config["paths"]["catalog_rpc"], root)
    assert catalog.is_relative_to(root)
    assert Path(config["paths"]["rpc_root"]).is_absolute() is False


def test_seed_repeats_torch_sample() -> None:
    set_seed(42)
    first = torch.rand(4)
    set_seed(42)
    second = torch.rand(4)
    assert torch.equal(first, second)


def test_seeded_generator_repeats_permutation() -> None:
    first = torch.randperm(6, generator=seeded_generator(7))
    second = torch.randperm(6, generator=seeded_generator(7))
    assert torch.equal(first, second)


def test_cpu_can_be_forced() -> None:
    device = get_device(prefer_gpu=False)
    assert device.type == "cpu"
