import json

from src.services.config_service import ConfigService


class TestConfigService:
    def test_defaults_when_no_file(self, tmp_path):
        path = tmp_path / "config.json"
        cs = ConfigService(config_path=path)

        config = cs.load()
        assert config["date_format"] == "%Y/%m/%d"
        assert config["handle_unknown"] is True
        assert isinstance(config["selected_extensions"], list)

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "config.json"
        cs = ConfigService(config_path=path)

        data = {
            "input_dir": "/my/input",
            "output_dir": "/my/output",
            "date_format": "%Y-%m",
            "selected_extensions": ["jpg"],
            "handle_unknown": False,
        }
        cs.save(data)
        loaded = cs.load()

        assert loaded["input_dir"] == "/my/input"
        assert loaded["date_format"] == "%Y-%m"
        assert loaded["handle_unknown"] is False

    def test_load_merges_with_defaults(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"input_dir": "/custom"}))

        cs = ConfigService(config_path=path)
        config = cs.load()

        assert config["input_dir"] == "/custom"
        assert config["date_format"] == "%Y/%m/%d"  # default filled in

    def test_corrupt_json_returns_defaults(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text("not valid json {{{")

        cs = ConfigService(config_path=path)
        config = cs.load()

        assert config["date_format"] == "%Y/%m/%d"

    def test_get_defaults(self, tmp_path):
        cs = ConfigService(config_path=tmp_path / "c.json")
        defaults = cs.get_defaults()
        assert "input_dir" in defaults
        assert "output_dir" in defaults
        assert "date_format" in defaults

    def test_save_creates_file(self, tmp_path):
        path = tmp_path / "config.json"
        assert not path.exists()

        ConfigService(config_path=path).save({"key": "value"})
        assert path.exists()

        data = json.loads(path.read_text())
        assert data["key"] == "value"
