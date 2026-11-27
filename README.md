# Clash Mi Rules

English | [中文文档](README_zh.md)

A refined, ready-to-use Clash Mi / Mihomo (Clash.Meta) routing configuration with **fine-grained traffic splitting**, stable `url-test` + `fallback` strategy, and well-maintained upstream rule sources.

完全为 **Clash Mi / Mihomo (Clash.Meta)** 内核调校的细化分流配置,开箱即用,规则来源全部换成主流权威上游(meta-rules-dat `.mrs` + blackmatrix7 `.list`)。

## Features / 特性

- ✅ **Fine-grained splitting**: AI / social / streaming / cloud / gaming / crypto are split into separate groups.
- ✅ **Stable strategy**: `url-test` + `fallback`, no experimental `smart`/LightGBM — reliable on any Mihomo kernel (Clash Mi included).
- ✅ **Auto node preference**: per-country groups with `手动 (manual) + 自动 (auto url-test) + 故转 (failover fallback)`.
- ✅ **Fresh rule sources**: only `metacubex/meta-rules-dat` (`.mrs`) and `blackmatrix7/ios_rule_script` (`.list`); no unmaintained personal lists.
- ✅ **Rule-set URLs checked nightly in CI** (with retry and a backup mirror).

## Files / 文件

| File | Description |
|------|-------------|
| `clash-mi-detail.yaml` | General config for any ClashMi/Mihomo client (mobile/desktop). Includes campus-network portal protection. |
| `openclash.yaml` | **Cudy daily-use** config (no exit-node). Based on `clash-mi-detail.yaml` + IPv6 off + `router_self_proxy=0`. |
| `openclash-backnode.yaml` | **Cudy exit-node** config. `openclash.yaml` + VLESS WebSocket listener on `127.0.0.1:10443` (for Cloudflare Tunnel / campus exit). |

### Campus-network portal protection / 校园网认证适配

All three configs exclude the campus authentication portal and network-connectivity probes from proxying (top-priority `直连` rules):

- `fake-ip-filter`: `s.scut.edu.cn`, `connect.rom.miui.com`, `+.msftconnecttest.com`, `+.msftncsi.com`
- `rules:` top: `DOMAIN,s.scut.edu.cn`, `IP-CIDR,202.38.210.131/32`, `DOMAIN,connect.rom.miui.com`, `DOMAIN-SUFFIX,msftconnecttest.com`, `DOMAIN-SUFFIX,msftncsi.com` → `直连`

These portal/probe entries (Portal, MIUI/MSFT connectivity check) are safe to keep on any normal network — they only exclude known probe domains from proxying and do not break ordinary connectivity.

Cudy/OpenClash variants additionally set top-level `ipv6: false` and `dns.ipv6: false`, and require **OpenClash UCI `router_self_proxy=0`** so the router's own campus auto-login script and system traffic are not transparently proxied.

#### Portability principle / 可移植原则

The three configs never hard-code a device interface (e.g. `#apclix0`) in the DNS section, so they work across phones, PCs, routers, and any WAN type (`eth` / `pppoe` / `wwan` / `usb` / `apcli`). DNS normally uses plain IPs with Mihomo fallback / split rules.

#### Static DNS / no DHCP recursion / 静态 DNS · 无 DHCP 递归

All three configs keep the DNS upstream **static, explicit and DHCP-recursion-free**: `nameserver`, `default-nameserver`, `proxy-server-nameserver` and `direct-nameserver` use only fixed public DNS (`223.5.5.5` + `119.29.29.29`; `clash-mi-detail.yaml` also adds `tls://1.1.1.1` / `tls://8.8.8.8` as `fallback`). Never insert `dhcp://`, `dhcp://apclix0`, `system`, the campus-gateway DNS, or any DNS dynamically obtained from WAN DHCP — those create a DNS upstream loop and cause `7874` query pile-up, timeouts and high CPU.

`respect-rules` is intentionally left off / unconfigured.

