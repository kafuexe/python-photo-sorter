from pathlib import Path
from src.models.processing_config import ProcessingConfig


class TestProcessingConfig:
    def test_defaults(self):
        c = ProcessingConfig(input_dir="in", output_dir="out")
        assert c.input_dir == Path("in")
        assert c.output_dir == Path("out")
        assert c.date_format == "%Y/%m/%d"
        assert c.action == "copy"
        assert c.selected_extensions == []
        assert c.handle_unknown is True
        assert c.unknown_folder_name == ".unknown"

    def test_paths_converted_to_path(self):
        c = ProcessingConfig(input_dir="/some/dir", output_dir="/other/dir")
        assert isinstance(c.input_dir, Path)
        assert isinstance(c.output_dir, Path)

    def test_to_dict(self):
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
        assert "action" not in d

    def test_from_dict(self):
        d = {
            "input_dir": "/in",
            "output_dir": "/out",
            "date_format": "%Y",
            "selected_extensions": ["mp4"],
            "handle_unknown": False,
        }
        c = ProcessingConfig.from_dict(d, action="move")
        assert c.input_dir == Path("/in")
        assert c.action == "move"
        assert c.selected_extensions == ["mp4"]
        assert c.handle_unknown is False

    def test_from_dict_defaults(self):
        c = ProcessingConfig.from_dict({})
        assert c.date_format == "%Y/%m/%d"
        assert c.selected_extensions == []
        assert c.handle_unknown is True

    def test_roundtrip(self):
        original = ProcessingConfig(
            input_dir="/a",
            output_dir="/b",
            date_format="%Y/%m",
            selected_extensions=["jpg"],
            handle_unknown=True,
        )
        restored = ProcessingConfig.from_dict(original.to_dict(), action="copy")
        assert restored.input_dir == original.input_dir
        assert restored.output_dir == original.output_dir
        assert restored.date_format == original.date_format
        assert restored.selected_extensions == original.selected_extensions
        assert restored.handle_unknown == original.handle_unknown
