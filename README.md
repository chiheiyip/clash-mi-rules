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
| `clash-mi-detail-sslvpn.yaml` | `clash-mi-detail.yaml` + local EasyConnect SOCKS5 + selective campus-resource routing. |
| `openclash.yaml` | **Cudy daily-use** config (no exit-node). Based on `clash-mi-detail.yaml` + IPv6 off + `router_self_proxy=0`. |
| `openclash-sslvpn.yaml` | **Cudy campus access from off campus.** `openclash.yaml` + local EasyConnect SOCKS5 + campus policy group. |
| `openclash-backnode.yaml` | **Cudy exit-node** config. `openclash.yaml` + VLESS WebSocket listener on `127.0.0.1:10443` (for Cloudflare Tunnel / campus exit). |

### SCUT campus-network protection / 华南理工校园网适配

All five configs exclude the campus authentication portal and network-connectivity probes from proxying (top-priority `直连` rules):

- `fake-ip-filter`: `s.scut.edu.cn`, `connect.rom.miui.com`, `+.msftconnecttest.com`, `+.msftncsi.com`
- `rules:` top: `DOMAIN,s.scut.edu.cn`, `IP-CIDR,202.38.210.131/32`, `DOMAIN,connect.rom.miui.com`, `DOMAIN-SUFFIX,msftconnecttest.com`, `DOMAIN-SUFFIX,msftncsi.com` → `直连`

These portal/probe entries (Portal, MIUI/MSFT connectivity check) are safe to keep on any normal network — they only exclude known probe domains from proxying and do not break ordinary connectivity.

Cudy/OpenClash variants additionally set top-level `ipv6: false` and `dns.ipv6: false`, and require **OpenClash UCI `router_self_proxy=0`** so the router's own `scut_portal_login.sh`, EasyConnect control traffic and system traffic are not transparently proxied.

#### Portability principle / 可移植原则

The five configs never hard-code a device interface (e.g. `#apclix0`) in the DNS section, so they work across phones, PCs, routers, and any WAN type (`eth` / `pppoe` / `wwan` / `usb` / `apcli`). DNS normally uses plain IPs with Mihomo fallback / split rules.

#### Static DNS / no DHCP recursion / 静态 DNS · 无 DHCP 递归

All five configs keep the DNS upstream **static, explicit and DHCP-recursion-free**: `nameserver`, `default-nameserver`, `proxy-server-nameserver` and `direct-nameserver` use only fixed public DNS (`223.5.5.5` + `119.29.29.29`; the two `clash-mi-detail*` files also add `tls://1.1.1.1` / `tls://8.8.8.8` as `fallback`). Never insert `dhcp://`, `dhcp://apclix0`, `system`, the campus-gateway DNS, or any DNS dynamically obtained from WAN DHCP — those create a DNS upstream loop and cause `7874` query pile-up, timeouts and high CPU.

`respect-rules` is intentionally left off / unconfigured.

> **OpenClash runtime gotcha:** if `/etc/openclash/openclash.yaml` still shows `dhcp://"apclix0"` (or other WAN DNS) after startup even though the source YAML has none, that is OpenClash itself appending WAN/DHCP DNS during its startup phase. Fix it in **OpenClash settings → disable “DNS override / append WAN DNS”**, not in the source YAML — otherwise the loop keeps being re-injected at runtime.

#### SCUT / Cudy interface binding / 接口绑定说明

This repository is the SCUT/Cudy deployment itself — these configs **are** the Cudy/SCUT local-deployment configs, not a separate “local” variant. The DNS upstreams are left as bare public IPs so they stay portable across the WAN type the router actually uses (`eth` / `pppoe` / `wwan` / `usb` / `apcli`).

When you deploy on a Cudy whose campus Wi-Fi WAN egress really is the `apclix0` interface (e.g. a 4G module wired to a campus Wi-Fi AP), you can force DNS out of the campus WAN by binding the upstreams to that interface:

```yaml
# in the dns: section of any config
nameserver:
  - '223.5.5.5#apclix0'
  - '119.29.29.29#apclix0'
# do the same for default-nameserver / proxy-server-nameserver / direct-nameserver
#   if you need the same interface binding there.
```

The SSLVPN configs carry `SCUT Campus` as an inline classical rule-provider, so updating one YAML also updates campus domains/IPs; no second local rule file is required. CI proves each SSLVPN file differs from its base only by this validated EasyConnect overlay.

> The two `clash-mi-detail*` files (IPv6 enabled) include IPv6 private-network direct rules (`::1/128`, `fc00::/7`, `fe80::/10`). The three OpenClash configs have global IPv6 off, so they keep IPv4-private direct rules only.

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

### EasyConnect / bidirectional campus networking

