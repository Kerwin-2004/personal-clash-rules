# Personal Clash Rules · 国外 AI 独立分流 / 真实节点直选

这是一个基于 [Aethersailor/Custom_OpenClash_Rules](https://github.com/Aethersailor/Custom_OpenClash_Rules)
[Full 重度分流订阅转换模板](https://github.com/Aethersailor/Custom_OpenClash_Rules/blob/main/cfg/Custom_Clash_Full.ini)
的 **SubConverter INI 模板项目**。仅保存规则和策略组，不存放机场订阅、实际节点、密码、密钥。

## 这版做了什么

- **国外 AI 独立策略组**：保留上游 `🤖 ChatGPT`、`🤖 Copilot`（原上游 bing 分类）；新增 Claude、Gemini、Perplexity、Grok、GitHub Copilot、Cursor、Windsurf、Poe。其余国外 AI 使用上游 `🤖 国外AI服务` 兜底。
- **国内 AI 不显示分组，直接直连**：上游 `GEOSITE,category-ai-cn` 改为 `🎯 全球直连`，优先于国外 AI 聚合分类。DeepSeek、豆包等按 GeoSite 类别处理。若某品牌的海外网站被归入国外分类，则仍会按其 GeoSite 实际分类处理。
- **取消国家/地区策略组**：删除香港、美国、日本、韩国、欧洲等国家组及「其他地区」；所有常规业务 `select` 组末尾通过 `.*` **直接列出订阅里的真实节点**。保留每组原有的「🚀 手动选择」「♻️ 自动选择」等已有选项及其相对顺序，不重排默认项；专用「🎯 全球直连」与「🔀 非标端口」沿用原结构。
- **保留家宽，删除低倍率组**：继续采用 Aethersailor Full 已有的 `🏠 家宽节点`，不修改其节点名识别方式。彻底移除 `🐢 低倍率节点` 策略组以及各业务策略组中指向它的选项，不会删除机场订阅里的低倍率**实际节点**。家宽匹配仅根据节点名称，**不能验证节点是否真的为住宅 IP**。
- **保留科研工具**：把上游 `📚 学术资源` 显示名称调整为 `📚 科研工具`，继续使用 `GEOSITE,category-scholar-!cn`（IEEE、Google Scholar、主流学术出版/检索等），不新建域名清单；默认选项遵循上游原配置（可自行改为直连）。
- **其余仍沿用 Aethersailor Full**：测速、PT、下载、Apple、Microsoft、GitHub、即时通讯、游戏、媒体等规则集、顺序和远程更新地址不变。

**不自己维护域名列表。** AI 独立规则仅使用 [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community/tree/master/data) 已有的 `anthropic`、`google-deepmind`、`perplexity`、`xai`、`github-copilot`、`cursor`、`windsurf`、`poe` 等 GeoSite 分类。NotebookLM 随上游 `google-deepmind` 一起走 Gemini 组，不另做手写域名分流。

**注意**：这份 INI 是订阅转换器的规则模板，**不是节点订阅链接**，不能直接代替机场订阅；依赖转换器和客户端所用的 GeoSite 数据包确实包含以上分类。

## 文件结构

```text
.github/workflows/update-rules.yml   # 每日同步 Full 并生成 INI
scripts/update_rules.py              # 上游升级 + 分类注入 + 去国家及低倍率组 + 原始节点直选
custom/rules_prepend.txt             # AI 独立 GeoSite 分类（非手写域名）
custom/groups_extra.txt              # 新增 AI 策略组
custom/groups_override.txt           # 可选：覆盖上游原有策略组
custom/rules_append.txt              # 默认留空
config/Custom_Clash.ini              # Actions 生成，供 SubConverter 的 config= 使用
```

## 部署 GitHub

1. 在 [GitHub 创建空仓库](https://github.com/new)，例如 `personal-clash-rules`，默认分支为 `main`，不需要额外初始化 README。
2. 将本项目解压后完整 push 到仓库，包括隐藏的 `.github/` 目录。
3. 打开 **Actions → Sync upstream Clash rules → Run workflow**，成功后生成 `config/Custom_Clash.ini`。
4. GitHub Actions 每天定时检查 Full 上游是否更新，且修改 `custom/` 或脚本时也会自动重新生成；执行失败时不覆盖旧生成文件。若写入失败，查看 **Settings → Actions → General → Workflow permissions**。
5. 必须使用**自己的正确订阅链接**作为转换器 `url=` 参数；本仓库只是转换器 `config=` 的模板。

推送示例（在解压后的目录执行）：

```bash
git init -b main
git add .
git commit -m "init: personal clash full rules"
git remote add origin https://github.com/YOUR_ACCOUNT/personal-clash-rules.git
git push -u origin main
```

仓库首次运行 Actions 成功后，订阅转换器应把 `config=` 指向下面的 Raw URL，并做好 URL 编码：

```text
https://raw.githubusercontent.com/YOUR_ACCOUNT/personal-clash-rules/main/config/Custom_Clash.ini
```

**不要把完整订阅 URL、订阅凭据或节点链接提交到公开 GitHub。** 私有仓库的匿名 Raw URL 无法被部分在线订阅转换服务访问。

## 分流优先级与实际效果

1. Aethersailor Full 原有的本地网络/私有地址及个别优先直连/代理规则先匹配。
2. ChatGPT 使用上游 `openai`；微软 Copilot 保留上游 `bing`，按原作者配置匹配。
3. Claude、Gemini、Perplexity、Grok、GitHub Copilot、Cursor、Windsurf、Poe 使用各自上游 GeoSite 分类。
4. 国内 AI 使用 `category-ai-cn` 直连；其余国外 AI 使用 `category-ai-!cn` 兜底。
5. 学术资源使用上游 `category-scholar-!cn`；其他流量继续照 Full 默认规则匹配。

新增 AI 组维持原定义：`🚀 手动选择`、`🏠 家宽节点`、`♻️ 自动选择`、以及 `.*` 直接列出的真实节点。上游已有的所有业务组保留原本的自动/手动/直连/家宽选项和默认顺序（低倍率选项除外），**仅删除国家地区及低倍率组入口，并显示实际节点**；不会删除美国、日本、香港等实际节点本身。原本没有自动选择选项的少数业务组也不会被擅自改变。

如果家宽组为空，说明订阅节点名称未匹配上游家宽识别正则，或订阅中没有这样的节点。需要提供**节点名称示例（不要贴订阅凭据）** 才能优化识别，不能单凭配置创造家宽代理。

## 定制与更新

- 在 `custom/rules_prepend.txt` 增减 GeoSite 引用，不复制人工拼凑的域名列表。
- 在 `custom/groups_extra.txt` 调整新增 AI 组默认选项和排列顺序。
- 在 `custom/groups_override.txt` 通过完整 `custom_proxy_group=` 行覆写现有策略组。覆盖科研组时仍使用上游**原名** `📚 学术资源`，生成时会自动改名为 `📚 科研工具`。
- `python3 scripts/update_rules.py --source-file upstream-full.ini --check` 可用本地保存的 Full 模板离线检查；直接执行脚本则从上游下载并生成。
- 订阅真正可用还需转换器正确展开分组、GeoSite 数据包包含这些分类，以及客户端正确配置 DNS/流量接管；**仅凭 INI 无法保证 DNS 不泄漏**。

## 来源与授权

上游为 [Aethersailor/Custom_OpenClash_Rules](https://github.com/Aethersailor/Custom_OpenClash_Rules)，规则模板为其 `cfg/Custom_Clash_Full.ini`。尊重上游文件署名及原项目所声明的 **CC BY-SA 4.0** 许可。规则数据类别来自上游使用的 GeoSite 生态，本项目不声称拥有原始域名列表。

## 切换到 ChatGPT Work 部署

当前对话中的 GitHub 连接能够操作已有授权仓库，但无法在本模式直接新建仓库。打开 ChatGPT 的 **Work** 模式后，让 Work 创建公开仓库 `personal-clash-rules`（owner 由登录的 GitHub 账号决定），将此 ZIP 内 `personal-clash-rules/` 文件夹中的文件全部推送到默认 `main` 分支，开启 Actions 写入权限，手动运行一次 `Sync upstream Clash rules`，再核查 `config/Custom_Clash.ini` 已生成、包含 AI 和科研独立组、没有国家策略组/低倍率组，但保留全部实际节点和家宽组。**不要把私人机场订阅 URL、节点信息、令牌写入仓库。**
