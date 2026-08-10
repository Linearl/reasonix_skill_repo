---
name: reasonix-remote-linux-setup
description: 在 Linux 远程主机（含绿联 NAS）上安装/配置 reasonix serve，并打通 Windows 桌面版远程连接（含全部已知坑）
---

# Reasonix Linux 远程主机部署与桌面版远程连接

在 Linux 远程主机（含绿联 NAS 等容器化/魔改系统）上安装配置 reasonix，并通过 web 端 / Windows 桌面版远程查看使用。基于 2026-08 绿联 DX4600PRO（Debian 12, x86_64）实战验证。

## 1. 安装二进制

```bash
# 下载官方 Linux 包（GitHub release: esengine/DeepSeek-Reasonix）
# 国内网络：本机走代理下载后 scp 上传，或远程 curl 走 gh-proxy.com 镜像
# https://gh-proxy.com/https://github.com/esengine/DeepSeek-Reasonix/releases/download/<tag>/Reasonix-linux-amd64.tar.gz
mkdir -p ~/reasonix && cd ~/reasonix
tar -xzf Reasonix-linux-amd64.tar.gz   # 解出 reasonix / reasonix-desktop 等
chmod +x reasonix
./reasonix version
```

**⚠️ 必须加入 PATH**：桌面版 remote bootstrap 用 `command -v reasonix` 检测远程是否已装，检测不到就尝试下载（直连 GitHub 易失败）→ 连接报「无法连接」。
```bash
sudo ln -s ~/reasonix/reasonix /usr/local/bin/reasonix
# 验证：command -v reasonix && reasonix serve --help | grep port-file  # 需支持 --port-file
```

## 2. 配置（~/.reasonix/）

- `~/.reasonix/config.toml`：`default_model` + `[[providers]]`（name/kind/base_url/models/api_key_env）+ `[serve]` 段
- `~/.reasonix/.env`：API key（`chmod 600`）；provider 只存 env 变量名，密钥在 .env
- **无 bubblewrap 的容器系统必须 `[sandbox] bash = "off"`**，否则 v1.16+ 拒绝执行 shell 命令（绿联 NAS 无 bwrap）
- serve 认证（公网暴露必须）：
  ```bash
  ./reasonix serve --hash-password --password '密码'   # 生成 bcrypt hash
  # config.toml:
  # [serve]
  # auth_mode = "password"
  # password_hash = "$2a$12$..."
  ```

## 3. 启动 serve（常驻）

```bash
cd ~/reasonix
setsid nohup ./reasonix serve --addr 0.0.0.0:8787 > ~/reasonix/serve.log 2>&1 < /dev/null &
```
验证：`curl http://IP:8787/login` 得登录页；POST `password=` 得 302；`/sessions` 得会话列表。
重启用 `kill -9 $(pgrep -f '^\./reasonix serve')` 再启（注意 pkill 模式别匹配到自身 shell）。

## 4. 关键坑（务必读）

1. **serve 的 /reload 会导致会话目录分裂**：启动时 SessionDir = cwd 映射的项目目录（`~/.reasonix/projects/<cwd-slug>/sessions`）；`/reload` 重建 controller 时回落为全局目录（`~/.reasonix/sessions`，可能不存在）→ `/sessions` 返回空、左侧列表空白。**修复**：
   ```bash
   ln -s ~/.reasonix/projects/<cwd-slug>/sessions ~/.reasonix/sessions
   ```
   （符号链接统一两个路径；之后避免用 web 端 /reload，装技能直接重启 serve）
2. 会话列表只显示**已落盘**的会话（每个 turn 完成后才写盘），进行中的对话刷新后不出现属正常
3. 技能/命令装完后，常驻 serve 不会热加载 → **重启 serve**（或 /reload，注意坑 1）

## 5. 用户级技能/命令安装

