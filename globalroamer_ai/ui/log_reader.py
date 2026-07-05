from __future__ import annotations

from pathlib import Path


DEFAULT_LOG_FILES = {
    "ingest": "ingest.log",
    "analyze": "analyze.log",
    "report": "report.log",
}


class LogReader:
    def __init__(self, log_dir: str | Path):
        self.log_dir = Path(log_dir)

    def get_log_path(self, log_name: str) -> Path:
        filename = DEFAULT_LOG_FILES.get(log_name, log_name)
        return self.log_dir / filename

    def exists(self, log_name: str) -> bool:
        return self.get_log_path(log_name).is_file()

    def read_text(self, log_name: str) -> str:
        path = self.get_log_path(log_name)

        if not path.is_file():
            return f"Log file not found: {path}"

        return path.read_text(encoding="utf-8", errors="replace")

    def tail(self, log_name: str, lines: int = 300) -> str:
        path = self.get_log_path(log_name)

        if not path.is_file():
            return f"Log file not found: {path}"

        return "\n".join(self._tail_lines(path, lines))

    def list_logs(self) -> list[str]:
        if not self.log_dir.exists():
            return []

        return sorted(path.name for path in self.log_dir.glob("*.log") if path.is_file())

    def latest_activity(self) -> dict[str, str | None]:
        result = {}

        for name in DEFAULT_LOG_FILES:
            path = self.get_log_path(name)
            result[name] = self._last_non_empty_line(path)

        return result

    def _last_non_empty_line(self, path: Path) -> str | None:
        if not path.is_file():
            return None

        for line in reversed(self._tail_lines(path, 100)):
            value = line.strip()
            if value:
                return value

        return None

    def _tail_lines(self, path: Path, lines: int) -> list[str]:
        if lines <= 0:
            return []

        with path.open("rb") as file:
            file.seek(0, 2)
            file_size = file.tell()
            block_size = 4096
            data = b""
            blocks = 0

            while file_size > 0 and data.count(b"\n") <= lines:
                blocks += 1
                seek_offset = max(file_size - block_size * blocks, 0)
                read_size = file_size - seek_offset if seek_offset == 0 else block_size
                file.seek(seek_offset)
                data = file.read(read_size) + data

                if seek_offset == 0:
                    break

        text = data.decode("utf-8", errors="replace")
        return text.splitlines()[-lines:]
