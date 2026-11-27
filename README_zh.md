# Clash Mi Rules

[English](README.md) | 中文文档

为 **Clash Mi / Mihomo (Clash.Meta)** 内核设计的**细化分流配置**。采用主流稳定策略,规则来源全部换成权威上游(meta-rules-dat `.mrs` + blackmatrix7 `.list`),开箱即用。

## 特性

- ✅ **细化分流**:AI / 社交 / 流媒体 / 云 / 游戏 / Crypto 各自独立分组。
- ✅ **稳定的策略**:`url-test` + `fallback`,不使用实验性的 `smart`/LightGBM,任意 Mihomo 内核(含 Clash Mi)都可稳定运行。
- ✅ **自动优选节点**:每个地区组包含 `手动` + `自动(url-test 测速)` + `故转(fallback 故障转移)` 三层。
- ✅ **更新的规则来源**:只用 `metacubex/meta-rules-dat`(`.mrs`)和 `blackmatrix7/ios_rule_script`(`.list`),不依赖个人维护的旧列表。
- ✅ **规则集 URL 由 CI 每晚检查**(带重试与备用镜像)。

## 文件

| 文件 | 说明 |
|------|------|
| `clash-mi-detail.yaml` | 通用配置(手机/电脑等任意 ClashMi/Mihomo 客户端),含校园网认证保护 |
| `openclash.yaml` | **Cudy 日常使用**(不承担校园网出口节点)。基于 `clash-mi-detail.yaml` + 关闭 IPv6 + `router_self_proxy=0` |
| `openclash-backnode.yaml` | **Cudy 校园网出口节点**。即 `openclash.yaml` + 监听 `127.0.0.1:10443` 的 VLESS WebSocket listener(配合 Cloudflare Tunnel) |

### 校园网认证适配(三份均含)

三份配置都将校园网认证 Portal 与联网探测域名排除出代理(最高优先级 `直连` 规则):

- `fake-ip-filter`: `s.scut.edu.cn`、`connect.rom.miui.com`、`+.msftconnecttest.com`、`+.msftncsi.com`
- `rules:` 顶部: `DOMAIN,s.scut.edu.cn`、`IP-CIDR,202.38.210.131/32`、`DOMAIN,connect.rom.miui.com`、`DOMAIN-SUFFIX,msftconnecttest.com`、`DOMAIN-SUFFIX,msftncsi.com` → `直连`

这些 Portal / 联网探测条目(MIUI / MSFT 连通性检测)在任何普通网络环境都安全保留——它们仅把已知探测域名排除出代理,不会破坏正常联网。

Cudy/OpenClash 两版额外将顶层 `ipv6` 与 `dns.ipv6` 设为 `false`,并要求 OpenClash UCI 设 `router_self_proxy=0`,避免路由器本机的 校园网自动登录脚本 和系统流量被透明代理。

#### 可移植原则

三份配置的 DNS 段一律**不写死设备接口**(如 `#apclix0`),可跨手机 / PC / 路由器以及任意 WAN 类型(`eth` / `pppoe` / `wwan` / `usb` / `apcli`)使用,DNS 统一用纯 IP + Mihomo 的 fallback / 分流机制。

#### 静态 DNS · 无 DHCP 递归

三份配置的 DNS 上游一律**静态、明确、无 DHCP 递归**:`nameserver`、`default-nameserver`、`proxy-server-nameserver`、`direct-nameserver` 只使用固定的公网 DNS(`223.5.5.5` + `119.29.29.29`;`clash-mi-detail.yaml` 另以 `tls://1.1.1.1` / `tls://8.8.8.8` 作为 `fallback`)。不要填入 `dhcp://`、`dhcp://apclix0`、`system`、校园网网关 DNS 或任何由 WAN DHCP 动态取得的 DNS——这些会形成 DNS 上游循环,导致 7874 查询堆积、DNS 超时与高 CPU。`respect-rules` 保持不启用。

> **OpenClash 运行时注意**:若源 YAML 已无 `dhcp://apclix0`,但 `/etc/openclash/openclash.yaml` 启动后仍自动出现 `dhcp://"apclix0"`(或其它 WAN DNS),那是 **OpenClash 自身启动阶段自动追加 WAN/DHCP DNS**,不是仓库 YAML 能解决的问题。请在 OpenClash 设置中关闭 “DNS 覆写 / 追加 WAN DNS ”,否则循环会在运行时被重新注入。

#### 校园网 · Cudy 接口绑定说明

本仓库的三份配置**就是** Cudy 校园网本地部署配置(公开仓库版本与 Cudy 本地部署是同一个东西,并非两套)。DNS 上游统一写成纯公网 IP,以保持对路由器实际所用 WAN 类型(`eth` / `pppoe` / `wwan` / `usb` / `apcli`)的可移植性。

