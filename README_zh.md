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
| `clash-mi-detail.yaml` | 通用配置(手机/电脑等任意 ClashMi/Mihomo 客户端),含华南理工校园网保护 |
| `openclash.yaml` | **Cudy 日常使用**(不承担校园网出口节点)。基于 `clash-mi-detail.yaml` + 关闭 IPv6 + `router_self_proxy=0` |
| `openclash-backnode.yaml` | **Cudy 校园网出口节点**。即 `openclash.yaml` + 监听 `127.0.0.1:10443` 的 VLESS WebSocket listener(配合 Cloudflare Tunnel) |

### 华南理工校园网适配(三份均含)

三份配置都将校园网认证 Portal 与联网探测域名排除出代理(最高优先级 `直连` 规则):

- `fake-ip-filter`: `s.scut.edu.cn`、`connect.rom.miui.com`、`+.msftconnecttest.com`、`+.msftncsi.com`
- `rules:` 顶部: `DOMAIN,s.scut.edu.cn`、`IP-CIDR,202.38.210.131/32`、`DOMAIN,connect.rom.miui.com`、`DOMAIN-SUFFIX,msftconnecttest.com`、`DOMAIN-SUFFIX,msftncsi.com` → `直连`

这些 Portal / 联网探测条目(MIUI / MSFT 连通性检测)在任何普通网络环境都安全保留——它们仅把已知探测域名排除出代理,不会破坏正常联网。

Cudy/OpenClash 两版额外将顶层 `ipv6` 与 `dns.ipv6` 设为 `false`,并要求 OpenClash UCI 设 `router_self_proxy=0`,避免路由器本机的 `scut_portal_login.sh` 和系统流量被透明代理。

#### 可移植原则

三份配置的 DNS 段一律**不写死设备接口**(如 `#apclix0`),可跨手机 / PC / 路由器以及任意 WAN 类型(`eth` / `pppoe` / `wwan` / `usb` / `apcli`)使用,DNS 统一用纯 IP + Mihomo 的 fallback / 分流机制。

#### 静态 DNS · 无 DHCP 递归

三份配置的 DNS 上游一律**静态、明确、无 DHCP 递归**:`nameserver`、`default-nameserver`、`proxy-server-nameserver`、`direct-nameserver` 只使用固定的公网 DNS(`223.5.5.5` + `119.29.29.29`;`clash-mi-detail.yaml` 另以 `tls://1.1.1.1` / `tls://8.8.8.8` 作为 `fallback`)。不要填入 `dhcp://`、`dhcp://apclix0`、`system`、校园网网关 DNS 或任何由 WAN DHCP 动态取得的 DNS——这些会形成 DNS 上游循环,导致 7874 查询堆积、DNS 超时与高 CPU。`respect-rules` 保持不启用。

> **OpenClash 运行时注意**:若源 YAML 已无 `dhcp://apclix0`,但 `/etc/openclash/openclash.yaml` 启动后仍自动出现 `dhcp://"apclix0"`(或其它 WAN DNS),那是 **OpenClash 自身启动阶段自动追加 WAN/DHCP DNS**,不是仓库 YAML 能解决的问题。请在 OpenClash 设置中关闭 “DNS 覆写 / 追加 WAN DNS ”,否则循环会在运行时被重新注入。

#### 华南理工 · Cudy 接口绑定说明

本仓库的三份配置**就是** Cudy / SCUT 本地部署配置(公开仓库版本与 Cudy 本地部署是同一个东西,并非两套)。DNS 上游统一写成纯公网 IP,以保持对路由器实际所用 WAN 类型(`eth` / `pppoe` / `wwan` / `usb` / `apcli`)的可移植性。

当部署在 Cudy 上、且实际校园 WAN 出口确实为 `apclix0` 接口时(例如 4G 模块接校园 Wi-Fi AP),可把 DNS 上游绑定到该接口以强制 DNS 走校园 WAN:

```yaml
# 在任意配置的 dns: 段内
nameserver:
  - '223.5.5.5#apclix0'
  - '119.29.29.29#apclix0'
# 如需要,对 default-nameserver / proxy-server-nameserver / direct-nameserver 同样绑定
```

为避免日后 3~4 份大配置长期漂移,本仓库**不单独维护**第四份完整 `scut-campus.yaml`;接口绑定按需手工套用即可。

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

## 开发运维(CI 与发布)

每次改动配置都会被自动验证,坏改动在合并时就被拦截,而不是等到部署当天才翻车。

### CI(`.github/workflows/ci.yml`)

在每次触及配置/脚本的 `push` / `PR`,以及**每天定时**(UTC 03:17)运行,用于提前发现静默失效的规则镜像源:

| 检查 | 作用 |
|------|------|
| YAML + 一致性 | `scripts/validate.py` —— 解析每个 `*.yaml`,校验必需顶层键、DNS 递归防护(实时配置中不允许 `dhcp://`/`system`/`apclix0`)、可移植性防护(实时代码中不允许写死 `IP#接口`)、rule-provider URL 合法性 |
| Mihomo 配置测试 | `scripts/mihomo_test.sh` —— 拉取官方 `mihomo` 二进制,在**副本**上把机场订阅占位符和安全密钥替换后,对每个配置跑 `mihomo -t` |
| 规则 URL 可用性 | `scripts/check_rules.py` —— 并发 HEAD/GET 每个 `rule-provider` URL 及健康探测地址 `gstatic.com/generate_204` |

### 发布(`.github/workflows/release.yml`)

打标签即可产出带版本的发布包,方便固定/回滚到某个具体配置版本:

```bash
git tag v0.1.0
git push origin v0.1.0
```

会生成一个 GitHub Release,附带 `clash-mi-rules-<版本>.tar.gz`(三份配置 + README + 脚本)和每文件 SHA-256 的 `MANIFEST.txt`。每个发布都先过一遍 CI 校验门槛。

### 本地跑校验

```bash
pip install pyyaml
python3 scripts/validate.py          # 离线结构检查
python3 scripts/check_rules.py      # 在线规则 URL 可用性
bash scripts/mihomo_test.sh --bin ./bin/mihomo   # 需一个 mihomo 二进制
```

## 许可

MIT

---

**免责声明**:本项目仅供个人合法使用,使用者需自行遵守所在地法律法规。
