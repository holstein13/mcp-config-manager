"""Utility for detecting availability of supported MCP clients."""

from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from ..utils.file_utils import (
    get_claude_config_path,
    get_gemini_config_path,
    get_codex_config_path,
)


@dataclass
class CLIDetector:
    """Detect the presence of Claude, Gemini, and Codex CLIs/configs."""

    ttl_seconds: int = 300
    _cache: Dict[str, bool] = field(default_factory=dict, init=False)
    _last_checked: float = field(default=0.0, init=False)

    def detect_all(self, force_refresh: bool = False) -> Dict[str, bool]:
        """Return availability map for all supported clients."""
        now = time.time()
        if not force_refresh and self._cache and (now - self._last_checked) < self.ttl_seconds:
            return dict(self._cache)

        status = {
            "claude": self.detect_claude(),
            "gemini": self.detect_gemini(),
            "codex": self.detect_codex(),
        }
        self._cache = status
        self._last_checked = now
        return dict(status)

    def refresh_detection(self) -> Dict[str, bool]:
        """Force re-check of CLI availability."""
        return self.detect_all(force_refresh=True)

    # ------------------------------------------------------------------
    # Individual detectors
    # ------------------------------------------------------------------

    def detect_claude(self) -> bool:
        """Return True when Claude Desktop configuration or binary is available."""
        config_path = get_claude_config_path()
        if config_path.exists():
            return True
        return bool(shutil.which("claude"))

    def detect_gemini(self) -> bool:
        """Return True when Gemini CLI/config appears present."""
        config_path = get_gemini_config_path()
        if config_path.exists():
            return True
        return bool(shutil.which("gemini")) or bool(os.environ.get("GEMINI_API_KEY"))

    def detect_codex(self) -> bool:
        """Return True when Codex CLI/config appears present."""
        config_path = get_codex_config_path()
        if config_path.exists():
            return True
        # Codex CLI currently ships as `codex` binary within OpenAI tooling.
        return bool(shutil.which("codex")) or bool(shutil.which("openai"))