当部署在 Cudy 上、且实际校园 WAN 出口确实为 `apclix0` 接口时(例如 4G 模块接校园 Wi-Fi AP),可把 DNS 上游绑定到该接口以强制 DNS 走校园 WAN:

```yaml
# 在任意配置的 dns: 段内
nameserver:
  - '223.5.5.5#apclix0'
  - '119.29.29.29#apclix0'
# 如需要,对 default-nameserver / proxy-server-nameserver / direct-nameserver 同样绑定
```

为避免日后 3~4 份大配置长期漂移,本仓库**不单独维护**第四份完整 `campus.yaml`;接口绑定按需手工套用即可。

> `clash-mi-detail.yaml`(IPv6 开启)的私网直连规则含 IPv6(`::1/128`、`fc00::/7`、`fe80::/10`);两份 OpenClash 全局 IPv6 已关闭,故只保留 IPv4 私网直连。

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

### 通用客户端(Clash Mi / Mihomo)

1. 打开 `clash-mi-detail.yaml`。
2. 在 `proxy-providers` 里,把 `url: "机场订阅地址"` 换成你机场的真实订阅链接,并把 `机场名称` 改成你机场的名字。
3. (可选)如果你介意默认的 `secret`(占位符),改成你自己的强密码。
4. 将该文件作为配置 / 订阅导入 Clash Mi(或其他 Mihomo 客户端)。

### Cudy / OpenClash(校园网出口节点)

1. **日常使用(无出口节点):**导入 `openclash.yaml`。在 OpenClash 设置 `router_self_proxy=0`;两个 `ipv6` 已默认 `false`。
2. **校园网出口节点(Cloudflare Tunnel → VLESS/WS):**导入 `openclash-backnode.yaml`,把 `YOUR_VLESS_UUID_PLACEHOLDER` 换成 XBoard 实际下发给 ClashMi 的真实 UUID,Cloudflare Tunnel 公开域名 `tunnel.freeapp.tech` → HTTP → `127.0.0.1:10443`(路径留空)。客户端节点:VLESS、连接 `tunnel.freeapp.tech:443`、传输 WebSocket、路径 `/`、TLS 开启、SNI/Host `tunnel.freeapp.tech`、Flow 空、Reality 关闭。

## 分组结构

### 业务分流组(31)

- **AI(5)**:ChatGPT / Claude / Gemini / Grok(xAI:grok.com、x.ai)/ 其他AI(Groq、Copilot、Meta AI、Perplexity…)
  - **Claude**:手写官方域名(anthropic.com、claude.ai、claude.com、clau.de、claudemcpclient.com、claudeusercontent.com、CDN 端点、Auth0)、IP 段(160.79.104.0/21、2607:6bc0::/32;不使用 `IP-ASN`,启动无需 ASN 数据库),另加官方 `geosite/anthropic` 规则集(claude.app、claude.dev、ant.dev 等)。可选共享遥测规则(cdn.usefathom.com、sentry.io、intercom、datadog、statsigapi.net)默认保持注释,以免影响其他服务。
  - **Copilot** 用 7 条手写的 Microsoft Copilot 精确规则,不再使用 blackmatrix7 的 `Copilot.list`:该列表混入了 stripe.com、auth0.com、challenges.cloudflare.com、sentry.io、intercom.io 等大量网站共用的服务,以及 DigitalOcean / Vultr 整个 ASN,导致其他网站的付款和验证码从与网页不同的出口 IP 发出。
  - **Meta AI** 只匹配 `meta.ai` / `ai.meta.com`——`geosite/meta` 会连 Facebook / Instagram / WhatsApp 一起吞掉。
- **独立站点(2)**:GitHub / LinuxDo
- **社交(8)**:X / Instagram / Telegram / WhatsApp / Facebook / TikTok / Discord / Reddit
- **流媒体(4)**:Netflix / YouTube / Spotify / Stream Media(Disney、HBO、Prime Video、Crunchyroll、Popcorn…)
- **云与系统(5)**:Google / Microsoft / Apple / Nvidia / Cloud(Adobe…)
- **游戏(1)**:Games(Steam、Epic、EA、Blizzard、UBI、PlayStation、Nintendo…)
- **Crypto(1)**:Crypto(OKX、Bybit、Binance、Kraken、Bybit EU、Ether.fi、Trading 212、Monese、Myfin、Altery…)
- **兜底(5)**:Test / 国外 / 国内 / 其他 / Block

### 地区与策略组

- 全局:`所有-手动` / `所有-自动`
- 每个地区一组 `手动 + 自动 + 故转`:香港 / 台湾 / 日本 / 新加坡 / 韩国 / 美国 / 英国 / 德国 / 其他

## 分流顺序