> **OpenClash runtime gotcha:** if `/etc/openclash/openclash.yaml` still shows `dhcp://"apclix0"` (or other WAN DNS) after startup even though the source YAML has none, that is OpenClash itself appending WAN/DHCP DNS during its startup phase. Fix it in **OpenClash settings → disable “DNS override / append WAN DNS”**, not in the source YAML — otherwise the loop keeps being re-injected at runtime.

#### Campus / Cudy interface binding / 接口绑定说明

This repository is the campus/Cudy deployment itself — the three configs **are** the Cudy campus local-deployment configs, not a separate “local” variant. The DNS upstreams are left as bare public IPs so they stay portable across the WAN type the router actually uses (`eth` / `pppoe` / `wwan` / `usb` / `apcli`).

When you deploy on a Cudy whose campus Wi-Fi WAN egress really is the `apclix0` interface (e.g. a 4G module wired to a campus Wi-Fi AP), you can force DNS out of the campus WAN by binding the upstreams to that interface:

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
  - **Claude**: hand-written official domains (anthropic.com, claude.ai, claude.com, clau.de, claudemcpclient.com, claudeusercontent.com, CDN endpoints, Auth0), IP ranges (160.79.104.0/21, 2607:6bc0::/32; no `IP-ASN` rule, so startup needs no ASN database), plus the official `geosite/anthropic` set (claude.app, claude.dev, ant.dev…). Optional shared telemetry rules (cdn.usefathom.com, sentry.io, intercom, datadog, statsigapi.net) stay commented out by default to avoid affecting other services.
  - **Copilot** uses 7 hand-written Microsoft Copilot rules. blackmatrix7's `Copilot.list` is not used: it bundles services shared by countless websites (stripe.com, auth0.com, challenges.cloudflare.com, sentry.io, intercom.io …) plus the whole DigitalOcean / Vultr ASNs, which sent other sites' payments and CAPTCHAs out through a different exit IP than the page itself.
  - **Meta AI** matches only `meta.ai` / `ai.meta.com` — `geosite/meta` would also capture Facebook / Instagram / WhatsApp.
- **Standalone (2)**: GitHub / LinuxDo
- **Social (8)**: X / Instagram / Telegram / WhatsApp / Facebook / TikTok / Discord / Reddit
- **Streaming (4)**: Netflix / YouTube / Spotify / Stream Media (Disney, HBO, Prime Video, Crunchyroll, Popcorn…)
- **Cloud & System (5)**: Google / Microsoft / Apple / Nvidia / Cloud (Adobe…)
- **Gaming (1)**: Games (Steam, Epic, EA, Blizzard, UBI, PlayStation, Nintendo…)
- **Crypto (1)**: Crypto (OKX, Bybit, Binance, Kraken, Bybit EU, Ether.fi, Trading 212, Monese, Myfin, Altery…)
- **Fallback (5)**: Test / 国外 / 国内 / 其他 / Block

### Region / Strategy Groups / 地区与策略组

- Global: `所有-手动` / `所有-自动`
- Per region `手动 + 自动 + 故转`: 香港 / 台湾 / 日本 / 新加坡 / 韩国 / 美国 / 英国 / 德国 / 其他

## Routing Order / 分流顺序

Rules match top-down (first match wins). Before the service groups, a **CN-subset** block sends the China-side domains of Microsoft / Apple / Steam / Amazon (`microsoft@cn`, `apple@cn`, `apple-cn`, `steam@cn`, `amazon@cn`) to `国内`, so Windows / Apple updates and Steam's China CDN do not consume proxy traffic.

The fallback funnel:

```
RULE-SET Block  / Domain,Block    # ads / trackers not claimed by a service rule above
RULE-SET Direct / Domain,国内     # known direct domains (NAS DDNS, PT sites, campus-licensed academic sites) → 国内
RULE-SET Proxy  / Domain,国外     # well-known accelerated foreign domains → 国外
RULE-SET China  / Domain,国内     # mainland China domains → 国内
RULE-SET China  / IP,国内         # mainland IPs → 国内
MATCH,其他                        # everything else → 其他
```

