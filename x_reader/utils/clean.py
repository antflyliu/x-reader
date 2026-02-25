# -*- coding: utf-8 -*-
"""
Content cleaning utilities.

Removes noise from extracted content:
- Jina Reader metadata (URL Source, Published Time, Markdown Content)
- X/Twitter page UI (login prompts, navigation, footer)
- Generic web noise (cookie consent, repeated nav menus, footer links)
"""

import re
from typing import Optional


# Jina Reader 在响应中插入的元数据块
JINA_METADATA_PATTERNS = [
    r"URL Source:\s*https?://[^\n]+",
    r"Published Time:\s*[^\n]+",
    r"Markdown Content:\s*",
    r"={10,}\s*",  # 长等号分隔线
]

# X/Twitter 页面 UI 噪音（Jina 抓取整页时带入）
TWITTER_UI_PATTERNS = [
    r"Don't miss what's happening\s*",
    r"People on X are the first to know\.?\s*",
    r"\[Log in\]\([^)]+\)\s*",
    r"\[Sign up\]\([^)]+\)\s*",
    r"\[\]\(https://x\.com/\)\s*",
    r"={5,}\s*Post\s*-+\s*",
    r"See new posts\s*",
    r"Conversation\s*={5,}\s*",
    r"Translate post\s*",
    r"New to X\?\s*-+\s*",
    r"Sign up now to get your own personalized timeline!?\s*",
    r"Sign up with Apple\s*",
    r"\[Create account\]\([^)]+\)\s*",
    r"By signing up, you agree to the \[Terms of Service\][^\n]+",
    r"Read \d+ replies\s*",
    r"\[\d+\.\d+K Views\]\([^)]+\)\s*",
    r"^\d+\s*$",  # 孤立的数字（点赞/转发数）
]

# 通用网页噪音
WEB_NOISE_PATTERNS = [
    r"Continuer sans accepter\s*[→›]\s*",
    r"Avec votre accord[^.]*?\.\s*",
    r"En savoir plus\s*[→›]\s*Accepter\s*&\s*Fermer\s*",
    r"Vos données personnelles sont traitées[^\n]+",
    r"Données de géolocalisation[^\n]+",
    r"\[nos \d+ partenaires\]\(javascript:[^)]+\)[^.]*?\.\s*",
    r"utilisons des cookies ou technologies similaires[^.]*?\.\s*",
    r"Publicité\s*",
    r"LIRE AUSSI\s*-+\s*",
    r"voir toutes les ressources\s*",
    r"TAGS ASSOCIÉS\s*",
    r"Brand Voice\s*-+\s*",
    r"Brand Voice marques[^\n]+",
    r"ACTUALITÉS\s*",
    r"PARTENAIRES\s*",
    r"CONTACTS\s*",
    r"NOUS SUIVRE\s*",
    r"Consentements cookies\s*",
    r"Gérer vos consentements\s*",
    r"Retrouvez tous les sites\s*",
    r"CGU\s*\|",
    r"Politique de confidentialité\s*\|",
    r"Mentions légales\s*\|",
    r"Archives\s*",
]

# 作者/日期 attribution 行（保留主内容，可选择性清理尾部）
# 例如: "逸尘 on X: \"...\" / X" 或 "https://t.co/xxx — Author (@handle) Date"
ATTRIBUTION_PATTERN = r'^[^"]*on X:\s*"[^"]*"\s*/ X\s*$'


def _remove_patterns(text: str, patterns: list[str]) -> str:
    """按正则模式移除匹配内容。"""
    result = text
    for pat in patterns:
        result = re.sub(pat, "", result, flags=re.IGNORECASE | re.MULTILINE)
    return result


def _remove_cookie_consent_block(text: str) -> str:
    """
    移除 Cookie 同意弹窗相关的大块文本（多行）。
    常见起止：Continuer sans accepter / Accepter & Fermer
    """
    return re.sub(
        r"Continuer sans accepter\s*[→›]?\s*\n.*?Accepter\s*&\s*Fermer",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )


def _remove_jina_metadata(content: str) -> str:
    """
    移除 Jina Reader 在 markdown 中插入的元数据块。

    格式示例:
        URL Source: https://...
        Published Time: ...
        Markdown Content:
        ===============
    """
    lines = content.split("\n")
    out = []
    skip_until_blank = False

    for line in lines:
        stripped = line.strip()
        if re.match(r"URL Source:\s*https?://", stripped):
            skip_until_blank = True
            continue
        if re.match(r"Published Time:\s*", stripped):
            continue
        if re.match(r"Markdown Content:\s*", stripped, re.I):
            continue
        if skip_until_blank and re.match(r"^=+$", stripped):
            skip_until_blank = False
            continue
        if skip_until_blank and not stripped:
            skip_until_blank = False
            continue
        out.append(line)

    return "\n".join(out)


def clean_content(
    content: str,
    *,
    source_type: Optional[str] = None,
    strip_jina_metadata: bool = True,
    strip_twitter_ui: bool = True,
    strip_web_noise: bool = True,
) -> str:
    """
    清理采集内容中的噪音。

    Args:
        content: 原始内容
        source_type: 来源类型 (twitter, manual, 等)，用于选择清理策略
        strip_jina_metadata: 是否移除 Jina 元数据块
        strip_twitter_ui: 是否移除 X/Twitter 页面 UI
        strip_web_noise: 是否移除通用网页噪音

    Returns:
        清理后的内容
    """
    if not content or not content.strip():
        return content

    result = content

    if strip_jina_metadata:
        result = _remove_jina_metadata(result)

    if strip_twitter_ui and (source_type == "twitter" or "x.com" in content or "twitter.com" in content):
        result = _remove_patterns(result, TWITTER_UI_PATTERNS)

    if strip_web_noise:
        result = _remove_cookie_consent_block(result)
        result = _remove_patterns(result, WEB_NOISE_PATTERNS)

    # 合并多余空行，去除首尾空白
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def clean_title(title: str) -> str:
    """
    清理标题中的前缀噪音。

    例如: "Title: RAG open source..." -> "RAG open source..."
    """
    if not title or not title.strip():
        return title
    t = title.strip()
    if re.match(r"^Title:\s+", t, re.I):
        return re.sub(r"^Title:\s+", "", t, count=1, flags=re.I).strip()
    return t