规则自上而下匹配(命中即停)。在各服务组之前有一段**国内子集**:微软 / 苹果 / Steam / 亚马逊的中国域名(`microsoft@cn`、`apple@cn`、`apple-cn`、`steam@cn`、`amazon@cn`)走 `国内`,Windows / 苹果更新和 Steam 国内 CDN 不消耗代理流量。

兜底漏斗如下:

```
RULE-SET Block  / Domain,Block    # 未被上面服务规则认领的广告 / 追踪域名
RULE-SET Direct / Domain,国内     # 已知直连域名(NAS DDNS、PT 站、需校园网 IP 的学术站)→ 国内
RULE-SET Proxy  / Domain,国外     # 明确要加速的海外域名 → 国外
RULE-SET China  / Domain,国内     # 中国大陆域名 → 国内
RULE-SET China  / IP,国内         # 大陆 IP → 国内
MATCH,其他                        # 其余全部 → 其他
```

`Private / Domain`(localhost、`*.local`、Tailscale `ts.net`、路由器管理页等)放在**最前面**,与私网 IP 段一起始终走 `直连`。

支付 / 登录 / 验证码等共用服务(Stripe、PayPal、Auth0、Cloudflare Turnstile、hCaptcha、Arkose、Intercom)刻意**不归入任何服务组**,走通用路线(`国外` / `其他`),与嵌入它们的网页同一出口。CI 每晚用 `scripts/audit_routes.py` 校验这一点。

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
- `gh-proxy.com` 偶发限流(返回 403),重试或重新加载即可;也可用 `rule-providers` 注释里的 `sed` 命令切到备用镜像。
- 只有 `clash-mi-detail.yaml` 需要 GEO 数据库(GeoIP mmdb,供 `dns.fallback-filter` 使用),经 `geox-url` 走 `gh-proxy.com` 下载,仅在本地缺失时才下载;两份 OpenClash 配置不需要任何 GEO 数据库。`geo-auto-update` 刻意关闭(避免路由器闪存磨损,且 OpenClash 自带更新)。

## 开发运维(CI 与发布)

每次改动配置都会被自动验证,坏改动在合并时就被拦截,而不是等到部署当天才翻车。

### CI(`.github/workflows/ci.yml`)

在每次触及配置/脚本的 `push` / `PR`,以及**每天定时**(UTC 03:17)运行,用于提前发现静默失效的规则镜像源:

| 检查 | 作用 |
|------|------|
| YAML + 一致性 | `scripts/validate.py` —— 解析每个 `*.yaml`,校验必需顶层键、DNS 递归防护(实时配置中不允许 `dhcp://`/`system`/`apclix0`)、可移植性防护(实时代码中不允许写死 `IP#接口`)、rule-provider URL 合法性,以及**三份配置一致性**:两份 OpenClash 配置必须与 `clash-mi-detail.yaml` 逐条规则、逐个策略组一致,只允许已登记的差异(IPv6、DNS fallback、`find-process-mode`、`listeners`) |
| Mihomo 配置测试 | `scripts/mihomo_test.sh` —— 在**副本**上把机场订阅占位符和安全密钥替换后,对每个配置跑 `mihomo -t`。分别用**固定版本**内核(v1.19.34,失败即阻塞)和**最新版**(仅预警,不阻塞)各跑一次 |
| 分流预期 | `scripts/audit_routes.py` —— 下载当前上游列表,按规则顺序模拟匹配,校验 `scripts/route_expectations.txt`(共用支付 / 验证码服务走通用路线、内网直连、各服务进各自的组)。上游列表一旦开始误收共用域名就会报错 |
| 规则 URL 可用性 | `scripts/check_rules.py` —— 并发检查每个 `rule-provider`、`geox-url` 地址及健康探测地址 `gstatic.com/generate_204`,失败会退避重试;只有备用镜像可用时记为警告、不算失败 |

### 发布(`.github/workflows/release.yml`)

打标签即可产出带版本的发布包,方便固定/回滚到某个具体配置版本:

```bash
git tag v0.1.0
git push origin v0.1.0
```

会生成一个 GitHub Release,附带 `clash-mi-rules-<版本>.tar.gz`(三份配置 + README + CHANGELOG + 脚本)和每文件 SHA-256 的 `MANIFEST.txt`。打包前，标签对应的三份配置必须通过离线校验（含 OpenClash 上传文件头）和 `mihomo -t` 内核测试；外部规则镜像可用性单独报告。

### 本地跑校验

```bash
pip install pyyaml
python3 scripts/validate.py          # 离线结构检查
python3 scripts/check_rules.py      # 在线规则 URL 可用性
python3 scripts/audit_routes.py     # 在线分流模拟,对照 route_expectations.txt
bash scripts/mihomo_test.sh --bin ./bin/mihomo   # 需一个 mihomo 二进制
```

## 许可

MIT

---

**免责声明**:本项目仅供个人合法使用,使用者需自行遵守所在地法律法规。
