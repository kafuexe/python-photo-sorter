import time
from dataclasses import dataclass, field
from typing import Callable, TypeVar

T = TypeVar("T")


def timed(fn: Callable[[], T]) -> tuple[T, float]:
    """Execute a function and return (result, elapsed_seconds)."""
    start = time.perf_counter()
    result = fn()
    return result, time.perf_counter() - start


@dataclass
class TimingStats:
    """Accumulated timing statistics for pipeline steps."""
    find: float = 0.0
    extract: float = 0.0
    resolve: float = 0.0
    execute: float = 0.0
    total: float = 0.0
    file_count: int = 0
    _per_file: list[dict] = field(default_factory=list)

    def record(self, file: str, extract: float, resolve: float, execute: float) -> None:
        self._per_file.append({
            "file": file,
            "extract": extract,
            "resolve": resolve,
            "execute": execute,
        })

    @property
    def per_file(self) -> list[dict]:
        return self._per_file

    def slowest(self, n: int = 5) -> list[dict]:
        return sorted(
            self._per_file,
            key=lambda f: f["extract"] + f["resolve"] + f["execute"],
            reverse=True
        )[:n]

    def summary(self) -> str:
        return "\n".join([
            f"Total time:       {self.total:.3f}s",
            f"  File discovery:   {self.find:.3f}s",
            f"  Metadata extract: {self.extract:.3f}s  (avg {self._avg(self.extract)})",
            f"  Dest resolve:     {self.resolve:.3f}s  (avg {self._avg(self.resolve)})",
            f"  File execute:     {self.execute:.3f}s  (avg {self._avg(self.execute)})",
            f"  Files processed:  {self.file_count}",
        ])

    def _avg(self, total: float) -> str:
        if self.file_count == 0:
            return "-"
        avg = total / self.file_count
        return f"{avg * 1000:.2f}ms" if avg < 0.001 else f"{avg:.3f}s"
