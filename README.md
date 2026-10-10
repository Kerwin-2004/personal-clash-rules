# Personal Clash Rules

基于 [Aethersailor Custom OpenClash Rules](https://github.com/Aethersailor/Custom_OpenClash_Rules) 的 [Full 模板](https://github.com/Aethersailor/Custom_OpenClash_Rules/blob/main/cfg/Custom_Clash_Full.ini)，提供国外 AI 独立分流、真实节点选择和每日上游同步。

本项目保存 SubConverter INI 规则模板。使用时需要自行提供订阅，仓库不保存私人订阅、节点凭据或访问令牌。

## 功能

- **国外 AI 独立分流**：保留上游 ChatGPT、微软 Copilot 和国外 AI 服务组，新增 Claude、Gemini、Perplexity、Grok、GitHub Copilot、Cursor、Windsurf、Poe。独立规则在国外 AI 聚合规则之前匹配。
- **国内 AI 直连**：使用 `GEOSITE,category-ai-cn`，不显示国内 AI 策略组。
- **真实节点选择**：删除国家/地区策略组、「其他地区」和「低倍率节点」策略组及其入口；常规业务选择组通过 `.*` 展开订阅中的真实节点，包含原来的低倍率节点。其余策略选项的相对顺序遵循上游。
- **家宽节点**：保留上游 `🏠 家宽节点` 组及节点名称匹配规则。
- **学术资源**：保留上游原名 `📚 学术资源`，继续使用 `GEOSITE,category-scholar-!cn`（IEEE、Google Scholar、主流学术出版与检索等），不新增域名清单。删除地区和低倍率入口后，其余选项顺序遵循上游，可自行调整为直连。
- **上游规则同步**：其他服务的分流规则和远程规则地址沿用 Full 模板，每次更新重新应用个人设置。

AI 规则引用已有 GeoSite 分类：`openai`、`bing`、`anthropic`、`google-deepmind`、`perplexity`、`xai`、`github-copilot`、`cursor`、`windsurf`、`poe`。其余国外 AI 使用 `category-ai-!cn` 兜底；NotebookLM 按 `google-deepmind` 分类进入 Gemini 组。

## 使用

将订阅转换器的 `config=` 参数指向以下配置地址，并按转换器要求进行 URL 编码：

```text
https://raw.githubusercontent.com/Kerwin-2004/personal-clash-rules/main/config/Custom_Clash.ini
```

在转换器的 `url=` 参数中填写自己的订阅链接。生成的 INI 是规则模板，不能直接作为 Clash 节点订阅使用。私人订阅及转换后的节点配置请仅在本地或可信的私有环境中保存。

## 自动更新

[Sync upstream Clash rules](https://github.com/Kerwin-2004/personal-clash-rules/actions/workflows/update-rules.yml) 在以下情况运行：

- 每天 UTC 03:17（北京时间 11:17）定时同步，实际执行时间可能受 GitHub 调度影响。
- `main` 分支的 `custom/`、生成脚本或工作流发生变更。
- 在 Actions 页面选择 **Run workflow** 手动运行。

工作流从 Aethersailor 下载最新 Full 模板，应用 `custom/` 设置，然后仅在内容变化时提交 `config/Custom_Clash.ini`。同步不会修改 `custom/` 文件；上游结构校验失败时停止生成，保留仓库中已有配置。

## 文件结构

| 路径 | 用途 |
| --- | --- |
| `config/Custom_Clash.ini` | Actions 生成的配置 |
| `scripts/update_rules.py` | 下载、转换和校验上游模板 |
| `custom/rules_prepend.txt` | 在国外 AI 聚合规则前插入 GeoSite 分类 |
| `custom/groups_extra.txt` | 新增 AI 策略组 |
| `custom/groups_override.txt` | 覆盖已有策略组的选项与默认出口 |
| `custom/rules_append.txt` | 在 FINAL 规则前插入规则 |
| `.github/workflows/update-rules.yml` | 自动同步工作流 |

## 自定义

在 `custom/groups_override.txt` 中添加完整的 `custom_proxy_group=` 行即可覆盖已有策略组。使用上游原名，例如 `📚 学术资源`；选择组的第一个选项为默认出口。

`custom/groups_extra.txt` 用于调整新增 AI 组的默认选项与顺序。`custom/rules_prepend.txt` 用于调整 AI 的 GeoSite 引用。个人设置在每次同步时重新应用。

本地生成：

```bash
python3 scripts/update_rules.py
```

使用本地 Full 模板校验：

```bash
python3 scripts/update_rules.py --source-file upstream-full.ini --check
```

## 使用条件

转换器和客户端的 GeoSite 数据包需要包含引用的分类。真实节点由订阅转换器展开；家宽组根据节点名称匹配，无法据此验证住宅 IP。实际连接、DNS 与流量接管效果取决于订阅、转换器和客户端配置。

## 来源与许可

本项目生成的配置衍生自 Aethersailor 的 Full 模板，保留上游署名，并遵循上游声明的 **CC BY-SA 4.0** 许可。GeoSite 分类来自 [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)。改动说明见 [NOTICE.md](NOTICE.md)。