```bash
mkdir -p ~/.reasonix/skills ~/.claude/skills ~/.claude/commands
cp -rn skills/. ~/.reasonix/skills/       # Reasonix 用户级技能
cp -rn claude-skills/. ~/.claude/skills/  # convention root 技能
cp -rn commands/. ~/.claude/commands/     # slash 命令
# hooks: ~/.reasonix/settings.json（注意不要拷含 Windows 路径的 hooks）
```
验证：`reasonix doctor` 有技能警告即已扫描；`reasonix run -p "列出技能"` 可确认。

## 6. Windows 桌面版远程连接（v1.19.5+）

本机 `%APPDATA%\reasonix\config.toml` 加：
```toml
[remote]
[[remote.hosts]]
name          = "nas"
host          = "100.99.99.99"          # 或公网 IP
user          = "yjc121"
identity_file = "C:/Users/<user>/.ssh/id_ed25519_nas"   # ⚠️ 必须无口令专用密钥
password_env  = "NAS_SSH_PASSWORD"      # .env 里存 SSH 密码
workspace     = "/home/yjc121/reasonix"
serve_install = "auto"
```
`.env` 加 `NAS_SSH_PASSWORD=<密码>`。

**认证顺序（重要）**：桌面版会先试公钥（服务器拒绝后）自动回落密码。
- 有口令的私钥会弹口令框且认证卡死 → **生成无口令专用密钥**：`ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519_nas`
- 绿联等魔改 sshd 拒绝公钥（uid not match）是正常的，回落密码即成功
- UI 连接弹窗输入密码 → 连接 → 远程窗口（serve web）→ 登录页用 [serve] 的 password

## 7. 绿联 NAS（UGOS）特有坑

- **sshd 魔改**（pam_ug_login + ACL 检查）：公钥认证不可用（`uid not match. uid:1000, acl e_id:1001`），StrictModes no / AuthorizedKeysFile 绝对路径都绕不过；只能密码认证（绿联用户库，/etc/shadow 无记录）
- **SFTP 子系统 chroot 虚拟视图**：SFTP 看不到真实 `/home/<user>`，文件传输用 shell/scp 而非 SFTP
- **apt 状态混乱**（大量 unmet dependencies：exiv2/picom/vim 等）：不要 `apt --fix-broken install`；装包用 `dpkg -x` 手动解包到 /usr/local 或直接下载静态二进制
- Tailscale 若跑在容器里，SSH 来源显示 127.0.0.1（正常现象）
- home 目录 777 是系统设计（SMB 共享），不要 chmod 收紧
- 绿联升级可能重置 /usr/local/bin 软链和 apt 装的包，需重新检查

## 验证清单

```bash
# 远程
reasonix version && reasonix doctor
curl -k https://<域名>/login            # 200 登录页
# 本机
reasonix doctor --json | grep -c remote # 配置解析正常
# 桌面版：右上角「远程」→ 主机 → 连接 → 远程窗口登录
```

## 8. 绿联 NAS 根治方案：独立标准 sshd（桌面版远程窗口打通）

绿联魔改 sshd **和** `/usr/sbin/sftp-server` 都实现虚拟文件系统视图（SFTP `realpath("~")`→`/~`、cwd=`/`、真实 home 不可见）→ reasonix 桌面版 bootstrap（SFTP 写 `~/.reasonix/remote/`）必然失败，「打开远程网页」无反应。**根治：跑一个独立的 Debian 标准 sshd，完全不动绿联 22 端口**：

