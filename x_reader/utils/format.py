# -*- coding: utf-8 -*-
"""
Content format normalization utilities.

Restores Markdown structure when Jina Reader flattens X/Twitter content
(removes line breaks between numbered sections and bullet points).
"""

import re


def normalize_twitter_markdown(text: str) -> str:
    """
    Restore Markdown structure in flattened X/Twitter content.

    Jina Reader sometimes returns X post content as a single line, losing
    the original structure (numbered lists, bullet points, tree diagrams).
    This function restores:
    - Numbered sections (1. 2. 3. ...)
    - Bullet points (·)
    - Tree structure (├── └──)

    Args:
        text: Flattened content from Jina (or similar)

    Returns:
        Content with proper line breaks for Markdown rendering
    """
    if not text or not text.strip():
        return text

    result = text

    # 1. Add newline before numbered items (1. 2. 3. ... 10. etc)
    #    When preceded by non-whitespace (e.g. "原则 1. 安全" -> "原则\n\n1. 安全")
    result = re.sub(r"(?<=\S)\s+(?=\d+\.\s)", "\n\n", result)

    # 2. Add newline before bullet points (·)
    #    e.g. "最优 · 自己写" -> "最优\n· 自己写"
    result = re.sub(r"(?<=\S)\s+(?=·\s)", "\n", result)

    # 3. Add newline before tree structure (├── └──)
    #    e.g. "workspace/ ├── SOUL" -> "workspace/\n├── SOUL"
    result = re.sub(r"(?<=\S)\s+(?=[├└]\s*──)", "\n\n", result)

    # 4. Collapse excessive newlines (max 2 consecutive)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()
