"""Processing statistics and cost estimation module."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


# Approximate pricing per 1K tokens (USD)
PRICING = {
    "openai": {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    },
    "claude": {
        "claude-sonnet-4-6-20250514": {"input": 0.003, "output": 0.015},
        "claude-opus-4-7": {"input": 0.015, "output": 0.075},
    },
    "kimi": {
        "moonshot-v1-8k": {"input": 0.012, "output": 0.012},
        "moonshot-v1-32k": {"input": 0.024, "output": 0.024},
        "moonshot-v1-128k": {"input": 0.06, "output": 0.06},
    },
}


@dataclass
class ProcessingStats:
    """Statistics for a single processing session."""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    files_processed: int = 0
    files_succeeded: int = 0
    files_failed: int = 0
    total_pages: int = 0
    total_chars: int = 0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    api_calls: int = 0
    cache_hits: int = 0
    provider: str = ""
    model: str = ""

    @property
    def duration_seconds(self) -> float:
        """Get processing duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

    @property
    def avg_time_per_file(self) -> float:
        """Get average time per file in seconds."""
        if self.files_processed > 0:
            return self.duration_seconds / self.files_processed
        return 0

    def estimate_cost(self) -> float:
        """Estimate total API cost in USD."""
        provider_prices = PRICING.get(self.provider, {})
        model_prices = provider_prices.get(self.model, {"input": 0.01, "output": 0.01})

        input_cost = (self.total_tokens_input / 1000) * model_prices["input"]
        output_cost = (self.total_tokens_output / 1000) * model_prices["output"]

        return input_cost + output_cost

    def estimate_cost_cny(self) -> float:
        """Estimate cost in CNY (approximate rate)."""
        return self.estimate_cost() * 7.2

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "files_processed": self.files_processed,
            "files_succeeded": self.files_succeeded,
            "files_failed": self.files_failed,
            "total_pages": self.total_pages,
            "total_chars": self.total_chars,
            "total_tokens_input": self.total_tokens_input,
            "total_tokens_output": self.total_tokens_output,
            "api_calls": self.api_calls,
            "cache_hits": self.cache_hits,
            "provider": self.provider,
            "model": self.model,
            "estimated_cost_usd": round(self.estimate_cost(), 4),
            "estimated_cost_cny": round(self.estimate_cost_cny(), 2),
        }


class StatsManager:
    """Manager for processing statistics."""

    def __init__(self, stats_dir: Optional[Path] = None):
        self.stats_dir = stats_dir or Path("./output/.stats")
        self.stats_dir.mkdir(parents=True, exist_ok=True)
        self._current_stats: Optional[ProcessingStats] = None

    def start_session(self, provider: str, model: str) -> ProcessingStats:
        """Start a new processing session."""
        self._current_stats = ProcessingStats(
            provider=provider,
            model=model,
        )
        return self._current_stats

    def get_current(self) -> Optional[ProcessingStats]:
        """Get current session stats."""
        return self._current_stats

    def end_session(self) -> ProcessingStats:
        """End current session and save stats."""
        if self._current_stats is None:
            raise ValueError("No active session")

        self._current_stats.end_time = datetime.now()
        self._save_stats(self._current_stats)

        return self._current_stats

    def add_file_result(
        self,
        pages: int,
        chars: int,
        success: bool,
        tokens_input: int = 0,
        tokens_output: int = 0,
        from_cache: bool = False,
    ):
        """Add a file processing result to current session."""
        if self._current_stats is None:
            return

        self._current_stats.files_processed += 1
        self._current_stats.total_pages += pages
        self._current_stats.total_chars += chars

        if success:
            self._current_stats.files_succeeded += 1
        else:
            self._current_stats.files_failed += 1

        if not from_cache:
            self._current_stats.api_calls += 1
            self._current_stats.total_tokens_input += tokens_input
            self._current_stats.total_tokens_output += tokens_output
        else:
            self._current_stats.cache_hits += 1

    def _save_stats(self, stats: ProcessingStats):
        """Save stats to file."""
        timestamp = stats.start_time.strftime("%Y%m%d_%H%M%S")
        stats_file = self.stats_dir / f"session_{timestamp}.json"

        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"Stats saved to: {stats_file}")

    def get_history(self, limit: int = 10) -> List[dict]:
        """Get historical stats."""
        stats_files = sorted(
            self.stats_dir.glob("session_*.json"),
            reverse=True
        )[:limit]

        history = []
        for f in stats_files:
            with open(f, encoding="utf-8") as fp:
                history.append(json.load(fp))

        return history

    def get_summary(self) -> dict:
        """Get overall summary statistics."""
        history = self.get_history(limit=100)

        if not history:
            return {}

        total_files = sum(h.get("files_processed", 0) for h in history)
        total_pages = sum(h.get("total_pages", 0) for h in history)
        total_tokens = sum(h.get("total_tokens_input", 0) + h.get("total_tokens_output", 0) for h in history)
        total_cost = sum(h.get("estimated_cost_usd", 0) for h in history)

        return {
            "total_sessions": len(history),
            "total_files": total_files,
            "total_pages": total_pages,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "total_cost_cny": round(total_cost * 7.2, 2),
        }


def format_stats_report(stats: ProcessingStats) -> str:
    """Format stats as a readable report."""
    lines = [
        "╔══════════════════════════════════════════════╗",
        "║          处理统计报告 / Stats Report          ║",
        "╠══════════════════════════════════════════════╣",
        f"║ 提供商: {stats.provider:<20} 模型: {stats.model:<10}  ║",
        f"║ 处理时间: {stats.duration_seconds:.1f}秒                         ║",
        "╠══════════════════════════════════════════════╣",
        f"║ 文件统计:                                    ║",
        f"║   处理: {stats.files_processed}  成功: {stats.files_succeeded}  失败: {stats.files_failed}          ║",
        f"║   总页数: {stats.total_pages}  总字符: {stats.total_chars:,}           ║",
        "╠══════════════════════════════════════════════╣",
        f"║ API 统计:                                    ║",
        f"║   调用次数: {stats.api_calls}  缓存命中: {stats.cache_hits}           ║",
        f"║   输入Token: {stats.total_tokens_input:,}  输出Token: {stats.total_tokens_output:,}    ║",
        "╠══════════════════════════════════════════════╣",
        f"║ 成本估算:                                    ║",
        f"║   USD: ${stats.estimate_cost():.4f}                          ║",
        f"║   CNY: ¥{stats.estimate_cost_cny():.2f}                           ║",
        "╚══════════════════════════════════════════════╝",
    ]
    return "\n".join(lines)
