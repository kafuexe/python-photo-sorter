from datetime import datetime
from pathlib import Path

import pytest

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


@pytest.fixture
def resolver():
    return DestinationResolver()


class TestDestinationResolverConfig:
    def test_is_subclass_of_base(self):
        assert issubclass(DestinationResolver, BaseDestinationResolver)


class TestDestinationResolverWithDate:
    @pytest.mark.parametrize("date_format, expected_subdir", [
        ("%Y/%m/%d", "2024/06/15"),
        ("%Y-%m",    "2024-06"),
        ("%Y%m%d",   "20240615"),
        ("%Y",       "2024"),
    ])
    def test_date_format_produces_correct_path(self, resolver, date_format, expected_subdir):
        config = make_config(date_format=date_format)
        metadata = {"date": datetime(2024, 6, 15, 14, 30)}

        result = resolver.resolve(Path("/in/photo.jpg"), metadata, config)
        assert result == Path(f"/out/{expected_subdir}/photo.jpg")

    def test_preserves_filename_with_spaces(self, resolver):
        config = make_config()
        metadata = {"date": datetime(2024, 1, 1)}

        result = resolver.resolve(Path("/in/my vacation photo.jpg"), metadata, config)
        assert result.name == "my vacation photo.jpg"


class TestDestinationResolverWithoutDate:
    def test_handle_unknown_routes_to_unknown_folder(self, resolver):
        config = make_config(handle_unknown=True, unknown_folder_name=".nodate")
        result = resolver.resolve(Path("/in/photo.jpg"), {}, config)
        assert result == Path("/out/.nodate/photo.jpg")

    def test_handle_unknown_disabled_returns_none(self, resolver):
        config = make_config(handle_unknown=False)
        result = resolver.resolve(Path("/in/photo.jpg"), {}, config)
        assert result is None

    def test_date_key_is_none_treated_as_no_date(self, resolver):
        """metadata has 'date' key but value is None — should route to unknown."""
        config = make_config(handle_unknown=True, unknown_folder_name=".nodate")
        result = resolver.resolve(Path("/in/photo.jpg"), {"date": None}, config)
        assert result == Path("/out/.nodate/photo.jpg")

    def test_date_none_with_unknown_disabled_returns_none(self, resolver):
        config = make_config(handle_unknown=False)
        result = resolver.resolve(Path("/in/photo.jpg"), {"date": None}, config)
        assert result is None
