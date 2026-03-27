from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

import pytest

from src.handlers.pymediainfo_handler import PyMediaInfoHandler


class MockTrack:
    """Mock MediaInfo track with configurable attributes."""

    def __init__(self, track_type: str, **kwargs):
        self.track_type = track_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockMediaInfo:
    """Mock MediaInfo.parse() result."""

    def __init__(self, tracks: list):
        self.tracks = tracks


@pytest.fixture
def mock_pymediainfo():
    """Create a mock pymediainfo module."""
    mock_module = MagicMock()
    mock_module.MediaInfo.can_parse.return_value = True
    return mock_module


@pytest.fixture
def handler(mock_pymediainfo):
    """Create handler with mocked pymediainfo module."""
    with patch.dict(sys.modules, {"pymediainfo": mock_pymediainfo}):
        return PyMediaInfoHandler()


class TestPyMediaInfoHandlerConfig:
    def test_supported_extensions_include_common_video_types(self, handler):
        exts = handler.supported_extensions()
        assert set(exts) >= {"mp4", "mov", "avi", "mkv", "wmv", "flv", "3gp", "webm"}

    def test_priority_is_external_tool_tier(self, handler):
        assert handler.priority() == 50


class TestPyMediaInfoAvailability:
    def test_available_when_can_parse_returns_true(self):
        mock_module = MagicMock()
        mock_module.MediaInfo.can_parse.return_value = True
        with patch.dict(sys.modules, {"pymediainfo": mock_module}):
            handler = PyMediaInfoHandler()
            assert handler._available is True

    def test_unavailable_when_can_parse_returns_false(self):
        mock_module = MagicMock()
        mock_module.MediaInfo.can_parse.return_value = False
        with patch.dict(sys.modules, {"pymediainfo": mock_module}):
            handler = PyMediaInfoHandler()
            assert handler._available is False

    def test_unavailable_when_import_fails(self):
        # Remove pymediainfo from modules to simulate ImportError
        with patch.dict(sys.modules, {"pymediainfo": None}):
            handler = PyMediaInfoHandler()
            assert handler._available is False

    def test_unavailable_when_can_parse_raises(self):
        mock_module = MagicMock()
        mock_module.MediaInfo.can_parse.side_effect = RuntimeError("Native lib failed")
        with patch.dict(sys.modules, {"pymediainfo": mock_module}):
            handler = PyMediaInfoHandler()
            assert handler._available is False

    def test_unavailable_handler_returns_empty(self, handler):
        handler._available = False
        result = handler.extract_metadata(Path("video.mp4"))
        assert result == {}


class TestPyMediaInfoDateExtraction:
    def test_extracts_date_from_tagged_date(self, mock_pymediainfo, handler):
        mock_pymediainfo.MediaInfo.parse.return_value = MockMediaInfo(
            [MockTrack("General", Tagged_Date="2024-06-15 14:30:00")]
        )

        with patch.dict(sys.modules, {"pymediainfo": mock_pymediainfo}):
            result = handler.extract_metadata(Path("video.mp4"))
        assert result["date"] == datetime(2024, 6, 15, 14, 30, 0)

    def test_extracts_date_from_encoded_date(self, mock_pymediainfo, handler):
        mock_pymediainfo.MediaInfo.parse.return_value = MockMediaInfo(
            [MockTrack("General", Encoded_Date="2023-03-10 08:00:00")]
        )

        with patch.dict(sys.modules, {"pymediainfo": mock_pymediainfo}):
            result = handler.extract_metadata(Path("video.mp4"))
        assert result["date"] == datetime(2023, 3, 10, 8, 0, 0)

    def test_extracts_date_from_file_modified_date(self, mock_pymediainfo, handler):
        mock_pymediainfo.MediaInfo.parse.return_value = MockMediaInfo(
            [MockTrack("General", File_Modified_Date="2020-01-01 00:00:00")]
        )

        with patch.dict(sys.modules, {"pymediainfo": mock_pymediainfo}):
            result = handler.extract_metadata(Path("video.mp4"))
        assert result["date"] == datetime(2020, 1, 1)

    def test_tag_priority_tagged_date_wins(self, mock_pymediainfo, handler):
        mock_pymediainfo.MediaInfo.parse.return_value = MockMediaInfo(
            [
                MockTrack(
                    "General",
                    Tagged_Date="2024-01-01 00:00:00",
                    Encoded_Date="2025-01-01 00:00:00",
                    File_Modified_Date="2026-01-01 00:00:00",
                )
            ]
        )

        with patch.dict(sys.modules, {"pymediainfo": mock_pymediainfo}):
            result = handler.extract_metadata(Path("video.mp4"))
        assert result["date"] == datetime(2024, 1, 1)

    def test_tag_priority_encoded_date_second(self, mock_pymediainfo, handler):
        mock_pymediainfo.MediaInfo.parse.return_value = MockMediaInfo(
            [
                MockTrack(
                    "General",
                    Encoded_Date="2025-01-01 00:00:00",
                    File_Modified_Date="2026-01-01 00:00:00",
                )
            ]
        )

        with patch.dict(sys.modules, {"pymediainfo": mock_pymediainfo}):
            result = handler.extract_metadata(Path("video.mp4"))
        assert result["date"] == datetime(2025, 1, 1)


