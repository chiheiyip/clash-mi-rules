# Changelog / 更新日志

All three configs (`clash-mi-detail.yaml`, `openclash.yaml`, `openclash-backnode.yaml`)
are changed together; CI enforces that they stay in sync.

三份配置始终同步修改,CI 会校验三者一致。

## Unreleased

### Routing fixes / 分流修正
- **Meta AI** now matches only `meta.ai` / `ai.meta.com`. The previous `geosite/meta`
  set also contains facebook.com / instagram.com / whatsapp.com and sat before the
  social rules, so the Instagram / Facebook / WhatsApp groups never matched.
  Meta AI 只匹配 `meta.ai` / `ai.meta.com`;原 `geosite/meta` 含 Facebook / Instagram / WhatsApp,导致这三个组从未生效。
- **Claude** rule set: blackmatrix7 `Claude.list` → official `geosite/anthropic`
  (adds claude.app / claude.dev / ant.dev …; no longer includes the shared
  `cdn.usefathom.com` that the config deliberately leaves commented out).
- **Gemini** rule set: `Gemini.list` (13 rules incl. broad keywords like `colab`) →
  `geosite/google-gemini` (49 exact domains: NotebookLM, AI Studio, Jules, Antigravity …).
- New **CN-subset** block → `国内`: `microsoft@cn`, `apple@cn`, `apple-cn`, `steam@cn`,
  `amazon@cn`. Windows / Apple updates, Steam China CDN and Amazon China go direct.
  新增国内子集,微软 / 苹果更新、Steam 国内 CDN、亚马逊中国直连,不消耗代理流量。
- **Stream Media**: `geosite/amazon` (contains `+.amazonaws.com` / `+.cloudfront.net`)
  → `geosite/primevideo`.

### Performance / 性能
- Text `.list` → binary `.mrs` for Nvidia, Adobe, Epic, EA, UBI, PlayStation.
  Blizzard, Nintendo, WhatsApp and Speedtest stay as text (geosite misses
  battlenet.com / nintendowifi.net / WhatsApp IP ranges, or adds CN speed-test sites).
- Subscriptions: `exclude-filter` drops "剩余流量 / 到期 / 官网" info pseudo-nodes.
- Fallback groups `lazy: true` (Mihomo default); `max-failed-times: 3` on all
  url-test / fallback groups (forced re-test after 3 failed dials instead of 5).
- `unified-delay: true`, `tcp-concurrent: true`.
- OpenClash configs: `find-process-mode: "off"` (quoted: a bare `off` is boolean
  false under YAML 1.1).
- The ad-block list (`Advertising.list`) is intentionally unchanged.

### Startup reliability / 启动可靠性
- `geox-url` → gh-proxy mirror for GeoIP / GeoSite / MMDB / ASN (default is github.com,
  which can fail on a first start in mainland China). `geo-auto-update` left off.
- `fake-ip-filter`: `geosite:cn` → `rule-set:China / Domain`; GeoSite.dat is no longer needed.
- TUN block: comments only (Clash Mi / OpenClash manage it).

### Docs / 文档
- School-specific labels replaced with generic "校园网认证 / campus-network portal"
  wording; the portal domain and IP rules are unchanged.

### CI
- `actions/checkout@v7`, `setup-python@v7`, `action-gh-release@v3` (Node 24).
- Mihomo test: pinned v1.19.34 (blocking) + latest (non-blocking).
- `validate.py`: three-config parity check, `find-process-mode` type check,
  placeholder / UUID warnings.
- `check_rules.py`: retry with backoff, backup-mirror fallback (warning only),
  ranged GET, also checks `geox-url`.
- `mihomo_test.sh`: no GeoSite.dat pre-download; placeholder subscription URLs.

### Not changed (deliberately) / 刻意未改
- `clash-mi-detail.yaml` LAN exposure (`allow-lan`, `0.0.0.0:9090`) — kept as is for now.
- Sniffer — deferred until it can be tested on the router.

## v0.1.0

Baseline: the configuration as of commit `fdb50fe`, before the optimization pass above.
