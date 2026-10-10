#!/usr/bin/env python3
"""Sync Aethersailor's Full SubConverter template while keeping personal group choices.

Only existing upstream/v2fly GEOSITE categories are used. No custom domain
lists, subscription links or credentials are stored by this project.
Requires Python 3.9+, standard library only.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
import urllib.request
from typing import List

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_URL = (
    "https://raw.githubusercontent.com/Aethersailor/Custom_OpenClash_Rules/"
    "refs/heads/main/cfg/Custom_Clash_Full.ini"
)
OUTPUT = ROOT / "config" / "Custom_Clash.ini"
CUSTOM = ROOT / "custom"
AI_ANCHOR = "ruleset=🤖 国外AI服务,[]GEOSITE,category-ai-!cn"
DOMESTIC_AI = "ruleset=🤖 国内AI服务,[]GEOSITE,category-ai-cn"
ACADEMIC_RULE = "ruleset=📚 学术资源,[]GEOSITE,category-scholar-!cn"
FINAL_ANCHOR = "ruleset=🐟 漏网之鱼,[]FINAL"
GROUP_CLOSE_ANCHOR = ";设置分组标志位"
GROUP_PATTERN = re.compile(r"^custom_proxy_group=([^`]+)`")


def load_custom(name: str, prefix: str) -> List[str]:
    path = CUSTOM / name
    if not path.is_file():
        raise RuntimeError(f"缺少个人设置文件: {path}")
    result: List[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if not line.startswith(prefix):
            raise RuntimeError(f"{name} 第 {number} 行格式错误: {line}")
        result.append(line)
    return result


def index_unique(lines: List[str], exact: str) -> int:
    indices = [i for i, line in enumerate(lines) if line.strip() == exact]
    if len(indices) != 1:
        raise RuntimeError(f"上游结构变化：锚点 {exact!r} 出现 {len(indices)} 次（应为1）")
    return indices[0]


def group_name(line: str) -> str:
    match = GROUP_PATTERN.match(line)
    if not match:
        raise RuntimeError(f"策略组定义无效: {line}")
    return match.group(1)


# Only national / regional *policy groups* disappear; all actual subscription
# nodes (including nodes named by country) remain selectable via `.*`.
COUNTRY_FLAG_GROUP = re.compile(r"^[\U0001F1E6-\U0001F1FF]{2} .+节点$")


def is_removed_group(name: str) -> bool:
    """Remove national/region groups and the low-rate policy group."""
    return bool(COUNTRY_FLAG_GROUP.match(name)) or name in {"🌐 其他地区", "🐢 低倍率节点"}


def adapt_selection(line: str) -> str:
    """Only drop country references and append real nodes; preserve every other option."""
    parts = line.split("`")
    name = group_name(line)
    if len(parts) < 3 or parts[1] != "select" or name == "🎯 全球直连":
        return line
    choices = [part for part in parts[2:]
               if not (part.startswith("[]") and is_removed_group(part[2:]))]
    # Preserve the special nonstandard-port group, whose two options intentionally
    # forward traffic to policy groups rather than exposing individual nodes.
    if name != "🔀 非标端口" and ".*" not in choices:
        choices.append(".*")
    return "`".join(parts[:2] + choices)


def build(source: str) -> str:
    lines = source.replace("\r\n", "\n").lstrip("\ufeff").splitlines()
    if "[custom]" not in lines or sum(x.startswith("ruleset=") for x in lines) < 45:
        raise RuntimeError("上游 Full 模板缺少规则或规则数量异常")
    if sum(x.startswith("custom_proxy_group=") for x in lines) < 45:
        raise RuntimeError("上游 Full 模板策略组数量异常")
    for anchor in (AI_ANCHOR, DOMESTIC_AI, ACADEMIC_RULE, FINAL_ANCHOR,
                   GROUP_CLOSE_ANCHOR, "enable_rule_generator=true", "overwrite_original_rules=true"):
        index_unique(lines, anchor)

    ai_rules = load_custom("rules_prepend.txt", "ruleset=")
    trailing_rules = load_custom("rules_append.txt", "ruleset=")
    overrides = load_custom("groups_override.txt", "custom_proxy_group=")
    extras = load_custom("groups_extra.txt", "custom_proxy_group=")

    # Preserve upstream rules/ordering. Insert existing GeoSite subsets BEFORE
    # category-ai-!cn; that category is an aggregate containing those subsets.
    lines.remove(DOMESTIC_AI)
    idx = index_unique(lines, AI_ANCHOR)
    lines[idx:idx] = [
        "; ===== 个人分类（仅引用 GeoSite 上游分类，不维护域名清单） =====",
        *ai_rules,
        "ruleset=🎯 全球直连,[]GEOSITE,category-ai-cn",
        "; ===== 个人分类结束 =====",
    ]
    lines[index_unique(lines, ACADEMIC_RULE)] = ACADEMIC_RULE.replace("📚 学术资源", "📚 科研工具")
    if trailing_rules:
        idx = index_unique(lines, FINAL_ANCHOR)
        lines[idx:idx] = trailing_rules

    # Overrides may modify a group but cannot reintroduce removed region groups.
    override_map = {}
    for line in overrides:
        name = group_name(line)
        if name in override_map:
            raise RuntimeError(f"groups_override.txt 重复: {name}")
        override_map[name] = line
    if any(is_removed_group(name) or name == "🤖 国内AI服务" for name in override_map):
        raise RuntimeError("不允许覆盖已取消的地区节点组或国内 AI 组")

    upstream_names = {group_name(l) for l in lines if l.startswith("custom_proxy_group=")}
    missing = set(override_map) - upstream_names
    if missing:
        raise RuntimeError(f"groups_override.txt 指定了上游不存在的分组: {sorted(missing)}")
    for keep in ("🏠 家宽节点", "🚀 手动选择", "♻️ 自动选择"):
        if keep not in upstream_names:
            raise RuntimeError(f"Full 模板不再提供 {keep}，停止更新以防丢失策略组")

    output: List[str] = []
    for line in lines:
        if line.startswith("custom_proxy_group="):
            name = group_name(line)
            if is_removed_group(name) or name == "🤖 国内AI服务":
                continue
            if name == "📚 学术资源":
                line = override_map.get(name, line).replace(
                    "custom_proxy_group=📚 学术资源`", "custom_proxy_group=📚 科研工具`", 1
                )
            else:
                line = override_map.get(name, line)
            line = adapt_selection(line)
        output.append(line)

    extra_names = set()
    for line in extras:
        name = group_name(line)
        if name in upstream_names or name in extra_names or is_removed_group(name):
            raise RuntimeError(f"新增组与上游冲突或无效: {name}")
        extra_names.add(name)
    idx = index_unique(output, GROUP_CLOSE_ANCHOR)
    output[idx:idx] = ["; ===== 个人 AI 独立策略组 =====", *[adapt_selection(x) for x in extras], "; ===== 个人 AI 组结束 ====="]

    final_groups = [group_name(l) for l in output if l.startswith("custom_proxy_group=")]
    if len(final_groups) != len(set(final_groups)):
        raise RuntimeError("生成结果存在同名策略组")
    valid = set(final_groups)
    for line in output:
        if line.startswith("ruleset="):
            group = line[len("ruleset="):].split(",", 1)[0]
            if group not in valid:
                raise RuntimeError(f"规则引用了不存在的策略组: {group}")
        if line.startswith("custom_proxy_group="):
            for part in line.split("`")[2:]:
                if part.startswith("[]") and part[2:] not in valid and part[2:] not in {"DIRECT", "REJECT", "REJECT-DROP", "PASS"}:
                    raise RuntimeError(f"分组引用了不存在的策略组: {part}")
    for policy in ("🏠 家宽节点", "♻️ 自动选择"):
        if not any(l.startswith(f"custom_proxy_group={policy}`url-test`") for l in output):
            raise RuntimeError(f"既有策略组丢失：{policy}")
    if any(l.startswith("custom_proxy_group=") and is_removed_group(group_name(l)) for l in output):
        raise RuntimeError("仍存在国家/地区或低倍率策略组")
    return "\n".join(output).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build personal INI from Aethersailor Full")
    parser.add_argument("--source-file", type=pathlib.Path, help="使用本地上游 INI 进行离线校验")
    parser.add_argument("--output", type=pathlib.Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.source_file:
        source = args.source_file.read_text(encoding="utf-8-sig")
    else:
        req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "personal-clash-rules/2.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            source = response.read().decode("utf-8-sig")
    result = build(source)
    if args.check:
        print("校验成功：保留既有组序，只删除国家和低倍率分组；业务组选项加入真实节点")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    existing = args.output.read_text(encoding="utf-8") if args.output.exists() else None
    if existing == result:
        print("规则无变化")
        return 0
    args.output.write_text(result, encoding="utf-8")
    print(f"生成 {args.output}，共 {len(result.splitlines())} 行")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, UnicodeError) as error:
        print(f"错误：{error}", file=sys.stderr)
        sys.exit(1)