`Private / Domain` (localhost, `*.local`, Tailscale `ts.net`, router admin pages) sits at the **very top** with the private IP ranges and always goes `直连`.

Shared payment / login / CAPTCHA services (Stripe, PayPal, Auth0, Cloudflare Turnstile, hCaptcha, Arkose, Intercom) are deliberately **not** claimed by any service group: they take the general route (`国外` / `其他`), i.e. the same exit as the website embedding them. CI enforces this nightly (`scripts/audit_routes.py`).

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
- Rule-set URLs may occasionally be rate-limited by `gh-proxy.com` (403). Retry or reload to resolve, or switch to the backup mirror with the `sed` command in the `rule-providers` comment.
- Only `clash-mi-detail.yaml` needs a GEO database (GeoIP mmdb, for `dns.fallback-filter`); it is downloaded through `gh-proxy.com` via `geox-url`, only when missing locally. The OpenClash configs need none. `geo-auto-update` is intentionally off (flash wear on routers; OpenClash has its own updater).

## Development / 开发运维 (CI & Releases)

Every change to the configs is verified automatically so a broken edit is caught at merge time, not on deployment day.

### CI (`.github/workflows/ci.yml`)

Runs on every `push`/`PR` touching the configs or scripts, and on a **nightly schedule** (03:17 UTC) to catch a silently-broken rule mirror:

| Check | What it does |
|-------|--------------|
| YAML + consistency | `scripts/validate.py` — parse every `*.yaml`, verify required top-level keys, DNS recursion guard (no `dhcp://`/`system`/`apclix0` in live config), portability guard (no hard-coded `IP#interface` binding in live code), rule-provider URL sanity, and **three-config parity**: the OpenClash configs must match `clash-mi-detail.yaml` rule by rule and group by group except for the documented differences (IPv6, DNS fallback, `find-process-mode`, `listeners`) |
| Mihomo config test | `scripts/mihomo_test.sh` — substitutes the airport-subscription placeholder + a safe secret on a **copy** and runs `mihomo -t` on each config. Runs against the **pinned** kernel (v1.19.34, blocking) and the **latest** release (non-blocking early warning) |
| Routing expectations | `scripts/audit_routes.py` — downloads the current upstream lists, replays the rules top-down and checks `scripts/route_expectations.txt` (shared payment / CAPTCHA services on the general route, LAN direct, every service in its group). Catches upstream lists that start capturing shared domains |
| Rule URL availability | `scripts/check_rules.py` — concurrently checks every `rule-provider` and `geox-url` URL + the health probe `gstatic.com/generate_204`, retrying with backoff; a URL that only works on the backup mirror is a warning, not a failure |

### Release (`.github/workflows/release.yml`)

Tag-based, versioned releases so a specific config set can be pinned and rolled back to:

```bash
git tag v0.1.0
git push origin v0.1.0
```

A GitHub Release is created with a `clash-mi-rules-<version>.tar.gz` bundle (the three configs, READMEs, CHANGELOG, scripts) plus a `MANIFEST.txt` with a SHA-256 per file. Before packaging, the tagged revision must pass offline validation (including the OpenClash upload header) and `mihomo -t` on all three configs. Rule-mirror availability is reported separately.

### Run the checks locally

```bash
pip install pyyaml
python3 scripts/validate.py          # offline structural checks
python3 scripts/check_rules.py      # online rule-URL availability
python3 scripts/audit_routes.py     # online routing simulation vs route_expectations.txt
bash scripts/mihomo_test.sh --bin ./bin/mihomo   # needs a mihomo binary
```

## License / 许可

MIT

---

**Disclaimer**: This project is for personal / lawful use. Users are responsible for complying with local laws and regulations.
**免责声明**: 本项目仅供个人合法使用,使用者需自行遵守所在地法律法规。