The ARM GUI/noVNC EasyConnect container is a **one-time Cudy host deployment**, not Mihomo YAML. Publish its unauthenticated SOCKS5 endpoint only on host `127.0.0.1:1080`; complete SMS verification through noVNC. Afterwards, normal maintenance remains a single-YAML replacement (`openclash-sslvpn.yaml`, or `clash-mi-detail-sslvpn.yaml` when Mihomo and EasyConnect share another host).

The SSLVPN variants use Mihomo's `type: inline` rule-provider and therefore require a recent core that supports it; CI validates against the latest stable release. Mihomo v1.18.10 does not support `inline`, so upgrade the OpenClash core once during EasyConnect deployment if the Cudy still runs that version. The original three configs are unaffected.

| Scenario | Selection |
|----------|-----------|
| On campus | Use `openclash-sslvpn.yaml` and select `直连` in `校园网`, or keep using `openclash.yaml`. |
| Off-campus EasyConnect | Log the container into `sslvpn2.scut.edu.cn` or `sslvpn3.scut.edu.cn`; keep `校园网-故转` or select `SCUT-EasyConnect`. |
| Campus exit-node | Keep `openclash-backnode.yaml` on the on-campus Cudy and expose its campus exit through Cloudflare Tunnel/VLESS. |

`校园网-故转` checks the local SOCKS5 every 60 seconds, preferring EasyConnect and falling back to direct. Only the inline campus rule-set (SCUT systems, HPC login nodes and common library databases) enters this group; all AI/media/region/general traffic retains the original routing. Portal and SSLVPN control-plane domains stay higher-priority DIRECT to prevent recursion.

## Group Layout / 分组结构

### Business Groups / 业务分流组 (31 base groups; SSLVPN adds `校园网`)

- **AI (5)**: ChatGPT / Claude / Gemini / Grok (xAI: grok.com, x.ai) / 其他AI (Groq, Copilot, Meta AI, Perplexity…)
  - **Claude**: Now includes comprehensive official domains (anthropic.com, claude.ai, claude.com, clau.de, claudemcpclient.com, claudeusercontent.com, CDN endpoints, Auth0), IP ranges (160.79.104.0/21, 2607:6bc0::/32), and AS399358. Optional shared telemetry rules (sentry.io, intercom, datadog, statsigapi.net) are documented but commented out by default to avoid affecting other services.
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
RULE-SET,SCUT Campus,校园网        # SSLVPN only; after Portal/control-plane DIRECT rules
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

External providers are fetched via `gh-proxy.com` (China GitHub mirror); the SSLVPN-only `SCUT Campus` provider is inline:
- [metacubex/meta-rules-dat](https://github.com/metacubex/meta-rules-dat) — `.mrs` GeoSite/GeoIP datasets (updated frequently)
- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) — `.list` rule sets

## Note / 注意

- This is a **template** — you must fill in your own airport subscription URL before use.
- `secret` is the API controller secret (currently a placeholder); change it to your own strong password if your instance is reachable externally.
- Rule-set URLs may occasionally be rate-limited by `gh-proxy.com` (403). Retry or reload to resolve.

## Development / 开发运维 (CI & Releases)

Every change to the configs is verified automatically so a broken edit is caught at merge time, not on deployment day.

### CI (`.github/workflows/ci.yml`)

Runs on every `push`/`PR` touching the configs or scripts, and on a **nightly schedule** (03:17 UTC) to catch a silently-broken rule mirror:

| Check | What it does |
|-------|--------------|
| YAML + consistency | `scripts/validate.py` — parse all five configs; check DNS/interface guards, providers, the EasyConnect node/groups, Portal/campus priority, and that each SSLVPN file is only the expected overlay on its base |
| Mihomo config test | `scripts/mihomo_test.sh` — fetches the official `mihomo` binary, substitutes the airport-subscription placeholder + a safe secret on a **copy**, runs `mihomo -t` on each config |
| Rule URL availability | `scripts/check_rules.py` — concurrently HEAD/GET every `rule-provider` URL + the health probe `gstatic.com/generate_204` |

### Release (`.github/workflows/release.yml`)

Tag-based, versioned releases so a specific config set can be pinned and rolled back to:

```bash
git tag v0.1.0
git push origin v0.1.0
```

A GitHub Release is created with a `clash-mi-rules-<version>.tar.gz` bundle (the five configs, READMEs, scripts) plus a `MANIFEST.txt` with a SHA-256 per file. CI validation gates every release.

### Run the checks locally

```bash
pip install pyyaml
python3 scripts/validate.py          # offline structural checks
python3 scripts/check_rules.py      # online rule-URL availability
bash scripts/mihomo_test.sh --bin ./bin/mihomo   # needs a mihomo binary
```

## License / 许可

MIT

---

**Disclaimer**: This project is for personal / lawful use. Users are responsible for complying with local laws and regulations.
**免责声明**: 本项目仅供个人合法使用,使用者需自行遵守所在地法律法规。
