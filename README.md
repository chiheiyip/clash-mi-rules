# Clash Mi Rules

English | [中文文档](README_zh.md)

A refined, ready-to-use Clash Mi / Mihomo (Clash.Meta) routing configuration with **fine-grained traffic splitting**, stable `url-test` + `fallback` strategy, and well-maintained upstream rule sources.

完全为 **Clash Mi / Mihomo (Clash.Meta)** 内核调校的细化分流配置,开箱即用,规则来源全部换成主流权威上游(meta-rules-dat `.mrs` + blackmatrix7 `.list`)。

## Features / 特性

- ✅ **Fine-grained splitting**: AI / social / streaming / cloud / gaming / crypto are split into separate groups.
- ✅ **Stable strategy**: `url-test` + `fallback`, no experimental `smart`/LightGBM — reliable on any Mihomo kernel (Clash Mi included).
- ✅ **Auto node preference**: per-country groups with `手动 (manual) + 自动 (auto url-test) + 故转 (failover fallback)`.
- ✅ **Fresh rule sources**: only `metacubex/meta-rules-dat` (`.mrs`) and `blackmatrix7/ios_rule_script` (`.list`); no unmaintained personal lists.
- ✅ **All rule-set URLs verified** (HTTP 200).

## Files / 文件

| File | Description |
|------|-------------|
| `clash-mi-detail.yaml` | The refined configuration (main file) |

## Download Clash Mi / 下载 Clash Mi

This config is built for **Clash Mi** (a Clash/Mihomo GUI client). Get it here:

- Official site: <https://clashmi.app>
- GitHub Releases (all platforms): <https://github.com/KaringX/clashmi/releases/latest>
  - Windows: `clashmi_*_windows_x64.exe` / `.zip`
  - macOS: `clashmi_*_macos_universal.dmg`
  - Linux: `clashmi_*_linux_amd64.deb` / `.rpm` / `.AppImage`
  - Android: `clashmi_*_android_arm64-v8a.apk` (or arm / armeabi-v7a)
- iOS (App Store, search “clash mi”): <https://apps.apple.com/us/app/clash-mi/id6744321968>

> Any other site claiming to be Clash Mi is unofficial. Only use `clashmi.app` or the official GitHub Releases.

## Quick Start / 快速开始

1. Open `clash-mi-detail.yaml`.
2. In `proxy-providers`, replace `url: "机场订阅地址"` with your real airport (provider) subscription URL, and rename `机场名称`.
3. (Optional) Change `secret` (placeholder) to your own strong password if you care.
4. Import the file into Clash Mi (or any Mihomo client) as a config / override subscription.

## Group Layout / 分组结构

### Business Groups / 业务分流组 (31)

- **AI (5)**: ChatGPT / Claude / Gemini / Grok (xAI: grok.com, x.ai) / 其他AI (Groq, Copilot, Meta AI, Perplexity…)
- **Standalone (2)**: GitHub / LinuxDo
- **Social (8)**: X / Instagram / Telegram / WhatsApp / Facebook / TikTok / Discord / Reddit
- **Streaming (4)**: Netflix / YouTube / Spotify / Stream Media (Disney, HBO, Amazon, Crunchyroll, Popcorn…)
- **Cloud & System (5)**: Google / Microsoft / Apple / Nvidia / Cloud (Adobe…)
- **Gaming (1)**: Games (Steam, Epic, EA, Blizzard, UBI, PlayStation, Nintendo…)
- **Crypto (1)**: Crypto (OKX, Bybit, Binance, Kraken, Bybit EU, Ether.fi, Trading 212, Monese, Myfin, Altery…)
- **Fallback (5)**: Test / 国外 / 国内 / 其他 / Block

### Region / Strategy Groups / 地区与策略组

- Global: `所有-手动` / `所有-自动`
- Per region `手动 + 自动 + 故转`: 香港 / 台湾 / 日本 / 新加坡 / 韩国 / 美国 / 英国 / 德国 / 其他

## Routing Order / 分流顺序

Rules match top-down (first match wins). The fallback funnel:

```
RULE-SET Proxy / Domain,国外      # well-known accelerated foreign domains → 国外
RULE-SET Direct / Domain,国内     # known direct domains → 国内
RULE-SET China / Domain,国内      # mainland China domains → 国内
RULE-SET China / IP,国内          # mainland IPs → 国内
RULE-SET Private/ Domain,国内     # LAN / reserved → 国内
MATCH,其他                        # everything else → 其他
```

- **国外 (Overseas)**: foreign domains explicitly listed for acceleration.
- **国内 (Domestic)**: mainland China / direct-connect domains & IPs.
- **其他 (Other)**: the final catch-all for anything not matched above.

## Rule Sources / 规则来源

All providers are fetched via `gh-proxy.com` (China GitHub mirror) from:
- [metacubex/meta-rules-dat](https://github.com/metacubex/meta-rules-dat) — `.mrs` GeoSite/GeoIP datasets (updated frequently)
- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) — `.list` rule sets

## Note / 注意

- This is a **template** — you must fill in your own airport subscription URL before use.
- `secret` is the API controller secret (currently a placeholder); change it to your own strong password if your instance is reachable externally.
- Rule-set URLs may occasionally be rate-limited by `gh-proxy.com` (403). Retry or reload to resolve.

## License / 许可

MIT

---

**Disclaimer**: This project is for personal / lawful use. Users are responsible for complying with local laws and regulations.
**免责声明**: 本项目仅供个人合法使用,使用者需自行遵守所在地法律法规。
