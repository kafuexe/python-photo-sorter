from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProcessingConfig:
    input_dir: Path
    output_dir: Path
    date_format: str = "%Y/%m/%d"
    action: str = "copy"
    selected_extensions: list[str] = None
    handle_unknown: bool = True
    unknown_folder_name: str = ".unknown"

    def __post_init__(self):
        if self.selected_extensions is None:
            self.selected_extensions = []
        self.input_dir = Path(self.input_dir)
        self.output_dir = Path(self.output_dir)

    def to_dict(self) -> dict:
        return {
            "input_dir": str(self.input_dir),
            "output_dir": str(self.output_dir),
            "date_format": self.date_format,
            "selected_extensions": self.selected_extensions,
            "handle_unknown": self.handle_unknown,
            "unknown_folder_name": self.unknown_folder_name,
        }

    @classmethod
    def from_dict(cls, data: dict, action: str = "copy") -> "ProcessingConfig":
        return cls(
            input_dir=Path(data.get("input_dir", "")),
            output_dir=Path(data.get("output_dir", "")),
            date_format=data.get("date_format", "%Y/%m/%d"),
            action=action,
            selected_extensions=data.get("selected_extensions", []),
            handle_unknown=data.get("handle_unknown", True),
            unknown_folder_name=data.get("unknown_folder_name", ".unknown"),
        )
