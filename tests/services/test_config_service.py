import json

import pytest

from src.services.config_service import ConfigService


@pytest.fixture
def config_service(tmp_path):
    return ConfigService(config_path=tmp_path / "config.json")


class TestConfigServiceLoad:
    def test_defaults_when_no_file(self, config_service):
        config = config_service.load()
        assert config["date_format"] == "%Y/%m/%d"
        assert config["handle_unknown"] is True
        assert isinstance(config["selected_extensions"], list)

    def test_merges_partial_file_with_defaults(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"input_dir": "/custom"}))

        config = ConfigService(config_path=path).load()
        assert config["input_dir"] == "/custom"
        assert config["date_format"] == "%Y/%m/%d"  # default filled in

    def test_corrupt_json_returns_defaults(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text("not valid json {{{")

        config = ConfigService(config_path=path).load()
        assert config["date_format"] == "%Y/%m/%d"


class TestConfigServiceSave:
    def test_save_creates_file(self, config_service, tmp_path):
        config_service.save({"key": "value"})
        path = tmp_path / "config.json"
        assert path.exists()
        assert json.loads(path.read_text())["key"] == "value"

    def test_save_and_load_roundtrip(self, config_service):
        data = {
            "input_dir": "/my/input",
            "output_dir": "/my/output",
            "date_format": "%Y-%m",
            "selected_extensions": ["jpg"],
            "handle_unknown": False,
        }
        config_service.save(data)
        loaded = config_service.load()

        assert loaded["input_dir"] == "/my/input"
        assert loaded["date_format"] == "%Y-%m"
        assert loaded["handle_unknown"] is False


class TestConfigServiceDefaults:
    @pytest.mark.parametrize("key", ["input_dir", "output_dir", "date_format"])
    def test_get_defaults_contains_required_keys(self, config_service, key):
        assert key in config_service.get_defaults()

    def test_get_defaults_returns_fresh_copy(self, config_service):
        d1 = config_service.get_defaults()
        d2 = config_service.get_defaults()
        d1["extra_key"] = "mutated"
        assert "extra_key" not in d2


class TestConfigServiceErrors:
    def test_save_raises_config_error_on_bad_path(self, tmp_path):
        from src.errors.exceptions import ConfigError
        bad_path = tmp_path / "nonexistent_dir" / "deep" / "config.json"
        cs = ConfigService(config_path=bad_path)
        with pytest.raises(ConfigError):
            cs.save({"key": "value"})

    def test_unknown_keys_in_file_preserved_on_load(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"input_dir": "/x", "custom_plugin_key": "hello"}))
        config = ConfigService(config_path=path).load()
        assert config["custom_plugin_key"] == "hello"
        assert config["date_format"] == "%Y/%m/%d"  # defaults still merged
