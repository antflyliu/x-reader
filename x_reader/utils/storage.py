# -*- coding: utf-8 -*-
"""
Storage utilities — save content to JSON inbox and optional Markdown file.

Implements the "atomic archiving" from the tweet:
- unified_inbox.json (for AI/programmatic use)
- markdown file (for human reading, e.g. Obsidian)
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from loguru import logger

from x_reader.schema import UnifiedContent


def _slugify(title: str, max_len: int = 50) -> str:
    """
    将标题转为安全的文件名 slug：去除非法字符、截断长度。

    Args:
        title: 原始标题
        max_len: 最大长度（不含扩展名）

    Returns:
        可用于文件名的 slug 字符串
    """
    if not title or not title.strip():
        return "untitled"
    # 移除 Windows/Unix 非法字符: \ / : * ? " < > |
    slug = re.sub(r'[\\/:*?"<>|]', "", title.strip())
    # 连续空白合并为单个下划线
    slug = re.sub(r"\s+", "_", slug)
    # 去除首尾下划线
    slug = slug.strip("_")
    if not slug:
        return "untitled"
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("_")
    return slug


def save_to_json(item: UnifiedContent, filepath: str = "unified_inbox.json"):
    """Append content to JSON inbox file."""
    path = Path(filepath)
    data = []

    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = []

    data.append(item.to_dict())

    # Keep last 500 entries to prevent unbounded growth
    data = data[-500:]

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved to JSON: {path}")


def save_to_markdown(item: UnifiedContent, filepath: str = None) -> str | None:
    """
    将单条内容写入独立的 Markdown 文件。

    每条内容一个文件，命名规则：{slug}_{YYYY-MM-DD_HHmmss}.md
    - slug：标题经 _slugify 处理后的安全文件名
    - 时间戳：采集时间或当前时间，保证唯一性

    输出目录（平铺，不按日期分子目录）：
    - OBSIDIAN_VAULT: {vault}/01-收集箱/{slug}_{timestamp}.md
    - OUTPUT_DIR: {output_dir}/{slug}_{timestamp}.md

    若两者均未配置，则跳过输出。
    暂不做 URL 去重，由调用方或后续逻辑单独维护已采集 URL 集合。
    """
    output_dir = None
    if filepath:
        p = Path(filepath)
        # 无扩展名或已是目录 → 视为输出目录；否则用父目录
        output_dir = str(p) if (not p.suffix or p.is_dir()) else str(p.parent)
    else:
        vault_path = os.getenv("OBSIDIAN_VAULT", "")
        if vault_path:
            output_dir = os.path.join(vault_path, "01-收集箱")
        else:
            output_dir = os.getenv("OUTPUT_DIR", "")
        if not output_dir:
            return None

    # 时间戳：优先用 fetched_at，否则当前时间
    ts_raw = item.fetched_at or datetime.now().isoformat()
    try:
        dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        dt = datetime.now()
    ts = dt.strftime("%Y-%m-%d_%H%M%S")
    slug = _slugify(item.title)
    filename = f"{slug}_{ts}.md"
    path = Path(output_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)

    emoji = {
        "telegram": "📢", "rss": "📰", "bilibili": "🎬",
        "xhs": "📕", "twitter": "🐦", "wechat": "💬",
        "youtube": "▶️", "manual": "✏️",
    }.get(item.source_type.value, "📄")

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"## {emoji} {item.title}\n\n")
        f.write(f"- Source: {item.source_name} ({item.source_type.value})\n")
        f.write(f"- URL: {item.url}\n")
        f.write(f"- Fetched: {item.fetched_at[:16]}\n\n")
        # f.write(f"{item.content[:2000]}\n")
        f.write(f"{item.content}\n")

    logger.info(f"Saved to Markdown: {path}")
    return str(path)


def save_content(item: UnifiedContent, json_path: str = None, md_path: str = None):
    """Save content to both JSON and Markdown."""
    inbox_file = json_path or os.getenv("INBOX_FILE", "unified_inbox.json")
    save_to_json(item, inbox_file)
    save_to_markdown(item, md_path)
