from datetime import datetime
from pathlib import Path

from src.models.processing_config import ProcessingConfig
from src.steps.destination_resolver import DestinationResolver, BaseDestinationResolver


def make_config(**overrides):
    defaults = {
        "input_dir": "/in",
        "output_dir": "/out",
        "date_format": "%Y/%m/%d",
        "action": "copy",
        "selected_extensions": ["jpg"],
        "handle_unknown": True,
        "unknown_folder_name": ".unknown",
    }
    defaults.update(overrides)
    return ProcessingConfig(**defaults)


class TestDestinationResolver:
    def test_is_subclass_of_base(self):
        assert issubclass(DestinationResolver, BaseDestinationResolver)

    def test_resolves_with_date(self):
        config = make_config()
        metadata = {"date": datetime(2024, 6, 15, 14, 30)}
        file = Path("/in/photo.jpg")

        result = DestinationResolver().resolve(file, metadata, config)
        assert result == Path("/out/2024/06/15/photo.jpg")

    def test_custom_format(self):
        config = make_config(date_format="%Y-%m")
        metadata = {"date": datetime(2024, 6, 15)}
        file = Path("/in/photo.jpg")

        result = DestinationResolver().resolve(file, metadata, config)
        assert result == Path("/out/2024-06/photo.jpg")

    def test_no_date_with_handle_unknown(self):
        config = make_config(handle_unknown=True, unknown_folder_name=".nodate")
        file = Path("/in/photo.jpg")

        result = DestinationResolver().resolve(file, {}, config)
        assert result == Path("/out/.nodate/photo.jpg")

    def test_no_date_without_handle_unknown(self):
        config = make_config(handle_unknown=False)
        file = Path("/in/photo.jpg")

        result = DestinationResolver().resolve(file, {}, config)
        assert result is None

    def test_preserves_filename(self):
        config = make_config()
        metadata = {"date": datetime(2024, 1, 1)}
        file = Path("/in/my vacation photo.jpg")

        result = DestinationResolver().resolve(file, metadata, config)
        assert result.name == "my vacation photo.jpg"