class TestPyMediaInfoUTCPrefix:
    def test_strips_utc_prefix_from_tagged_date(self, mock_pymediainfo, handler):
        mock_pymediainfo.MediaInfo.parse.return_value = MockMediaInfo(
            [MockTrack("General", Tagged_Date="UTC 2024-06-15 14:30:00")]
        )

        with patch.dict(sys.modules, {"pymediainfo": mock_pymediainfo}):
            result = handler.extract_metadata(Path("video.mp4"))
        assert result["date"] == datetime(2024, 6, 15, 14, 30, 0)

    def test_strips_utc_prefix_from_encoded_date(self, mock_pymediainfo, handler):
        mock_pymediainfo.MediaInfo.parse.return_value = MockMediaInfo(
            [MockTrack("General", Encoded_Date="UTC 2023-12-25 10:00:00")]
        )

        with patch.dict(sys.modules, {"pymediainfo": mock_pymediainfo}):
            result = handler.extract_metadata(Path("video.mp4"))
        assert result["date"] == datetime(2023, 12, 25, 10, 0, 0)


class TestPyMediaInfoFailures:
    def test_empty_tracks_returns_empty(self, mock_pymediainfo, handler):
        mock_pymediainfo.MediaInfo.parse.return_value = MockMediaInfo([])

        with patch.dict(sys.modules, {"pymediainfo": mock_pymediainfo}):
            result = handler.extract_metadata(Path("video.mp4"))
        assert result == {}

    def test_no_general_track_returns_empty(self, mock_pymediainfo, handler):
        mock_pymediainfo.MediaInfo.parse.return_value = MockMediaInfo(
            [MockTrack("Video", Tagged_Date="2024-06-15 14:30:00")]
        )

        with patch.dict(sys.modules, {"pymediainfo": mock_pymediainfo}):
            result = handler.extract_metadata(Path("video.mp4"))
        assert result == {}

    def test_general_track_without_date_fields_returns_empty(
        self, mock_pymediainfo, handler
    ):
        mock_pymediainfo.MediaInfo.parse.return_value = MockMediaInfo(
            [MockTrack("General", Format="MPEG-4", Duration=120000)]
        )

        with patch.dict(sys.modules, {"pymediainfo": mock_pymediainfo}):
            result = handler.extract_metadata(Path("video.mp4"))
        assert result == {}

    def test_invalid_date_string_returns_empty(self, mock_pymediainfo, handler):
        mock_pymediainfo.MediaInfo.parse.return_value = MockMediaInfo(
            [MockTrack("General", Tagged_Date="not a date")]
        )

        with patch.dict(sys.modules, {"pymediainfo": mock_pymediainfo}):
            result = handler.extract_metadata(Path("video.mp4"))
        assert result == {}

    def test_parse_exception_returns_empty(self, mock_pymediainfo, handler):
        mock_pymediainfo.MediaInfo.parse.side_effect = RuntimeError("Native lib error")

        with patch.dict(sys.modules, {"pymediainfo": mock_pymediainfo}):
            result = handler.extract_metadata(Path("video.mp4"))
        assert result == {}


class TestPyMediaInfoParseDate:
    @pytest.mark.parametrize(
        "date_str, expected",
        [
            ("2024-06-15 14:30:00", datetime(2024, 6, 15, 14, 30, 0)),
            ("2020-01-01 00:00:00", datetime(2020, 1, 1)),
            ("2019-12-31 23:59:59", datetime(2019, 12, 31, 23, 59, 59)),
            ("UTC 2024-06-15 14:30:00", datetime(2024, 6, 15, 14, 30, 0)),
            ("UTC 2020-01-01 00:00:00", datetime(2020, 1, 1)),
        ],
    )
    def test_valid_date_strings(self, date_str, expected):
        assert PyMediaInfoHandler._parse_date(date_str) == expected

    @pytest.mark.parametrize(
        "date_str",
        [
            "not a date",
            "",
            "2024:06:15 14:30:00",  # wrong separator (EXIF style)
            "2024-13-01 00:00:00",  # month 13
            "UTC",
            "UTC ",
        ],
    )
    def test_invalid_date_strings_return_none(self, date_str):
        assert PyMediaInfoHandler._parse_date(date_str) is None

    def test_truncates_to_19_chars(self):
        # Extra trailing data after 19 chars should be ignored
        result = PyMediaInfoHandler._parse_date("2024-06-15 14:30:00.123456")
        assert result == datetime(2024, 6, 15, 14, 30, 0)

    def test_strips_whitespace(self):
        result = PyMediaInfoHandler._parse_date("  2024-06-15 14:30:00  ")
        assert result == datetime(2024, 6, 15, 14, 30, 0)

    def test_strips_whitespace_with_utc(self):
        result = PyMediaInfoHandler._parse_date("  UTC 2024-06-15 14:30:00  ")
        assert result == datetime(2024, 6, 15, 14, 30, 0)
