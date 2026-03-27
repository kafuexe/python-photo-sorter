from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class FileStatus(Enum):
    pending = "pending"
    success = "success"
    skipped = "skipped"
    error = "error"
    unknown = "unknown"


@dataclass
class FileResult:
    source: Path
    destination: Path | None = None
    status: FileStatus = FileStatus.pending
    error: str | None = None
    metadata: dict = field(default_factory=dict)
