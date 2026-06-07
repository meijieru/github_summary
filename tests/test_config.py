from pathlib import Path

import pytest

from github_summary.config import load_config
from github_summary.models import Config
from github_summary.paths import get_default_run_dir


@pytest.mark.unit
def test_load_config_success(tmp_path):
    config_content = """
    [github]
    token = "dummy_token"

    [[repositories]]
    name = "owner/repo1"

    [[repositories]]
    name = "owner/repo2"
    [repositories.filters.commits]
    author = "test_author"
    """
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)

    config = load_config(str(config_file))
    assert isinstance(config, Config)
    assert config.repositories[0].name == "owner/repo1"
    assert config.repositories[0].audience is None
    assert config.repositories[1].name == "owner/repo2"
    assert config.repositories[1].filters.commits.author == "test_author"
    assert config.run_dir == str(Path(get_default_run_dir()).resolve())
    assert config.output_dir == str((Path(get_default_run_dir()) / "output").resolve())
    assert config.cache_dir == str((Path(get_default_run_dir()) / "cache").resolve())
    assert config.log_dir == str((Path(get_default_run_dir()) / "log").resolve())
    assert config.since_last_run is True


@pytest.mark.unit
def test_load_config_supports_per_repository_audience(tmp_path):
    config_content = """
    [github]
    token = "dummy_token"

    [llm]
    audience = "mixed"

    [[repositories]]
    name = "owner/user-facing"
    audience = "user"

    [[repositories]]
    name = "owner/internal-lib"
    audience = "maintainer"
    """
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)

    config = load_config(str(config_file))

    assert config.llm is not None
    assert config.llm.audience == "mixed"
    assert config.repositories[0].audience == "user"
    assert config.repositories[1].audience == "maintainer"


@pytest.mark.unit
def test_load_config_rejects_unknown_fields(tmp_path):
    config_content = """
    [github]
    token = "dummy_token"

    [[repositories]]
    name = "owner/repo1"
    output_dir = "wrong-place"
    """
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)

    with pytest.raises(ValueError, match="extra_forbidden"):
        load_config(str(config_file))


@pytest.mark.unit
def test_load_config_resolves_runtime_paths(tmp_path):
    config_content = """
    run_dir = "var/ghsum"
    output_dir = "reports"
    cache_dir = ".cache/ghsum"
    log_dir = "logs"

    [github]
    token = "dummy_token"

    [[repositories]]
    name = "owner/repo1"
    """
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)

    config = load_config(str(config_file))

    assert config.run_dir == str((Path.cwd() / "var/ghsum").resolve())
    assert config.output_dir == str((Path.cwd() / "var/ghsum/reports").resolve())
    assert config.cache_dir == str((Path.cwd() / "var/ghsum/.cache/ghsum").resolve())
    assert config.log_dir == str((Path.cwd() / "var/ghsum/logs").resolve())


@pytest.mark.unit
def test_load_config_uses_xdg_state_home_for_default_run_dir(tmp_path, monkeypatch):
    xdg_state_home = tmp_path / "state"
    monkeypatch.setenv("XDG_STATE_HOME", str(xdg_state_home))
    load_config.cache_clear()

    config_content = """
    [github]
    token = "dummy_token"

    [[repositories]]
    name = "owner/repo1"
    """
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)

    config = load_config(str(config_file))

    assert config.run_dir == str((xdg_state_home / "github-summary").resolve())
    assert config.output_dir == str((xdg_state_home / "github-summary/output").resolve())
    assert config.cache_dir == str((xdg_state_home / "github-summary/cache").resolve())
    assert config.log_dir == str((xdg_state_home / "github-summary/log").resolve())


@pytest.mark.unit
def test_load_config_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("non_existent_file.toml")


@pytest.mark.unit
def test_load_config_invalid(tmp_path):
    config_content = """
    # Missing 'name' in repository
    [[repositories]]
    """
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)

    with pytest.raises(ValueError):
        load_config(str(config_file))
