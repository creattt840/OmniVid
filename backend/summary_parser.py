"""从 AI 流式 JSON 响应中提取摘要文本，供前端逐字展示。"""

import json
import re


def extract_partial_summary(content: str) -> str:
    """从（可能未闭合的）JSON 中提取 summary 字段已生成的文本。"""
    match = re.search(r'"summary"\s*:\s*"', content)
    if not match:
        return ""

    result = []
    i = match.end()
    while i < len(content):
        c = content[i]
        if c == "\\":
            if i + 1 >= len(content):
                break
            esc = content[i + 1]
            mapping = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "/": "/"}
            result.append(mapping.get(esc, esc))
            i += 2
            continue
        if c == '"':
            break
        result.append(c)
        i += 1
    return "".join(result)


def repair_truncated_json(content: str) -> str:
    """尝试修复被截断的 JSON（补全引号与括号）。"""
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)

    start = content.find("{")
    if start < 0:
        return content

    text = content[start:]
    open_braces = 0
    open_brackets = 0
    in_string = False
    escape = False

    for c in text:
        if escape:
            escape = False
            continue
        if c == "\\" and in_string:
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            open_braces += 1
        elif c == "}":
            open_braces -= 1
        elif c == "[":
            open_brackets += 1
        elif c == "]":
            open_brackets -= 1

    if in_string:
        text += '"'
    text += "]" * max(0, open_brackets)
    text += "}" * max(0, open_braces)
    return text


def parse_summary_json(content: str) -> dict:
    """解析 AI 返回的 JSON，含 markdown 包裹与截断修复。"""
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)

    for attempt in (content, repair_truncated_json(content)):
        try:
            return json.loads(attempt)
        except json.JSONDecodeError:
            pass

        start = attempt.find("{")
        end = attempt.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(attempt[start : end + 1])
            except json.JSONDecodeError:
                pass

    summary_text = extract_partial_summary(content)
    return {
        "summary": summary_text or content[:500],
        "highlights": [],
        "chapters": [],
        "mindmap": "# 视频内容\n## 详见摘要",
        "terms": [],
    }
