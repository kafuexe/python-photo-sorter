from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FileResult:
    source: Path
    destination: Path | None = None
    status: str = "pending"  # "success", "skipped", "error", "unknown"
    error: str | None = None
    metadata: dict = field(default_factory=dict)
