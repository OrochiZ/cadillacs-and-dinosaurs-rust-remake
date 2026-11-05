#!/usr/bin/env python3
"""从 CodeBuddy 会话 .jsonl 抽取有效内容，生成 Markdown 笔记。

有效内容 = 真实用户消息 + 助手回答 + 压缩摘要。
跳过     = reasoning / 工具调用与结果 / 计时与会话元数据。

用法:
  python re/tools/session_notes.py <session.jsonl> [-o notes.md] [--with-tools] [--brief]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone

PSEUDO_PREFIXES = (
    "<system-reminder",
    "<command-name>",
    "<local-command",
    "<task-notification>",
    "<command-caveat",
    "<conversation_history_summary>",
)
SYSTEM_REMINDER_RE = re.compile(
    r"<system-reminder[^>]*>.*?</system-reminder>", re.DOTALL
)
TAG_STRIP = ("<user_query>", "</user_query>")


def clean(text: str) -> str:
    text = SYSTEM_REMINDER_RE.sub("", text)
    for tag in TAG_STRIP:
        text = text.replace(tag, "")
    return text.strip()


def text_of(record, kinds) -> str:
    parts = [
        c["text"]
        for c in (record.get("content") or [])
        if isinstance(c, dict)
        and c.get("type") in kinds
        and isinstance(c.get("text"), str)
    ]
    return clean("\n".join(parts))


def stamp(record) -> str:
    v = record.get("timestamp")
    if isinstance(v, (int, float)) and v > 0:
        try:
            return datetime.fromtimestamp(v / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M")
        except (ValueError, OSError, OverflowError):
            pass
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="会话 .jsonl 路径")
    ap.add_argument("-o", "--output", help="输出 .md 路径")
    ap.add_argument("--with-tools", action="store_true", help="附带工具调用清单")
    ap.add_argument("--brief", action="store_true", help="附录只列压缩摘要标题，不嵌全文")
    args = ap.parse_args()

    src = os.path.abspath(args.input)
    if not os.path.isfile(src):
        print(f"找不到文件: {src}", file=sys.stderr)
        return 1
    base = os.path.splitext(os.path.basename(src))[0]
    short = base.split("-")[0]
    out = args.output or os.path.join("re", "notes", f"session-{short}.md")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

    records, counts, bad = [], Counter(), 0
    with open(src, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            counts[r.get("type", "?")] += 1
            records.append((lineno, r))

    flow, compacts, tools = [], [], []
    users = assistants = 0
    for lineno, r in records:
        t = r.get("type")
        if t == "message":
            role = r.get("role")
            if role == "user":
                text = text_of(r, {"input_text"})
                if not text:
                    continue
                if text.lstrip().startswith("<conversation_history_summary>"):
                    body = text.replace("<conversation_history_summary>", "").replace(
                        "</conversation_history_summary>", ""
                    ).strip()
                    compacts.append((lineno, "压缩摘要", body))
                    flow.append(f"> ⚙ **COMPACTION** (line {lineno}) — 全文见附录 A")
                    continue
                if text.lstrip().startswith(PSEUDO_PREFIXES):
                    continue
                users += 1
                flow.append(f"### U{users} · {stamp(r)}\n\n{text}")
            elif role == "assistant":
                text = text_of(r, {"output_text"})
                if not text:
                    continue
                assistants += 1
                flow.append(f"**A{assistants}** · {stamp(r)}\n\n{text}")
        elif t == "summary":
            s = (r.get("summary") or "").strip()
            if s:
                compacts.append((lineno, "压缩标题", s))
        elif t == "function_call" and args.with_tools:
            a = r.get("arguments")
            brief = a[:140].replace("\n", " ") if isinstance(a, str) else ""
            tools.append((lineno, str(r.get("name", "?")), brief))

    compacts.sort(key=lambda x: x[0])
    type_line = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    full_summaries = sum(1 for c in compacts if c[1] == "压缩摘要")

    md = [
        f"# 会话笔记 · {base}",
        "",
        f"- 源文件：`{src}`",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}（文中时间戳为 UTC）",
        f"- 行数：{len(records)}（解析失败 {bad}）",
        f"- 记录类型：{type_line}",
        f"- 压缩点：{len(compacts)}（含 {full_summaries} 份完整摘要）",
        f"- 有效内容：用户 {users} 条 / 助手 {assistants} 条",
        "",
        "> 由 `re/tools/session_notes.py` 自动生成，是**原始对话档案**；"
        "提炼后的结论见 `re/notes/DECISIONS.md`。",
        "",
        "## 压缩点索引",
        "",
        "| 行号 | 类型 | 摘要 |",
        "|---|---|---|",
    ]
    for lineno, kind, body in compacts:
        one = " ".join(body.split())[:90].replace("|", "\\|")
        md.append(f"| {lineno} | {kind} | {one} |")
    md += ["", "## 对话流水", ""]
    md += ["\n\n---\n\n".join(flow)]
    if not args.brief:
        md += ["", "## 附录 A · 压缩摘要全文", ""]
        for i, (lineno, kind, body) in enumerate(compacts, 1):
            md += [
                f"<details><summary>#{i} · line {lineno} · {kind}</summary>",
                "",
                "```text",
                body.strip(),
                "```",
                "",
                "</details>",
                "",
            ]
    if args.with_tools and tools:
        md += ["", "## 附录 B · 工具调用", "", "| 行号 | 工具 | 参数摘要 |", "|---|---|---|"]
        for lineno, name, brief in tools:
            md.append(f"| {lineno} | `{name}` | {brief.replace('|', '\\|')} |")
    md.append("")

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"写出 {out}")
    print(
        f"  {len(records)} 行 / {len(compacts)} 压缩点 / U{users} A{assistants} "
        f"/ {os.path.getsize(out)} B"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
