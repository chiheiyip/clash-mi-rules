# Clash Mi Rules

[English](README.md) | 中文文档

为 **Clash Mi / Mihomo (Clash.Meta)** 内核设计的**细化分流配置**。采用主流稳定策略,规则来源全部换成权威上游(meta-rules-dat `.mrs` + blackmatrix7 `.list`),开箱即用。

## 特性

- ✅ **细化分流**:AI / 社交 / 流媒体 / 云 / 游戏 / Crypto 各自独立分组。
- ✅ **稳定的策略**:`url-test` + `fallback`,不使用实验性的 `smart`/LightGBM,任意 Mihomo 内核(含 Clash Mi)都可稳定运行。
- ✅ **自动优选节点**:每个地区组包含 `手动` + `自动(url-test 测速)` + `故转(fallback 故障转移)` 三层。
- ✅ **更新的规则来源**:只用 `metacubex/meta-rules-dat`(`.mrs`)和 `blackmatrix7/ios_rule_script`(`.list`),不依赖个人维护的旧列表。
- ✅ **所有规则集 URL 已验证**(HTTP 200)。

## 文件

| 文件 | 说明 |
|------|------|
| `clash-mi-detail.yaml` | 细化分流配置(主文件) |

## 下载 Clash Mi

本配置面向 **Clash Mi**(Clash/Mihomo 图形客户端)开发。下载地址:

- 官网:<https://clashmi.app>
- GitHub Releases(全平台):<https://github.com/KaringX/clashmi/releases/latest>
  - Windows:`clashmi_*_windows_x64.exe` / `.zip`
  - macOS:`clashmi_*_macos_universal.dmg`
  - Linux:`clashmi_*_linux_amd64.deb` / `.rpm` / `.AppImage`
  - Android:`clashmi_*_android_arm64-v8a.apk`(或 arm / armeabi-v7a)
- iOS(App Store 搜索 “clash mi”):<https://apps.apple.com/us/app/clash-mi/id6744321968>

> 其他声称是 Clash Mi 的站点均为非官方,请只认 `clashmi.app` 或官方 GitHub Releases。

## 快速开始

1. 打开 `clash-mi-detail.yaml`。
2. 在 `proxy-providers` 里,把 `url: "机场订阅地址"` 换成你机场的真实订阅链接,并把 `机场名称` 改成你机场的名字。
3. (可选)如果你介意默认的 `secret`(占位符),改成你自己的强密码。
4. 将该文件作为配置 / 订阅导入 Clash Mi(或其他 Mihomo 客户端)。

## 分组结构

### 业务分流组(31)

- **AI(5)**:ChatGPT / Claude / Gemini / Grok(xAI:grok.com、x.ai)/ 其他AI(Groq、Copilot、Meta AI、Perplexity…)
- **独立站点(2)**:GitHub / LinuxDo
- **社交(8)**:X / Instagram / Telegram / WhatsApp / Facebook / TikTok / Discord / Reddit
- **流媒体(4)**:Netflix / YouTube / Spotify / Stream Media(Disney、HBO、Amazon、Crunchyroll、Popcorn…)
- **云与系统(5)**:Google / Microsoft / Apple / Nvidia / Cloud(Adobe…)
- **游戏(1)**:Games(Steam、Epic、EA、Blizzard、UBI、PlayStation、Nintendo…)
- **Crypto(1)**:Crypto(OKX、Bybit、Binance、Kraken、Bybit EU、Ether.fi、Trading 212、Monese、Myfin、Altery…)
- **兜底(5)**:Test / 国外 / 国内 / 其他 / Block

### 地区与策略组

- 全局:`所有-手动` / `所有-自动`
- 每个地区一组 `手动 + 自动 + 故转`:香港 / 台湾 / 日本 / 新加坡 / 韩国 / 美国 / 英国 / 德国 / 其他

## 分流顺序

规则自上而下匹配(命中即停)。兜底漏斗如下:

```
RULE-SET Proxy / Domain,国外      # 明确要加速的海外域名 → 国外
RULE-SET Direct / Domain,国内     # 已知直连域名 → 国内
RULE-SET China / Domain,国内      # 中国大陆域名 → 国内
RULE-SET China / IP,国内          # 大陆 IP → 国内
RULE-SET Private/ Domain,国内     # 内网 / 保留地址 → 国内
MATCH,其他                        # 其余全部 → 其他
```

- **国外**:规则里明确点名要加速的海外域名。
- **国内**:中国大陆 / 需直连的域名和 IP。
- **其他**:最后的兜底,承接上面规则没匹配到的一切。

## 规则来源

所有 provider 经 `gh-proxy.com`(GitHub 加速镜像)拉取:
- [metacubex/meta-rules-dat](https://github.com/metacubex/meta-rules-dat) — `.mrs` GeoSite/GeoIP 数据库(更新频繁)
- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) — `.list` 规则集

## 注意

- 这是**模板**——使用前必须填入你自己的机场订阅链接。
- `secret` 是 API 控制器密钥(当前为占位符);若你的实例可被外部访问,务必改成你自己的强密码。
- `gh-proxy.com` 偶发限流(返回 403),重试或重新加载即可。

## 许可

MIT

---

**免责声明**:本项目仅供个人合法使用,使用者需自行遵守所在地法律法规。
