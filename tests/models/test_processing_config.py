from pathlib import Path

import pytest

from src.models.processing_config import ProcessingConfig


@pytest.fixture
def default_config():
    return ProcessingConfig(input_dir="in", output_dir="out")


class TestProcessingConfigDefaults:
    @pytest.mark.parametrize("attr, expected", [
        ("date_format", "%Y/%m/%d"),
        ("action", "copy"),
        ("selected_extensions", []),
        ("handle_unknown", True),
        ("unknown_folder_name", ".unknown"),
    ])
    def test_default_values(self, default_config, attr, expected):
        assert getattr(default_config, attr) == expected

    def test_paths_converted_to_path_objects(self, default_config):
        assert isinstance(default_config.input_dir, Path)
        assert isinstance(default_config.output_dir, Path)


class TestProcessingConfigSerialization:
    def test_to_dict_includes_expected_keys(self):
        c = ProcessingConfig(
            input_dir="/in",
            output_dir="/out",
            date_format="%Y-%m",
            action="move",
            selected_extensions=["jpg", "png"],
            handle_unknown=False,
            unknown_folder_name=".nodate",
        )
        d = c.to_dict()

        assert d["input_dir"] == str(Path("/in"))
        assert d["output_dir"] == str(Path("/out"))
        assert d["date_format"] == "%Y-%m"
        assert d["selected_extensions"] == ["jpg", "png"]
        assert d["handle_unknown"] is False
        assert d["unknown_folder_name"] == ".nodate"

    def test_to_dict_excludes_action(self):
        d = ProcessingConfig(input_dir="a", output_dir="b", action="move").to_dict()
        assert "action" not in d

    @pytest.mark.parametrize("overrides, expected_attr, expected_val", [
        ({"date_format": "%Y"}, "date_format", "%Y"),
        ({"selected_extensions": ["mp4"]}, "selected_extensions", ["mp4"]),
        ({"handle_unknown": False}, "handle_unknown", False),
    ])
    def test_from_dict_applies_overrides(self, overrides, expected_attr, expected_val):
        c = ProcessingConfig.from_dict(overrides)
        assert getattr(c, expected_attr) == expected_val

    def test_from_dict_with_action(self):
        c = ProcessingConfig.from_dict({"input_dir": "/in", "output_dir": "/out"}, action="move")
        assert c.action == "move"

    @pytest.mark.parametrize("attr, expected", [
        ("date_format", "%Y/%m/%d"),
        ("selected_extensions", []),
        ("handle_unknown", True),
    ])
    def test_from_dict_uses_defaults_for_missing_keys(self, attr, expected):
        c = ProcessingConfig.from_dict({})
        assert getattr(c, attr) == expected

    def test_roundtrip_preserves_values(self):
        original = ProcessingConfig(
            input_dir="/a",
            output_dir="/b",
            date_format="%Y/%m",
            selected_extensions=["jpg"],
            handle_unknown=True,
        )
        restored = ProcessingConfig.from_dict(original.to_dict(), action="copy")

        for attr in ("input_dir", "output_dir", "date_format", "selected_extensions", "handle_unknown"):
            assert getattr(restored, attr) == getattr(original, attr)


class TestProcessingConfigEdgeCases:
    def test_none_selected_extensions_becomes_empty_list(self):
        c = ProcessingConfig(input_dir="a", output_dir="b", selected_extensions=None)
        assert c.selected_extensions == []

    def test_from_dict_with_empty_string_paths(self):
        c = ProcessingConfig.from_dict({"input_dir": "", "output_dir": ""})
        assert c.input_dir == Path("")
        assert c.output_dir == Path("")

    def test_string_paths_converted_to_path(self):
        c = ProcessingConfig(input_dir="/some/dir", output_dir="/other")
        assert isinstance(c.input_dir, Path)
        assert isinstance(c.output_dir, Path)

    def test_path_objects_stay_as_paths(self):
        c = ProcessingConfig(input_dir=Path("/a"), output_dir=Path("/b"))
        assert c.input_dir == Path("/a")
