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
GOOGLE_SERVICE_RULE = "ruleset=🇬 谷歌服务,[]GEOSITE,google-scholar"

# --- 个人化改写：位置敏感的上游规则/分组（全部只引用上游已有 GeoSite） ---
# Telegram 单列：category-communication 聚合本身包含 telegram，必须在其之前匹配。
TELEGRAM_GROUP = "💬 Telegram"
COMMUNICATION_GROUP = "💬 即时通讯"
COMMUNICATION_RULE = "ruleset=💬 即时通讯,[]GEOSITE,category-communication"
TELEGRAM_GEOSITE_RULE = f"ruleset={TELEGRAM_GROUP},[]GEOSITE,telegram"
TELEGRAM_GEOIP_NEW = f"ruleset={TELEGRAM_GROUP},[]GEOIP,telegram,no-resolve"
UPSTREAM_TELEGRAM_GROUP = "📨 Telegram"
# These upstream groups now precede the AI aggregate. Personal Claude/Gemini
# rules replace them; the other services must continue using the aggregate.
UPSTREAM_AI_GROUPS = {
    "🤖 Claude", "🤖 Gemini", "🤖 Grok", "🤖 Cursor",
    "🤖 Perplexity", "🤗 Hugging Face",
}
TELEGRAM_GROUP_DEF = (
    f"custom_proxy_group={TELEGRAM_GROUP}`select`[]🚀 手动选择`[]♻️ 自动选择`.*"
)

# 流媒体：把上游 6 个独立影音组合并为「🎥 流媒体」，规则集中插入到上游
# AppleTV+ 的位置——必须早于 🍎 苹果服务，因为上游 apple 分类含 apple-tvplus。
STREAMING_GROUP = "🎥 流媒体"
STREAMING_GROUP_SLOT = "🎥 Netflix"
STREAMING_GROUP_DEF = (
    f"custom_proxy_group={STREAMING_GROUP}`select`"
    "[]🚀 手动选择`[]♻️ 自动选择`[]🎯 全球直连`.*"
)
# 以下上游规则从原位删除后集中重写（GEOIP 规则除外，它保留原位只改分组名）。
UPSTREAM_STREAMING_RULES = (
    "ruleset=🎥 Netflix,[]GEOSITE,netflix",
    "ruleset=🎥 DisneyPlus,[]GEOSITE,disney",
    "ruleset=🎥 HBO,[]GEOSITE,hbo",
    "ruleset=🎥 PrimeVideo,[]GEOSITE,primevideo",
    "ruleset=🎻 Spotify,[]GEOSITE,spotify",
)
# 插入锚点：上游 AppleTV+ 规则所在位置。
STREAMING_INSERT_ANCHOR = "ruleset=🎥 AppleTV+,[]GEOSITE,apple-tvplus"
STREAMING_RULES_BLOCK = (
    ";奈飞、迪士尼、HBO、PrimeVideo、AppleTV+、Spotify 合并为「🎥 流媒体」",
    f"ruleset={STREAMING_GROUP},[]GEOSITE,apple-tvplus",
    f"ruleset={STREAMING_GROUP},[]GEOSITE,netflix",
    f"ruleset={STREAMING_GROUP},[]GEOSITE,disney",
    f"ruleset={STREAMING_GROUP},[]GEOSITE,hbo",
    f"ruleset={STREAMING_GROUP},[]GEOSITE,primevideo",
    f"ruleset={STREAMING_GROUP},[]GEOSITE,spotify",
)
# 上游 GEOIP,netflix 规则保留原位（位于兜底规则前），只改写分组名。
STREAMING_GEOIP_OLD = "ruleset=🎥 Netflix,[]GEOIP,netflix,no-resolve"
STREAMING_GEOIP_NEW = f"ruleset={STREAMING_GROUP},[]GEOIP,netflix,no-resolve"

# bing 由 Ⓜ️ 微软服务 接管（上游 microsoft 分类包含 bing），删除 Copilot 组与规则。
COPILOT_RULE = "ruleset=🤖 Copilot,[]GEOSITE,bing"

# 删除的分组：国家/地区组、低倍率组、家宽组、Copilot 组，以及已并入流媒体的上游组。
# 注意：🎥 Netflix 不在其中，它被就地改写为「🎥 流媒体」以保留显示位置。
REMOVED_GROUPS = {
    "🌐 其他地区",
    "🐢 低倍率节点",
    "🏠 家宽节点",
    "🤖 Copilot",
    "🎥 DisneyPlus",
    "🎥 HBO",
    "🎥 PrimeVideo",
    "🎥 AppleTV+",
    "🎻 Spotify",
    UPSTREAM_TELEGRAM_GROUP,
    *UPSTREAM_AI_GROUPS,
}
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
    """Remove national/region groups, low-rate group and all merged groups."""
    return bool(COUNTRY_FLAG_GROUP.match(name)) or name in REMOVED_GROUPS


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


