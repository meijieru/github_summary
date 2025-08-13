import pytest

from github_summary.config import load_config
from github_summary.models import Config


@pytest.mark.unit
def test_load_config_success(tmp_path):
    config_content = """
    [github]
    token = "dummy_token"

    [filters.commits]
    since_days = 7

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
    assert config.repositories[1].name == "owner/repo2"
    assert config.repositories[1].filters.commits.author == "test_author"
    assert config.since_last_run is True


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
