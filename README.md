# Personal Clash Rules

基于 [Aethersailor Custom OpenClash Rules](https://github.com/Aethersailor/Custom_OpenClash_Rules) 的 [Full 模板](https://github.com/Aethersailor/Custom_OpenClash_Rules/blob/main/cfg/Custom_Clash_Full.ini)，提供 AI 独立分流、影音合并、真实节点选择和每日上游同步。

本项目保存 SubConverter INI 规则模板。使用时需要自行提供订阅，仓库不保存私人订阅、节点凭据或访问令牌。

## 功能

- **AI 独立分流**：只把 ChatGPT、Claude、Gemini 单列成组，规则位于国外 AI 聚合规则之前；其余国外 AI（含 Copilot、Perplexity、Grok、Cursor、Windsurf、Poe 等）统一走上游 `🤖 国外AI服务` 组。
- **国内 AI 直连**：使用 `GEOSITE,category-ai-cn`，不显示国内 AI 策略组。
- **Telegram 单列**：`💬 Telegram` 组位于 `💬 即时通讯` 之前，可单独切换出口；后者继续覆盖 WhatsApp、Line 等。
- **流媒体合并**：奈飞、迪士尼、HBO、PrimeVideo、AppleTV+、Spotify 合并为 `🎥 流媒体` 组，规则位于 `🍎 苹果服务` 之前（`apple` 分类含 `apple-tvplus`）。YouTube、TikTok、Emby、Bahamut 保持独立。
- **Google 学术归入谷歌服务**：在 `📚 学术资源` 之前插入 `GEOSITE,google-scholar`，Google 学术走 `🇬 谷歌服务`；其余学术域名仍由 `📚 学术资源`（Google Scholar 以外的 IEEE、ACM、出版平台等）处理。
- **真实节点选择**：删除国家/地区、`🌐 其他地区`、`🐢 低倍率节点` 和 `🏠 家宽节点` 策略组及其入口；常规选择组通过 `.*` 展开订阅中的真实节点，其余策略选项的相对顺序遵循上游。
- **Bing 归入微软服务**：删除上游 `🤖 Copilot` 组与规则，`bing` 由 `Ⓜ️ 微软服务` 接管。
- **上游规则同步**：其他服务的分流规则和远程规则地址沿用 Full 模板，每次更新重新应用个人设置。

规则只引用已有 GeoSite 分类，不维护自有域名清单。`anthropic`、`google-deepmind`、`openai` 等分类同时属于 `category-ai-!cn`，因此单列规则必须位于该聚合规则之前；NotebookLM 按 `google-deepmind` 分类进入 Gemini 组。

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
| `custom/rules_prepend.txt` | 单列 AI 分组的 GeoSite 规则，插在国外 AI 聚合之前 |
| `custom/groups_extra.txt` | 新增 Claude、Gemini 策略组 |
| `custom/groups_override.txt` | 覆盖已有策略组的选项与默认出口 |
| `custom/rules_append.txt` | 在 FINAL 规则前插入规则 |
| `.github/workflows/update-rules.yml` | 自动同步工作流 |

## 自定义

在 `custom/groups_override.txt` 中添加完整的 `custom_proxy_group=` 行即可覆盖已有策略组。使用上游原名，例如 `📚 学术资源`；选择组的第一个选项为默认出口。

`custom/groups_extra.txt` 用于调整新增 AI 组的默认选项与顺序。`custom/rules_prepend.txt` 只放需要单列的 AI GeoSite 分类。个人设置在每次同步时重新应用。已取消的分组（国家/地区组、`🏠 家宽节点`、`🤖 Copilot`，以及已并入 `🎥 流媒体` 的上游影音组）不可覆盖。

Telegram 单列、流媒体合并、Google 学术归入谷歌服务等位置敏感的改写由 `scripts/update_rules.py` 完成，不在 `custom/` 文件中维护。

本地生成：

```bash
python3 scripts/update_rules.py
```

使用本地 Full 模板校验：

```bash
python3 scripts/update_rules.py --source-file upstream-full.ini --check
```

## 使用条件

转换器和客户端的 GeoSite 数据包需要包含引用的分类。真实节点由订阅转换器展开。实际连接、DNS 与流量接管效果取决于订阅、转换器和客户端配置。

## 来源与许可

本项目生成的配置衍生自 Aethersailor 的 Full 模板，保留上游署名，并遵循上游声明的 **CC BY-SA 4.0** 许可。GeoSite 分类来自 [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)。改动说明见 [NOTICE.md](NOTICE.md)。