def is_stale_rollback(line: str) -> bool:
    """上游为旧版国家/地区组保留的注释回退块，其引用的组已不存在。"""
    stripped = line.lstrip()
    if not stripped.startswith(";"):
        return False
    if "custom_proxy_group=" not in stripped:
        return False
    return any(group in stripped for group in REMOVED_GROUPS) or any(
        match in stripped for match in ("🇭🇰", "🇺🇸", "🇯🇵", "🇸🇬", "🇼🇸", "🇰🇷", "🇨🇦", "🇬🇧", "🇫🇷", "🇩🇪", "🇳🇱", "🇹🇷", "🇷🇺")
    )


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

    # Accept both the legacy shared Telegram policy and the dedicated upstream
    # policy. Match the rule payload so a display-name change cannot break sync.
    telegram_ip = [line for line in lines if line.startswith("ruleset=")
                   and line.split(",", 1)[1] == "[]GEOIP,telegram,no-resolve"]
    if len(telegram_ip) != 1:
        raise RuntimeError("上游 Telegram GEOIP 规则缺失或重复")
    lines[lines.index(telegram_ip[0])] = TELEGRAM_GEOIP_NEW
    lines = [line for line in lines if not (
        line.startswith("ruleset=") and (
            line.split(",", 1)[0][len("ruleset="):] in UPSTREAM_AI_GROUPS
            or line.split(",", 1)[1] == "[]GEOSITE,telegram"
        )
    )]

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

    # category-scholar-!cn 自身包含 google-scholar，且上游把 📚 学术资源 排在
    # 谷歌服务之前，因此需要在学术规则前显式插入一条谷歌服务规则。Google 学术
    # 归入 🇬 谷歌服务，其余学术域名仍由 📚 学术资源 处理。
    idx = index_unique(lines, ACADEMIC_RULE)
    lines[idx:idx] = [
        ";Google 学术（google-scholar）归入谷歌服务，须先于学术资源匹配",
        GOOGLE_SERVICE_RULE,
    ]

    # Telegram 单列：category-communication 聚合本身包含 telegram，必须在聚合
    # 规则之前插入专用规则；同时把 GEOIP,telegram 也改指向 Telegram 组。
    idx = index_unique(lines, COMMUNICATION_RULE)
    lines[idx:idx] = [
        ";Telegram 单列分组，须先于即时通讯聚合匹配",
        TELEGRAM_GEOSITE_RULE,
    ]

    # bing 交给 Ⓜ️ 微软服务：删除上游 🤖 Copilot 规则（组定义随 REMOVED_GROUPS 删除）。
    lines.remove(COPILOT_RULE)

    # 影音组合并为「🎥 流媒体」：删除上游 5 条独立规则，在 AppleTV+ 原位
    # 集中插入合并块，保证早于 🍎 苹果服务 且顺序稳定。
    for old in UPSTREAM_STREAMING_RULES:
        lines.remove(old)
    idx = index_unique(lines, STREAMING_INSERT_ANCHOR)
    lines[idx] = STREAMING_RULES_BLOCK[0]
    lines[idx + 1:idx + 1] = list(STREAMING_RULES_BLOCK[1:])
    lines[index_unique(lines, STREAMING_GEOIP_OLD)] = STREAMING_GEOIP_NEW
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
    for keep in ("🚀 手动选择", "♻️ 自动选择", COMMUNICATION_GROUP, STREAMING_GROUP_SLOT):
        if keep not in upstream_names:
            raise RuntimeError(f"Full 模板不再提供 {keep}，停止更新以防丢失策略组")

    output: List[str] = []
    for line in lines:
        if line.startswith("custom_proxy_group="):
            name = group_name(line)
            if is_removed_group(name) or name == "🤖 国内AI服务":
                continue
            if name == STREAMING_GROUP_SLOT:
                # 上游 Netflix 组就地改写为合并后的流媒体组，保留其显示位置。
                line = STREAMING_GROUP_DEF
            elif name == COMMUNICATION_GROUP:
                # Telegram 单列分组紧随即时通讯组，便于单独切换出口。
                output.append(adapt_selection(line))
                output.append(TELEGRAM_GROUP_DEF)
                continue
            else:
                line = override_map.get(name, line)
            line = adapt_selection(line)
        elif is_stale_rollback(line):
            # 上游为旧版去重配置保留的注释回退块仍引用已删除的地区组，一并清理。
            continue
        elif line == ";GFW 及专用规则未命中的国外域名默认直连，可在策略组中切换代理":
            line = ";GFW 及专用规则未命中的国外域名按「🌍 国外域名」策略组的当前选择处理"
        output.append(line)

    extra_names = set()
    for line in extras:
        name = group_name(line)
        if name in upstream_names or name in extra_names or is_removed_group(name):
            raise RuntimeError(f"新增组与上游冲突或无效: {name}")
        extra_names.add(name)
    chatgpt_groups = [i for i, line in enumerate(output)
                     if line.startswith("custom_proxy_group=🤖 ChatGPT`")]
    if len(chatgpt_groups) != 1:
        raise RuntimeError("ChatGPT 策略组缺失或重复，无法排列个人 AI 分组")
    idx = chatgpt_groups[0] + 1
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
    for policy in ("♻️ 自动选择",):
        if not any(l.startswith(f"custom_proxy_group={policy}`url-test`") for l in output):
            raise RuntimeError(f"既有策略组丢失：{policy}")
    for required in (TELEGRAM_GROUP, STREAMING_GROUP):
        if required not in valid:
            raise RuntimeError(f"个人分组缺失：{required}")
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
        print("校验成功：上游模板可正常转换（AI 单列、Telegram 单列、流媒体合并、学术归谷歌）")
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
