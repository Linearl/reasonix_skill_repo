"""Email provider auto-configuration database.

30+ email providers with IMAP/SMTP/POP3 configs. Users only need
email address + auth code to auto-configure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class EmailProvider:
    """Configuration for an email service provider."""
    name: str
    domains: list[str]
    imap_server: str
    imap_port: int = 993
    smtp_server: str = ""
    smtp_port: int = 465
    pop3_server: str = ""
    pop3_port: int = 995
    use_ssl: bool = True
    protocol: str = "imap"
    note: str = ""

    def to_config(self, email: str, password: str) -> dict[str, Any]:
        return {
            "EMAIL": email, "PASSWORD": password,
            "PROTOCOL": self.protocol,
            "IMAP_SERVER": self.imap_server, "IMAP_PORT": self.imap_port,
            "POP3_SERVER": self.pop3_server or "", "POP3_PORT": self.pop3_port,
            "SMTP_SERVER": self.smtp_server, "SMTP_PORT": self.smtp_port,
            "USE_SSL": self.use_ssl,
        }


PROVIDERS: list[EmailProvider] = [
    # ── Chinese Mainstream ──
    EmailProvider("QQ邮箱", ["qq.com", "vip.qq.com", "foxmail.com"],
                  "imap.qq.com", 993, "smtp.qq.com", 465, "pop.qq.com", 995,
                  note="需开启IMAP/SMTP并使用授权码（非QQ密码）"),
    EmailProvider("网易163邮箱", ["163.com"],
                  "imap.163.com", 993, "smtp.163.com", 465, "pop.163.com", 995,
                  note="需开启IMAP/SMTP并使用客户端授权密码"),
    EmailProvider("网易126邮箱", ["126.com"],
                  "imap.126.com", 993, "smtp.126.com", 465, "pop.126.com", 995),
    EmailProvider("网易Yeah邮箱", ["yeah.net"],
                  "imap.yeah.net", 993, "smtp.yeah.net", 465, "pop.yeah.net", 995),
    EmailProvider("139邮箱（移动）", ["139.com"],
                  "imap.139.com", 993, "smtp.139.com", 465, "pop.139.com", 995,
                  note="需在139邮箱设置中开启IMAP/SMTP"),
    EmailProvider("189邮箱（电信）", ["189.cn"],
                  "imap.189.cn", 993, "smtp.189.cn", 465, "pop.189.cn", 995,
                  note="需在189邮箱设置中开启IMAP/SMTP"),
    EmailProvider("沃邮箱（联通）", ["wo.cn"],
                  "imap.wo.cn", 993, "smtp.wo.cn", 465, "pop.wo.cn", 995),
    EmailProvider("阿里企业邮箱", ["aliyun.com"],
                  "imap.aliyun.com", 993, "smtp.aliyun.com", 465, "pop.aliyun.com", 995),
    EmailProvider("阿里云企业邮箱（自定义域名）", [],
                  "imap.mxhichina.com", 993, "smtp.mxhichina.com", 465, "pop3.mxhichina.com", 995,
                  note="阿里云企业邮箱（含自定义域名），需在企业邮箱后台开启IMAP/SMTP"),
    EmailProvider("飞书邮箱", ["feishu.cn"],
                  "imap.feishu.cn", 993, "smtp.feishu.cn", 465,
                  note="需在飞书邮箱设置中开启IMAP/SMTP"),
    EmailProvider("新浪邮箱", ["sina.com", "sina.cn"],
                  "imap.sina.com", 993, "smtp.sina.com", 465, "pop.sina.com", 995),
    EmailProvider("搜狐邮箱", ["sohu.com"],
                  "imap.sohu.com", 993, "smtp.sohu.com", 465, "pop.sohu.com", 995),
    EmailProvider("21CN邮箱", ["21cn.com"],
                  "imap.21cn.com", 993, "smtp.21cn.com", 465, "pop.21cn.com", 995),
    # ── Enterprise ──
    EmailProvider("腾讯企业邮箱", [],
                  "imap.exmail.qq.com", 993, "smtp.exmail.qq.com", 465, "pop.exmail.qq.com", 995,
                  note="腾讯企业邮（含自定义域名），需在企业邮箱后台开启IMAP/SMTP"),
    EmailProvider("网易企业邮箱", [],
                  "imap.qiye.163.com", 993, "smtp.qiye.163.com", 465, "pop.qiye.163.com", 995,
                  note="网易企业邮（含自定义域名）"),
    EmailProvider("263企业邮箱", ["263.net"],
                  "imap.263.net", 993, "smtp.263.net", 465, "pop.263.net", 995),
    EmailProvider("新网企业邮箱", [],
                  "imap.xinnet.com", 993, "smtp.xinnet.com", 465),
    EmailProvider("西部数码企业邮箱", [],
                  "imap.west.cn", 993, "smtp.west.cn", 465),
    EmailProvider("中资源企业邮箱", [],
                  "imap.zzy.cn", 993, "smtp.zzy.cn", 465),
    # ── International ──
    EmailProvider("Gmail", ["gmail.com", "googlemail.com"],
                  "imap.gmail.com", 993, "smtp.gmail.com", 465, "pop.gmail.com", 995,
                  note="需开启两步验证并使用应用专用密码（App Password）"),
    EmailProvider("Outlook/Hotmail", ["outlook.com", "hotmail.com", "live.com", "msn.com"],
                  "outlook.office365.com", 993, "smtp.office365.com", 587, "outlook.office365.com", 995),
    EmailProvider("Yahoo邮箱", ["yahoo.com", "yahoo.co.jp", "ymail.com", "rocketmail.com"],
                  "imap.mail.yahoo.com", 993, "smtp.mail.yahoo.com", 465, "pop.mail.yahoo.com", 995,
                  note="需生成应用专用密码"),
    EmailProvider("iCloud", ["icloud.com", "me.com", "mac.com"],
                  "imap.mail.me.com", 993, "smtp.mail.me.com", 587,
                  note="需使用App-Specific Password（非Apple ID密码）"),
    EmailProvider("Proton Mail", ["protonmail.com", "proton.me", "pm.me"],
                  "127.0.0.1", 1143, "127.0.0.1", 1025, use_ssl=False,
                  note="需安装Proton Mail Bridge客户端"),
    EmailProvider("Zoho邮箱", ["zoho.com", "zohomail.com"],
                  "imap.zoho.com", 993, "smtp.zoho.com", 465, "pop.zoho.com", 995),
    EmailProvider("Yandex邮箱", ["yandex.com", "yandex.ru", "ya.ru"],
                  "imap.yandex.com", 993, "smtp.yandex.com", 465, "pop.yandex.com", 995),
    EmailProvider("GMX邮箱", ["gmx.com", "gmx.net", "gmx.de"],
                  "imap.gmx.com", 993, "mail.gmx.com", 587, "pop.gmx.com", 995),
    EmailProvider("Mail.com", ["mail.com", "email.com"],
                  "imap.mail.com", 993, "smtp.mail.com", 587, "pop.mail.com", 995),
    EmailProvider("Apple iCloud（中国）", ["icloud.com.cn"],
                  "imap.mail.me.com", 993, "smtp.mail.me.com", 587),
]

_domain_map: dict[str, EmailProvider] = {}
for p in PROVIDERS:
    for d in p.domains:
        _domain_map[d.lower()] = p


def extract_domain(email: str) -> str:
    m = re.search(r"@(.+)$", email.strip().lower())
    return m.group(1) if m else ""


def find_provider(email: str) -> EmailProvider | None:
    domain = extract_domain(email)
    if not domain:
        return None
    if domain in _domain_map:
        return _domain_map[domain]
    parts = domain.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[i:])
        if parent in _domain_map:
            return _domain_map[parent]
    return None


def auto_configure(email: str, password: str) -> tuple[EmailProvider | None, dict[str, Any]]:
    provider = find_provider(email)
    if provider:
        return provider, provider.to_config(email, password)
    return None, {
        "EMAIL": email, "PASSWORD": password, "PROTOCOL": "imap",
        "IMAP_SERVER": "", "IMAP_PORT": 993, "POP3_SERVER": "", "POP3_PORT": 995,
        "SMTP_SERVER": "", "SMTP_PORT": 465, "USE_SSL": True,
    }


def list_all_providers() -> list[dict[str, Any]]:
    return [{
        "name": p.name,
        "domains": p.domains if p.domains else ["* (custom domain)"],
        "imap": f"{p.imap_server}:{p.imap_port}",
        "smtp": f"{p.smtp_server}:{p.smtp_port}",
        "pop3": f"{p.pop3_server}:{p.pop3_port}" if p.pop3_server else "N/A",
        "note": p.note,
    } for p in PROVIDERS]


def generate_config_text(email: str, password: str, account_num: int = 1) -> str:
    provider, config = auto_configure(email, password)
    lines = [f"# --- Account {account_num} ---"]
    if provider:
        lines.append(f"# Auto-detected: {provider.name}")
        if provider.note:
            lines.append(f"# Note: {provider.note}")
    else:
        lines.append(f"# ⚠️  Unknown provider for {email}")
        lines.append("# Please fill in IMAP/SMTP server details manually.")
    lines.extend([
        f"MAIL_ACCOUNT_{account_num}_PROTOCOL={config['PROTOCOL']}",
        f"MAIL_ACCOUNT_{account_num}_EMAIL={config['EMAIL']}",
        f"MAIL_ACCOUNT_{account_num}_PASSWORD={config['PASSWORD']}",
        f"MAIL_ACCOUNT_{account_num}_IMAP_SERVER={config['IMAP_SERVER']}",
        f"MAIL_ACCOUNT_{account_num}_IMAP_PORT={config['IMAP_PORT']}",
        f"MAIL_ACCOUNT_{account_num}_SMTP_SERVER={config['SMTP_SERVER']}",
        f"MAIL_ACCOUNT_{account_num}_SMTP_PORT={config['SMTP_PORT']}",
    ])
    if config.get("POP3_SERVER"):
        lines.append(f"MAIL_ACCOUNT_{account_num}_POP3_SERVER={config['POP3_SERVER']}")
        lines.append(f"MAIL_ACCOUNT_{account_num}_POP3_PORT={config['POP3_PORT']}")
    lines.append(f"MAIL_ACCOUNT_{account_num}_USE_SSL={'true' if config['USE_SSL'] else 'false'}")
    lines.append("")
    return "\n".join(lines)
