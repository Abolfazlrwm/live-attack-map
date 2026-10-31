"""Incremental JSONL reader used by the live dashboard.

The tailer deliberately reads bytes instead of text. Text-mode ``tell()`` is
opaque on several platforms and an incomplete final line would otherwise be
silently skipped when the poll offset advances past it.
"""

from __future__ import annotations

from pathlib import Path


class LogTailer:
    """Read complete, newly appended lines from a log file.

    Args:
        path: File to follow.
        start_at_end: Skip existing content on the first poll. This is the
            normal live-tail behaviour; tests can disable it to read fixtures.
    """

    def __init__(self, path: Path, *, start_at_end: bool = True) -> None:
        self.path = Path(path)
        self.start_at_end = start_at_end
        self._offset = 0
        self._buffer = b""
        self._identity: tuple[int, int] | None = None
        self._initialized = False

    def _file_identity(self) -> tuple[int, int] | None:
        try:
            stat = self.path.stat()
        except FileNotFoundError:
            return None
        return stat.st_dev, stat.st_ino

    def _reset(self, *, at_end: bool) -> None:
        self._buffer = b""
        try:
            self._offset = self.path.stat().st_size if at_end else 0
        except FileNotFoundError:
            self._offset = 0
        self._identity = self._file_identity()
        self._initialized = True

    def read_new_lines(self) -> list[str]:
        """Return complete lines appended since the previous call.

        A trailing line without a newline is kept in an internal buffer until
        it is completed. Rotation (rename/replace) and truncation reset the
        stream so the new file is read from its beginning.
        """
        if not self.path.exists():
            self._identity = None
            self._buffer = b""
            self._offset = 0
            self._initialized = False
            return []

        identity = self._file_identity()
        size = self.path.stat().st_size

        if not self._initialized:
            self._reset(at_end=self.start_at_end)
            identity = self._identity
            size = self.path.stat().st_size
        if identity != self._identity or size < self._offset:
            self._reset(at_end=False)
            size = self.path.stat().st_size
            if size == 0:
                return []

        with self.path.open("rb") as handle:
            handle.seek(self._offset)
            chunk = handle.read()

        self._offset += len(chunk)
        self._buffer += chunk

        *complete, remainder = self._buffer.split(b"\n")
        self._buffer = remainder
        return [
            line.decode("utf-8", errors="replace")
            for line in complete
            if line.strip()
        ]
