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
| `clash-mi-detail.yaml` | General config for any ClashMi/Mihomo client (mobile/desktop). Includes SCUT campus-network protection. |
| `openclash.yaml` | **Cudy daily-use** config (no exit-node). Based on `clash-mi-detail.yaml` + IPv6 off + `router_self_proxy=0`. |
| `openclash-backnode.yaml` | **Cudy exit-node** config. `openclash.yaml` + VLESS WebSocket listener on `127.0.0.1:10443` (for Cloudflare Tunnel / campus exit). |

### SCUT campus-network protection / 华南理工校园网适配

All three configs exclude the campus authentication portal and network-connectivity probes from proxying (top-priority `直连` rules):

- `fake-ip-filter`: `s.scut.edu.cn`, `connect.rom.miui.com`, `+.msftconnecttest.com`, `+.msftncsi.com`
- `rules:` top: `DOMAIN,s.scut.edu.cn`, `IP-CIDR,202.38.210.131/32`, `DOMAIN,connect.rom.miui.com`, `DOMAIN-SUFFIX,msftconnecttest.com`, `DOMAIN-SUFFIX,msftncsi.com` → `直连`

These portal/probe entries (Portal, MIUI/MSFT connectivity check) are safe to keep on any normal network — they only exclude known probe domains from proxying and do not break ordinary connectivity.

Cudy/OpenClash variants additionally set top-level `ipv6: false` and `dns.ipv6: false`, and require **OpenClash UCI `router_self_proxy=0`** so the router's own `scut_portal_login.sh` and system traffic are not transparently proxied.

#### Portability principle / 可移植原则

The three configs never hard-code a device interface (e.g. `#apclix0`) in the DNS section, so they work across phones, PCs, routers, and any WAN type (`eth` / `pppoe` / `wwan` / `usb` / `apcli`). DNS normally uses plain IPs with Mihomo fallback / split rules.

#### SCUT / Cudy overlay / 华南理工 · Cudy 特例说明

`#apclix0` is **only** a SCUT/Cudy campus-Wi-Fi special case, not part of the defaults. If your device is on campus Wi-Fi and the actual campus WAN egress interface is `apclix0` (e.g. Cudy with a 4G module wired to a campus Wi-Fi AP), you can force DNS out of the campus WAN by editing the DNS upstreams to:

```yaml
# in the dns: section of any config
nameserver:
  - '223.5.5.5#apclix0'
  - '119.29.29.29#apclix0'
# do the same for default-nameserver / proxy-server-nameserver / direct-nameserver
#   if you need the same interface binding there.
```

This small overlay is intentionally not shipped as a fourth config file to avoid long-term drift across 3–4 large configs. Apply it locally on your Cudy when deploying, or keep it as a short README note.

> For `clash-mi-detail.yaml` (IPv6 enabled), the private-network direct rules include IPv6 (`::1/128`, `fc00::/7`, `fe80::/10`). The two OpenClash configs have global IPv6 off, so they keep IPv4-private direct rules only.

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

### General client (Clash Mi / Mihomo)

1. Open `clash-mi-detail.yaml`.
2. In `proxy-providers`, replace `url: "机场订阅地址"` with your real airport (provider) subscription URL, and rename `机场名称`.
3. (Optional) Change `secret` (placeholder) to your own strong password if you care.
4. Import the file into Clash Mi (or any Mihomo client) as a config / override subscription.

### Cudy / OpenClash (campus exit node)

1. **Daily use (no exit-node):** import `openclash.yaml`. Set OpenClash UCI `router_self_proxy=0`, both `ipv6` flags already `false`.
2. **Campus exit-node (Cloudflare Tunnel → VLESS/WS):** import `openclash-backnode.yaml`. Replace the `YOUR_VLESS_UUID_PLACEHOLDER` UUID with the real UUID issued to ClashMi by XBoard, then point Cloudflare Tunnel public host `tunnel.freeapp.tech` → HTTP → `127.0.0.1:10443` (path left empty). Client node: VLESS, host `tunnel.freeapp.tech:443`, transport WebSocket, path `/`, TLS on, SNI/Host `tunnel.freeapp.tech`, Flow empty, Reality off.

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