```bash
# 1. 下载标准版 deb 并解包（绿联 apt 损坏，勿用 apt install）
curl -sL -o /tmp/oss.deb "https://deb.debian.org/debian/pool/main/o/openssh/openssh-server_9.2p1-2+deb12u10_amd64.deb"
curl -sL -o /tmp/sftp.deb "https://deb.debian.org/debian/pool/main/o/openssh/openssh-sftp-server_9.2p1-2+deb12u10_amd64.deb"
dpkg -x /tmp/oss.deb /tmp/oss-pkg && dpkg -x /tmp/sftp.deb /tmp/sftp-pkg
sudo cp /tmp/oss-pkg/usr/sbin/sshd /usr/local/openssh/sshd
sudo cp /tmp/sftp-pkg/usr/lib/openssh/sftp-server /usr/local/openssh/sftp-server
# 2. 独立配置 /usr/local/openssh/sshd_config（root 写，600）：
#    Port 2222 / ListenAddress 0.0.0.0 / HostKey /usr/local/openssh/host_keys/ssh_host_ed25519_key
#    PubkeyAuthentication yes / PasswordAuthentication no / UsePAM no / AllowUsers yjc121
#    Subsystem sftp /usr/local/openssh/sftp-server
# 3. host key：sudo ssh-keygen -t ed25519 -N "" -f /usr/local/openssh/host_keys/ssh_host_ed25519_key
# 4. 启动（日志必须放用户可写目录！/usr/local 下重定向会 Permission denied）：
sudo setsid nohup /usr/local/openssh/sshd -f /usr/local/openssh/sshd_config > ~/reasonix/sshd2222.log 2>&1 &
# 5. 桌面版 host 配置：port = 2222 + identity_file = 无口令专用密钥（ssh-keygen -N "" -f ~/.ssh/id_ed25519_nas）+ 公钥加入远程 authorized_keys
```

验证 SFTP 真实视图：paramiko `sftp.normalize('.')` 应返回 `/home/<user>`（魔改版返回 `/`）。桌面版重连后远程窗口自动打开（界面与本地一致，左侧显示远程会话）。

**运维注意**：NAS 重启后需重跑启动命令；绿联升级可能清 `/usr/local/openssh`（重跑即可）；回滚 = `sudo pkill -f 'openssh/sshd -[f]'` + 删目录。

## 9. 远程形态（重要认知）与 CLI 调用

- **官方远程形态**：自 1.20.0 起，桌面版的"同窗口远程投影"（same-window remote projection / Remote Workbench / Provider Broker）已被官方**有意移除**（原因：跨平台稳定性差、Provider Broker 会把本机 API key 暴露给远程、维护成本高、统一到 CLI/Serve 模型）。远程 = **独立子进程窗口（serve web UI）**，这是官方唯一形态，不要期待主窗口内嵌远程会话。
- **CLI 直接调用远程 reasonix**（headless 任务）：
  ```bash
  # 22 端口（绿联魔改 sshd，密码）或 2222（标准 sshd，密钥）
  ssh -i ~/.ssh/id_ed25519_nas -p 2222 yjc121@<host> \
    'cd ~/reasonix && ./reasonix run -p "任务描述" --model deepseek/deepseek-v4-flash'
  ```
  任务会话写入远程 `~/.reasonix/projects/<cwd-slug>/sessions/`，桌面版远程窗口/公网 web 端立即可见。注意远程命令输出含中文时用 `PYTHONIOENCODING=utf-8` 或 `2>&1 | head`。

## 10. 远程 reasonix 走代理（v2rayA 等）

NAS 无法直连国外站时，让 reasonix 走本地代理（容器端口映射）：

```toml
# ~/.reasonix/config.toml —— 注意！proxy_mode/proxy_url 必须放 [network] 段
# 放 [network.proxy] 子表（type/server/port 结构）会被静默忽略，doctor 显示 auto、实际直连！
[network]
proxy_mode = "custom"
proxy_url = "http://127.0.0.1:38419"        # 代理端口（v2rayA 20171→host 38419 示例）
no_proxy = "localhost,127.0.0.1,.local,100.99.99.99,192.168.0.0/16"
```

要点：
- 验证配置生效：`reasonix doctor --json` 应显示 `"proxy_mode": "custom" | "proxy": "custom (http://...)"`（显示 auto = 配置没被读到）
- 验证实际走代理：`reasonix run -p "用 web_fetch 访问 https://api.ipify.org 报告结果"` → 应返回国外出口 IP
- 改配置后**重启 serve**；桌面版远程窗口的 bootstrap serve 需**断开重连**才用新配置
- google.com 慢/超时通常是代理节点问题（curl 对照测试：`curl -x http://127.0.0.1:<port> -L https://www.google.com`），去代理面板换节点
- 替代方式：进程环境变量 `HTTPS_PROXY=http://127.0.0.1:<port>`（proxy_mode=auto 时读 env）
