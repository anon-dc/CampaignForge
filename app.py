"""
CampaignForge v3.0 — Professional Email & SMS Campaign Platform
Upgraded with: SMTP killing, spoofing, advanced testing, spam scoring, SSL/TLS/NONE support
Dynamic port configuration support
"""

import os, re, csv, json, time, uuid, threading, smtplib, ssl, logging, base64, requests, socket
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template, request, jsonify, send_file, Response, redirect
from flask_cors import CORS
import io
import socket

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

Path("uploads").mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)

# ─── PORT CONFIGURATION ─────────────────────────────────────
# Change this value to change the port throughout the application
APP_PORT = 5000  # ← CHANGE THIS VALUE TO CHANGE THE PORT

# 1x1 transparent GIF tracking pixel
TRACKING_PIXEL = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
    b'\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00'
    b'\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
)

# ─────────────────────────────────────────────
# CARRIER GATEWAYS
# ─────────────────────────────────────────────
CARRIER_GATEWAYS = {
    "USA": {
        "AT&T": "txt.att.net",
        "T-Mobile": "tmomail.net",
        "Verizon": "vtext.com",
        "Sprint": "messaging.sprintpcs.com",
        "Google Fi": "msg.fi.google.com",
        "US Cellular": "email.uscc.net",
        "Cricket": "sms.cricketwireless.net",
        "MetroPCS": "mymetropcs.com",
        "Boost Mobile": "sms.myboostmobile.com",
        "Consumer Cellular": "mailmymobile.net",
        "Simple Mobile": "smtext.com",
        "Tracfone": "mmst5.tracfone.com",
        "Xfinity Mobile": "vtext.com",
        "C-Spire": "cspire1.com",
        "Virgin Mobile": "vmobl.com",
        "Republic Wireless": "text.republicwireless.com"
    },
    "Canada": {
        "Bell": "txt.bell.ca",
        "Rogers": "pcs.rogers.com",
        "Telus": "msg.telus.com",
        "Fido": "fido.ca",
        "Koodo": "msg.koodomobile.com",
        "Freedom Mobile": "txt.freedommobile.ca",
        "Virgin Mobile": "vmobile.ca",
        "SaskTel": "sms.sasktel.com",
        "MTS": "text.mtsmobility.com"
    },
    "Australia": {
        "Telstra": "sms.telstra.com.au",
        "Optus": "optusmobile.com.au",
        "Vodafone": "voda.com.au",
        "Boost": "sms.boost.com.au",
        "Amaysim": "amaysim.com.au",
        "TPG": "tpg.com.au"
    },
    "UK": {
        "EE": "mms.ee.co.uk",
        "O2": "o2imail.co.uk",
        "Vodafone UK": "vodafone.net",
        "Three": "three.co.uk",
        "Virgin Mobile": "vxtras.com",
        "Giffgaff": "giffgaff.com"
    }
}

ESP_WHITELIST_INFO = {
    "SendGrid":    {"ips": ["167.89.0.0/17", "198.21.0.0/16", "208.117.48.0/20"],
                   "docs": "https://docs.sendgrid.com/ui/account-and-settings/ip-addresses"},
    "Mailgun":     {"ips": ["69.72.32.0/19", "192.161.136.0/21"],
                   "docs": "https://documentation.mailgun.com/en/latest/user_manual.html"},
    "Amazon SES":  {"ips": ["54.240.0.0/18", "199.255.192.0/18"],
                   "docs": "https://docs.aws.amazon.com/ses/latest/dg/dedicated-ip.html"},
    "Postmark":    {"ips": ["50.31.156.6", "50.31.156.148"],
                   "docs": "https://postmarkapp.com/developer/user-guide/sending-email/whitelist"},
    "Custom SMTP": {"ips": ["Your dedicated server IP"],
                   "docs": "Contact your hosting provider for dedicated IP options"},
}

# ─────────────────────────────────────────────
# SPAM TRIGGER WORDS (for scoring)
# ─────────────────────────────────────────────
SPAM_TRIGGERS = [
    "free", "winner", "cash", "bonus", "click here", "act now", "limited time",
    "urgent", "guaranteed", "earn money", "viagra", "lottery", "investment",
    "unsubscribe", "opt out", "@", "!!!", "$$$", "credit", "loan", "mortgage",
    "refinance", "debt", "consolidation", "insurance", "medication", "pharmacy"
]

class SpamScoreCalculator:
    """Calculate spam score for email content"""
    
    @staticmethod
    def calculate_score(subject: str, body: str, is_html: bool = False) -> dict:
        score = 0
        warnings = []
        
        if len(subject) > 50:
            score += 5
            warnings.append("Subject line > 50 characters")
        if subject.isupper():
            score += 15
            warnings.append("Subject line in ALL CAPS")
        if subject.endswith("!!!"):
            score += 10
            warnings.append("Subject ends with multiple exclamation marks")
        
        body_lower = body.lower()
        found_triggers = []
        for trigger in SPAM_TRIGGERS:
            if trigger.lower() in body_lower:
                found_triggers.append(trigger)
                score += 3
        
        if found_triggers:
            warnings.append(f"Spam trigger words found: {', '.join(found_triggers[:5])}")
        
        if body.count("!") > 5:
            score += 8
            warnings.append("Excessive exclamation marks")
        
        if is_html:
            link_count = len(re.findall(r'href=["\']', body))
            text_length = len(re.sub(r'<[^>]+>', '', body))
            if text_length > 0 and link_count / text_length > 0.01:
                score += 5
                warnings.append("High link-to-text ratio")
        
        if is_html and not re.search(r'[a-zA-Z0-9]{20,}', body):
            score += 10
            warnings.append("Little text content, mostly images")
        
        if is_html:
            if '</body>' not in body.lower():
                score += 3
                warnings.append("Missing </body> tag")
            if '</html>' not in body.lower():
                score += 2
                warnings.append("Missing </html> tag")
        
        if score <= 10:
            grade = "Excellent"
            color = "green"
        elif score <= 25:
            grade = "Good"
            color = "amber"
        elif score <= 45:
            grade = "Warning"
            color = "orange"
        else:
            grade = "Poor - May go to spam"
            color = "red"
        
        return {
            "score": score,
            "max_score": 100,
            "grade": grade,
            "color": color,
            "warnings": warnings,
            "found_triggers": found_triggers[:10]
        }

# ─────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────
@dataclass
class SMTPConfig:
    server: str
    port: int
    email: str
    password: str
    label: str = ""
    spoof_email: str = ""
    use_spoof: bool = False
    security: str = "TLS"
    health: float = 1.0
    sent_count: int = 0
    fail_count: int = 0
    last_used: float = 0.0
    test_status: str = "untested"
    test_message: str = ""
    test_send_id: str = ""
    test_spam_score: int = 0
    is_dead: bool = False
    last_tested_at: str = ""

@dataclass
class TrackingEvent:
    id: str
    smtp_email: str
    smtp_server: str
    sent_to: str
    sent_at: str
    event_type: str = "campaign"
    opened: bool = False
    opened_at: str = ""
    clicked: bool = False
    clicked_at: str = ""
    click_url: str = ""
    spam_score: int = 0

@dataclass
class Recipient:
    address: str
    name: str = ""
    tags: Dict = field(default_factory=dict)
    subscribed: bool = True
    channel: str = "email"
    carrier: str = ""

@dataclass
class SendResult:
    recipient: str
    success: bool
    error: str = ""
    timestamp: str = ""
    smtp_used: str = ""
    duration_ms: int = 0
    tracking_id: str = ""

@dataclass
class Campaign:
    id: str
    name: str
    subject: str
    body: str
    is_html: bool
    channel: str
    status: str = "draft"
    created_at: str = ""
    results: List[SendResult] = field(default_factory=list)
    sent: int = 0
    failed: int = 0
    total: int = 0
    progress: float = 0.0
    opens: int = 0
    clicks: int = 0
    attachments: List[Dict] = field(default_factory=list)

# ─────────────────────────────────────────────
# SMTP CONNECTION HELPER
# ─────────────────────────────────────────────
def create_smtp_connection(server: str, port: int, security: str = "TLS", timeout: int = 20):
    """Create SMTP connection with specified security type"""
    if security == "SSL":
        context = ssl.create_default_context()
        connection = smtplib.SMTP_SSL(server, port, timeout=timeout, context=context)
    elif security == "TLS":
        connection = smtplib.SMTP(server, port, timeout=timeout)
        connection.ehlo()
        connection.starttls(context=ssl.create_default_context())
        connection.ehlo()
    else:  # NONE
        connection = smtplib.SMTP(server, port, timeout=timeout)
        connection.ehlo()
    return connection

# ─────────────────────────────────────────────
# ENGINE (Upgraded)
# ─────────────────────────────────────────────
class CampaignEngine:
    def __init__(self):
        self.smtp_configs: List[SMTPConfig] = []
        self.recipients: List[Recipient] = []
        self.campaigns: Dict[str, Campaign] = {}
        self.tracking_events: Dict[str, TrackingEvent] = {}
        self.active_campaign_id: Optional[str] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self.test_queue: List[dict] = []
        self.test_in_progress = False

        # Send settings
        self.concurrency = 3
        self.delay_between = 0.5
        self.max_retries = 2
        self.timeout = 20
        self.daily_limit = 0

        # Identity / compliance
        self.from_name = ""
        self.from_address = ""
        self.reply_to = ""
        self.physical_address = ""
        self.unsubscribe_footer = True

        # Test & tracking
        self.test_recipient = ""
        self.test_recipient_name = ""
        self.tracking_base_url = ""
        self.auto_test_on_upload = True

        # Whitelist
        self.whitelist_mode = False
        self.whitelist_esp = "Custom SMTP"

        # Spoof settings
        self.enable_spoofing = False

        # Session stats
        self.session_sent = 0
        self.session_failed = 0

    def load_smtp(self, lines: List[str]) -> int:
        """Parse SMTP lines with support for multiple formats"""
        valid = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            
            if len(parts) >= 3:
                try:
                    server = parts[0].strip()
                    port = int(parts[1].strip())
                    email = parts[2].strip()
                    
                    password = ""
                    label = ""
                    spoof_email = ""
                    security = "TLS"
                    
                    if len(parts) >= 4:
                        password = parts[3].strip()
                    
                    if len(parts) >= 5 and parts[4].strip():
                        label = parts[4].strip()
                    else:
                        label = email.split('@')[0] if '@' in email else email
                    
                    if len(parts) >= 6 and parts[5].strip():
                        spoof_email = parts[5].strip()
                    
                    if len(parts) >= 7 and parts[6].strip().upper() in ["TLS", "SSL", "NONE"]:
                        security = parts[6].strip().upper()
                    
                    if security == "TLS" and port == 465:
                        security = "SSL"
                    elif security == "TLS" and port == 25:
                        security = "NONE"
                    
                    cfg = SMTPConfig(
                        server=server,
                        port=port,
                        email=email,
                        password=password,
                        label=label,
                        spoof_email=spoof_email,
                        security=security
                    )
                    valid.append(cfg)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse SMTP line: {line} - {e}")
                    continue
        
        self.smtp_configs = valid
        return len(valid)

    def get_from_address(self, cfg: SMTPConfig) -> str:
        """Get the from address - priority: global from_address > spoof_email > email"""
        if self.from_address:
            return self.from_address
        if cfg.use_spoof and cfg.spoof_email:
            return cfg.spoof_email
        return cfg.email

    def test_connection(self, index: int) -> Tuple[bool, str]:
        if index >= len(self.smtp_configs):
            return False, "Index out of range"
        cfg = self.smtp_configs[index]
        cfg.test_status = "testing"
        cfg.last_tested_at = datetime.now().isoformat()
        
        try:
            conn = create_smtp_connection(cfg.server, cfg.port, cfg.security, self.timeout)
            if cfg.email and cfg.password:
                conn.login(cfg.email, cfg.password)
            conn.quit()
            
            cfg.test_status = "pass"
            cfg.test_message = f"Connected — {cfg.server}:{cfg.port} [{cfg.security}]"
            cfg.is_dead = False
            cfg.health = min(1.0, cfg.health + 0.2)
            return True, cfg.test_message
            
        except smtplib.SMTPAuthenticationError:
            cfg.test_status = "fail"
            cfg.test_message = "Authentication failed - check email/password"
            cfg.health = 0.0
            cfg.is_dead = True
            return False, cfg.test_message
        except socket.timeout:
            cfg.test_status = "fail"
            cfg.test_message = f"Connection timeout after {self.timeout}s"
            cfg.health = max(0.0, cfg.health - 0.3)
            cfg.is_dead = True
            return False, cfg.test_message
        except Exception as e:
            error_msg = str(e)[:100]
            cfg.test_status = "fail"
            cfg.test_message = error_msg
            cfg.health = max(0.0, cfg.health - 0.3)
            
            auto_result = self._auto_detect_security(cfg)
            if auto_result:
                cfg.security = auto_result
                cfg.test_message += f" → Auto-detected as {auto_result}"
                try:
                    conn = create_smtp_connection(cfg.server, cfg.port, auto_result, self.timeout)
                    if cfg.email and cfg.password:
                        conn.login(cfg.email, cfg.password)
                    conn.quit()
                    cfg.test_status = "pass"
                    cfg.test_message = f"Connected with auto-detected {auto_result}"
                    cfg.is_dead = False
                    cfg.health = min(1.0, cfg.health + 0.3)
                    return True, cfg.test_message
                except Exception:
                    pass
            
            return False, cfg.test_message

    def _auto_detect_security(self, cfg: SMTPConfig) -> Optional[str]:
        security_types = ["TLS", "SSL", "NONE"]
        for sec in security_types:
            if sec == cfg.security:
                continue
            try:
                conn = create_smtp_connection(cfg.server, cfg.port, sec, 5)
                if cfg.email and cfg.password:
                    conn.login(cfg.email, cfg.password)
                conn.quit()
                return sec
            except Exception:
                continue
        return None

    def send_test_email(self, index: int, recipient: str, recipient_name: str = "",
                        base_url: str = "", test_type: str = "full") -> Tuple[bool, str, str, dict]:
        if not recipient:
            return False, "No test recipient set.", "", {}
        if index >= len(self.smtp_configs):
            return False, "SMTP index out of range", "", {}

        cfg = self.smtp_configs[index]
        from_addr = self.get_from_address(cfg)
        tid = uuid.uuid4().hex
        pixel_url = f"{base_url}/track/open/{tid}"
        click_url = f"{base_url}/track/click/{tid}?url={base64.urlsafe_b64encode(b'https://example.com').decode().rstrip('=')}"

        test_html, test_plain = self._build_test_email_content(
            cfg, tid, pixel_url, click_url, recipient_name or recipient.split("@")[0]
        )

        spam_score_result = {}
        
        try:
            conn = create_smtp_connection(cfg.server, cfg.port, cfg.security, self.timeout)
            if cfg.email and cfg.password:
                conn.login(cfg.email, cfg.password)
            
            msg = MIMEMultipart("alternative")
            display_name = self.from_name if self.from_name else "CampaignForge"
            msg["From"] = f"{display_name} <{from_addr}>"
            msg["To"] = f"{recipient_name} <{recipient}>" if recipient_name else recipient
            msg["Subject"] = f"[SMTP Test] {cfg.server} - {datetime.now().strftime('%H:%M')}"
            msg["X-Mailer"] = "CampaignForge v3.0"
            msg["X-CF-Test-ID"] = tid
            msg["X-Spoofed"] = "true" if cfg.use_spoof and cfg.spoof_email else "false"
            msg["X-Security"] = cfg.security
            
            msg.attach(MIMEText(test_plain, "plain", "utf-8"))
            msg.attach(MIMEText(test_html, "html", "utf-8"))
            
            conn.send_message(msg)
            conn.quit()

            spam_score_result = SpamScoreCalculator.calculate_score(
                msg["Subject"], test_html, is_html=True
            )
            cfg.test_spam_score = spam_score_result["score"]
            
            evt = TrackingEvent(
                id=tid, smtp_email=cfg.email, smtp_server=cfg.server,
                sent_to=recipient, sent_at=datetime.now().isoformat(),
                event_type="test", spam_score=spam_score_result["score"]
            )
            with self._lock:
                self.tracking_events[tid] = evt
                cfg.test_send_id = tid
                cfg.test_status = "pass"
                cfg.test_message = f"Test sent to {recipient} [{cfg.security}]"
                cfg.is_dead = False
                cfg.health = min(1.0, cfg.health + 0.1)

            return True, f"Test sent to {recipient}", tid, spam_score_result

        except smtplib.SMTPAuthenticationError as e:
            cfg.test_status = "fail"
            cfg.test_message = f"Auth failed: {str(e)[:80]}"
            cfg.is_dead = True
            cfg.health = 0.0
            return False, cfg.test_message, "", {}
        except Exception as e:
            cfg.test_status = "fail"
            cfg.test_message = str(e)[:100]
            cfg.is_dead = True if "authentication" in str(e).lower() else cfg.is_dead
            cfg.health = max(0.0, cfg.health - 0.3)
            return False, str(e)[:120], "", {}

    def _build_test_email_content(self, cfg: SMTPConfig, tid: str, pixel_url: str, 
                                   click_url: str, recipient_name: str) -> Tuple[str, str]:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if self.from_address:
            spoof_note = f"CUSTOM FROM: {self.from_address}"
            from_display = self.from_address
        elif cfg.use_spoof and cfg.spoof_email:
            spoof_note = "SPOOF MODE ACTIVE"
            from_display = cfg.spoof_email
        else:
            spoof_note = "Standard Mode"
            from_display = cfg.email
        
        security_badge = {
            "TLS": "TLS (STARTTLS)",
            "SSL": "SSL/TLS (SMTPS)",
            "NONE": "No Encryption"
        }.get(cfg.security, f"{cfg.security}")
        
        base_url = self.tracking_base_url or f"http://localhost:{APP_PORT}"
        
        tracking_url = f"{base_url}/tracking.html"
        
        click_tracking_url = (
            f"{tracking_url}?type=click"
            f"&tid={tid}"
            f"&url={click_url}"
            f"&campaign=test"
            f"&recipient={recipient_name}"
        )
        
        pixel_tracking_url = (
            f"{tracking_url}?mode=pixel"
            f"&tid={tid}"
            f"&type=open"
            f"&campaign=test"
            f"&recipient={recipient_name}"
        )
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMTP Test Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            padding: 20px;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .container {{
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .card {{
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 16px;
        }}
        
        .header {{
            background: #1a1a2e;
            padding: 24px 20px;
            color: #ffffff;
        }}
        
        .header h2 {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 6px;
        }}
        
        .header p {{
            font-size: 13px;
            opacity: 0.8;
            margin: 0;
        }}
        
        .content {{
            padding: 24px 20px;
        }}
        
        .info-row {{
            display: flex;
            flex-wrap: wrap;
            padding: 10px 0;
            border-bottom: 1px solid #eaeef2;
        }}
        
        .info-row:last-child {{
            border-bottom: none;
        }}
        
        .info-label {{
            font-weight: 600;
            width: 120px;
            color: #4a5568;
            flex-shrink: 0;
        }}
        
        .info-value {{
            color: #2d3748;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            word-break: break-all;
            flex: 1;
        }}
        
        .security-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            color: #10b981;
            background: rgba(16, 185, 129, 0.1);
        }}
        
        .security-badge.tls {{
            color: #10b981;
            background: rgba(16, 185, 129, 0.1);
        }}
        
        .security-badge.ssl {{
            color: #10b981;
            background: rgba(16, 185, 129, 0.1);
        }}
        
        .security-badge.none {{
            color: #f59e0b;
            background: rgba(245, 158, 11, 0.1);
        }}
        
        .deliverability-box {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 16px;
            margin: 20px 0;
        }}
        
        .deliverability-box h3 {{
            font-size: 14px;
            margin-bottom: 10px;
            color: #1a202c;
        }}
        
        .deliverability-box ul {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        
        .deliverability-box li {{
            font-size: 13px;
            color: #4a5568;
            padding: 3px 0;
        }}
        
        .deliverability-box li strong {{
            color: #1a202c;
        }}
        
        .btn {{
            display: inline-block;
            background: #2d3748;
            color: #ffffff;
            padding: 10px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            margin-top: 16px;
        }}
        
        .btn:hover {{
            background: #1a202c;
        }}
        
        .btn-primary {{
            background: #4f8ef7;
        }}
        
        .btn-primary:hover {{
            background: #3b7de4;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 16px 20px;
            text-align: center;
            font-size: 11px;
            color: #a0aec0;
            border-top: 1px solid #eaeef2;
        }}
        
        .footer p {{
            margin: 2px 0;
        }}
        
        .tracking-url {{
            background: #f1f5f9;
            border-radius: 6px;
            padding: 8px 12px;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            word-break: break-all;
            color: #1e293b;
            margin: 4px 0;
        }}
        
        /* Responsive */
        @media screen and (max-width: 480px) {{
            body {{
                padding: 10px;
            }}
            
            .header {{
                padding: 16px;
            }}
            
            .header h2 {{
                font-size: 17px;
            }}
            
            .content {{
                padding: 16px;
            }}
            
            .info-row {{
                flex-direction: column;
                padding: 8px 0;
            }}
            
            .info-label {{
                width: 100%;
                font-size: 12px;
                margin-bottom: 2px;
            }}
            
            .info-value {{
                font-size: 12px;
            }}
            
            .deliverability-box {{
                padding: 12px;
            }}
            
            .deliverability-box li {{
                font-size: 12px;
            }}
            
            .btn {{
                display: block;
                text-align: center;
                padding: 12px 20px;
            }}
            
            .footer {{
                padding: 12px;
                font-size: 10px;
            }}
            
            .tracking-url {{
                font-size: 10px;
                padding: 6px 10px;
            }}
        }}
        
        @media screen and (max-width: 360px) {{
            .header h2 {{
                font-size: 15px;
            }}
            
            .info-value {{
                font-size: 11px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header">
                <h2>CampaignForge SMTP Test Report</h2>
                <p>{spoof_note}</p>
            </div>
            
            <div class="content">
                <div class="info-row">
                    <div class="info-label">SMTP Server</div>
                    <div class="info-value">{cfg.server}:{cfg.port}</div>
                </div>
                
                <div class="info-row">
                    <div class="info-label">Security</div>
                    <div class="info-value">
                        <span class="security-badge {cfg.security.lower()}">{security_badge}</span>
                    </div>
                </div>
                
                <div class="info-row">
                    <div class="info-label">Account Email</div>
                    <div class="info-value">{cfg.email}</div>
                </div>
                
                <div class="info-row">
                    <div class="info-label">From Address</div>
                    <div class="info-value">{from_display}</div>
                </div>
                
                <div class="info-row">
                    <div class="info-label">Sent At</div>
                    <div class="info-value">{current_time}</div>
                </div>
                
                <div class="info-row">
                    <div class="info-label">Tracking ID</div>
                    <div class="info-value">{tid[:16]}...{tid[-8:]}</div>
                </div>
                
                <div class="info-row">
                    <div class="info-label">Tracking URL</div>
                    <div class="info-value">
                        <div class="tracking-url">{tracking_url}</div>
                    </div>
                </div>
                
                <div class="info-row">
                    <div class="info-label">Click URL</div>
                    <div class="info-value">
                        <div class="tracking-url">{click_tracking_url}</div>
                    </div>
                </div>
                
                <div class="deliverability-box">
                    <h3>Deliverability Checklist</h3>
                    <ul>
                        <li>If in <strong>Inbox</strong> - Good deliverability</li>
                        <li>If in <strong>Spam/Junk</strong> - Check SPF/DKIM/DMARC DNS records</li>
                        <li>If <strong>Not Received</strong> - SMTP may be blocked</li>
                    </ul>
                </div>
                
                <a href="{click_tracking_url}" class="btn btn-primary" target="_blank">Test Click Tracking</a>
            </div>
            
            <div class="footer">
                <p>CampaignForge v3.0 - Automated SMTP Test - ID: {tid[:8]}</p>
                <p>Security: {cfg.security} | From: {from_display}</p>
                <p style="font-size:10px;color:#94a3b8;margin-top:4px;">Tracking URL: {tracking_url}</p>
            </div>
        </div>
    </div>
    <!-- Tracking Pixel -->
    <img src="{pixel_tracking_url}" width="1" height="1" alt="" style="display:block;width:1px;height:1px;border:0;opacity:0;">
</body>
</html>"""

        plain = f"""
╔══════════════════════════════════════════════════════════════╗
║              CampaignForge SMTP Test Report                 ║
║                         {spoof_note}                         ║
╚══════════════════════════════════════════════════════════════╝

📡 SMTP SERVER: {cfg.server}:{cfg.port}
🔒 SECURITY: {security_badge}
📧 ACCOUNT: {cfg.email}
✉️  FROM ADDRESS: {from_display}
🕐 SENT AT: {current_time}
🔑 TRACKING ID: {tid[:16]}...

────────────────────────────────────────────────────────────────

✅ DELIVERABILITY CHECKLIST:
   • Inbox (Green)    → Good deliverability
   • Spam/Junk (Red)  → Check SPF/DKIM/DMARC DNS records
   • Not Received     → SMTP may be blocked

────────────────────────────────────────────────────────────────

🔗 CLICK TRACKING TEST: {click_url}

────────────────────────────────────────────────────────────────
CampaignForge v3.0 · Automated SMTP Test · ID: {tid[:8]}
Security: {cfg.security}
"""
        return html, plain

    def _send_one(self, cfg: SMTPConfig, rec: Recipient, subject: str,
              body: str, is_html: bool, campaign_id: str = "", attachments: List = None) -> SendResult:
        start = time.time()
        pbody = self._personalize(body, rec)
        psubj = self._personalize(subject, rec)
        tid = uuid.uuid4().hex
        base = self.tracking_base_url.rstrip("/")
        from_addr = self.get_from_address(cfg)
    
        for attempt in range(self.max_retries + 1):
            if self._stop_event.is_set():
                return SendResult(rec.address, False, "Stopped", datetime.now().isoformat(), cfg.email, 0, tid)
            try:
                conn = create_smtp_connection(cfg.server, cfg.port, cfg.security, self.timeout)
                if cfg.email and cfg.password:
                    conn.login(cfg.email, cfg.password)
    
                msg = MIMEMultipart("alternative")
                display_name = self.from_name if self.from_name else "CampaignForge"
                msg["From"] = f"{display_name} <{from_addr}>"
                msg["To"] = rec.address
                msg["Subject"] = psubj
                if self.reply_to:
                    msg["Reply-To"] = self.reply_to
                msg["List-Unsubscribe"] = f"<mailto:{cfg.email}?subject=unsubscribe>"
                msg["X-Mailer"] = "CampaignForge v3.0"
                msg["X-CF-Campaign"] = campaign_id
                msg["X-CF-Tracking"] = tid
                msg["X-Security"] = cfg.security
    
                plain = re.sub(r'<[^>]+>', '', pbody) if is_html else pbody
                plain += self._unsub_plain(rec.address)
                msg.attach(MIMEText(plain, "plain", "utf-8"))
    
                if is_html:
                    html = pbody
                    if self.unsubscribe_footer:
                        footer = self._unsub_html(rec.address)
                        html = re.sub(r'</body>', footer + '</body>', html, flags=re.IGNORECASE) \
                               if "</body>" in html.lower() else html + footer
                    if base:
                        html = self._inject_tracking(html, tid, base)
                    msg.attach(MIMEText(html, "html", "utf-8"))
                elif base:
                    pixel_url = f"{base}/track/open/{tid}"
                    html_wrap = (f'<html><body><pre style="font-family:inherit;white-space:pre-wrap">{pbody}</pre>'
                                 f'<img src="{pixel_url}" width="1" height="1" alt="" style="opacity:0"></body></html>')
                    msg.attach(MIMEText(html_wrap, "html", "utf-8"))
    
                if attachments:
                    mixed = MIMEMultipart("mixed")
                    
                    for header in ["From", "To", "Subject", "Reply-To", "List-Unsubscribe", 
                                  "X-Mailer", "X-CF-Campaign", "X-CF-Tracking", "X-Security"]:
                        if header in msg:
                            mixed[header] = msg[header]
                    
                    alt = MIMEMultipart("alternative")
                    for part in msg.get_payload():
                        alt.attach(part)
                    
                    mixed.attach(alt)
                    
                    for attachment in attachments:
                        try:
                            if isinstance(attachment, dict):
                                filename = attachment.get("filename", "attachment")
                                content = attachment.get("content", b"")
                                content_type = attachment.get("content_type", "application/octet-stream")
                                
                                if isinstance(content, str):
                                    try:
                                        import base64
                                        content = base64.b64decode(content)
                                    except Exception:
                                        content = content.encode("utf-8")
                                
                                part = MIMEText(content, "plain", "utf-8")
                                part.add_header("Content-Type", content_type)
                                part.add_header("Content-Disposition", f"attachment; filename=\"{filename}\"")
                                part.add_header("Content-Transfer-Encoding", "base64")
                                import base64
                                part.set_payload(base64.b64encode(content).decode("ascii"))
                                mixed.attach(part)
                        except Exception as e:
                            logger.warning(f"Failed to attach file: {e}")
                    
                    msg = mixed
    
                conn.send_message(msg)
                conn.quit()
    
                ms = int((time.time() - start) * 1000)
                with self._lock:
                    cfg.sent_count += 1
                    cfg.last_used = time.time()
                    cfg.health = min(1.0, cfg.health + 0.05)
                    self.tracking_events[tid] = TrackingEvent(
                        id=tid, smtp_email=cfg.email, smtp_server=cfg.server,
                        sent_to=rec.address, sent_at=datetime.now().isoformat()
                    )
                return SendResult(rec.address, True, "", datetime.now().isoformat(), cfg.email, ms, tid)
    
            except smtplib.SMTPAuthenticationError:
                with self._lock:
                    cfg.health = 0.0
                return SendResult(rec.address, False, "Auth failed", datetime.now().isoformat(), cfg.email, 0, tid)
            except smtplib.SMTPRecipientsRefused:
                return SendResult(rec.address, False, "Recipient refused", datetime.now().isoformat(), cfg.email, 0, tid)
            except Exception as e:
                if attempt < self.max_retries:
                    time.sleep(1.5 ** attempt)
                    continue
                with self._lock:
                    cfg.fail_count += 1
                    cfg.health = max(0.0, cfg.health - 0.15)
                return SendResult(rec.address, False, str(e)[:120],
                                  datetime.now().isoformat(), cfg.email,
                                  int((time.time()-start)*1000), tid)
        return SendResult(rec.address, False, "Max retries exceeded", datetime.now().isoformat(), cfg.email, 0, tid)

    def kill_dead_smtps(self) -> List[str]:
        removed = []
        alive = []
        for cfg in self.smtp_configs:
            if cfg.is_dead:
                removed.append(f"{cfg.email} ({cfg.server})")
            else:
                alive.append(cfg)
        self.smtp_configs = alive
        return removed

    def mark_as_dead(self, index: int) -> bool:
        if 0 <= index < len(self.smtp_configs):
            self.smtp_configs[index].is_dead = True
            self.smtp_configs[index].health = 0.0
            return True
        return False

    def purge_failed_tests(self) -> List[str]:
        removed = []
        alive = []
        for cfg in self.smtp_configs:
            if cfg.test_status == "fail":
                removed.append(f"{cfg.email} ({cfg.server})")
            else:
                alive.append(cfg)
        self.smtp_configs = alive
        return removed

    def auto_test_all(self, test_recipient: str, test_recipient_name: str = "",
                      base_url: str = "") -> List[dict]:
        results = []
        for i, cfg in enumerate(self.smtp_configs):
            cfg.is_dead = False
            ok, msg = self.test_connection(i)
            row = {
                "index": i, "email": cfg.email, "server": cfg.server,
                "port": cfg.port, "security": cfg.security,
                "connected": ok, "message": msg,
                "test_sent": False, "send_message": "", "tid": "",
                "spam_score": 0, "spam_grade": ""
            }
            if ok and test_recipient:
                sent, smsg, tid, spam = self.send_test_email(
                    i, test_recipient, test_recipient_name, base_url
                )
                row["test_sent"] = sent
                row["send_message"] = smsg
                row["tid"] = tid
                row["spam_score"] = spam.get("score", 0)
                row["spam_grade"] = spam.get("grade", "")
            elif ok:
                row["send_message"] = "No test recipient configured"
            else:
                cfg.is_dead = True
            results.append(row)
            time.sleep(0.4)
        return results

    def load_recipients(self, lines: List[str], channel: str = "email",
                       carrier_country: str = "USA", carrier_name: str = "AT&T") -> Tuple[int, int]:
        valid, skipped, new_recs = 0, 0, []
        gateway = CARRIER_GATEWAYS.get(carrier_country, {}).get(carrier_name)
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            if line.lower().startswith("email") or line.lower().startswith("phone"):
                continue
            
            digits_only = re.sub(r'\D', '', line)
            is_phone = len(digits_only) >= 10 and re.match(r'^\d+$', digits_only)
            is_email = '@' in line and '.' in line
            
            if is_phone and (channel == "sms" or channel == "both"):
                if gateway:
                    converted = f"{digits_only}@{gateway}"
                    if not any(r.address == converted for r in new_recs) and \
                       not any(r.address == converted for r in self.recipients):
                        new_recs.append(Recipient(
                            address=converted,
                            name=digits_only,
                            channel="sms",
                            carrier=f"{carrier_country}/{carrier_name}"
                        ))
                        valid += 1
                    else:
                        skipped += 1
                else:
                    skipped += 1
            elif is_email and (channel == "email" or channel == "both"):
                address = line
                name = ""
                if "," in line:
                    parts = [p.strip() for p in line.split(",")]
                    address = parts[0]
                    name = parts[1] if len(parts) > 1 else ""
                elif "<" in line and ">" in line:
                    match = re.search(r'<([^>]+)>', line)
                    if match:
                        address = match.group(1)
                        name = line.replace(f"<{address}>", "").strip()
                
                if not any(r.address == address for r in new_recs) and \
                   not any(r.address == address for r in self.recipients):
                    new_recs.append(Recipient(
                        address=address,
                        name=name,
                        channel="email",
                        carrier=""
                    ))
                    valid += 1
                else:
                    skipped += 1
            elif channel == "email" and line:
                if not any(r.address == line for r in new_recs) and \
                   not any(r.address == line for r in self.recipients):
                    new_recs.append(Recipient(
                        address=line,
                        name="",
                        channel="email",
                        carrier=""
                    ))
                    valid += 1
                else:
                    skipped += 1
            elif not is_email and (channel == "sms" or channel == "both"):
                digits = re.sub(r'\D', '', line)
                if len(digits) >= 10 and gateway:
                    converted = f"{digits}@{gateway}"
                    if not any(r.address == converted for r in new_recs) and \
                       not any(r.address == converted for r in self.recipients):
                        new_recs.append(Recipient(
                            address=converted,
                            name=line,
                            channel="sms",
                            carrier=f"{carrier_country}/{carrier_name}"
                        ))
                        valid += 1
                    else:
                        skipped += 1
                else:
                    skipped += 1
            else:
                skipped += 1
        
        self.recipients.extend(new_recs)
        return valid, skipped

    def _personalize(self, text: str, rec: Recipient) -> str:
        text = text.replace("{{name}}", rec.name or rec.address.split("@")[0])
        text = text.replace("{{email}}", rec.address)
        for k, v in rec.tags.items():
            text = text.replace(f"{{{{{k}}}}}", str(v))
        return text

    def _inject_tracking(self, html: str, tid: str, base: str) -> str:
        pixel = (f'<img src="{base}/track/open/{tid}" width="1" height="1" '
                 f'alt="" style="display:block;width:1px;height:1px;border:0;opacity:0">')
        def wrap_link(m):
            url = m.group(2)
            if "/track/" in url or "unsubscribe" in url:
                return m.group(0)
            enc = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
            return f'{m.group(1)}{base}/track/click/{tid}?url={enc}{m.group(3)}'
        html = re.sub(r'(href=["\'])([^"\'#][^"\']*?)(["\'])', wrap_link, html)
        if "</body>" in html.lower():
            html = re.sub(r'</body>', pixel + '</body>', html, flags=re.IGNORECASE)
        else:
            html += pixel
        return html

    def _unsub_html(self, addr: str) -> str:
        link = f"https://yourdomain.com/unsubscribe?email={addr}"
        pa = f"<br>{self.physical_address}" if self.physical_address else ""
        return (f'<p style="font-size:11px;color:#9ca3af;text-align:center;margin-top:40px;line-height:1.7">'
                f'You received this because you subscribed. '
                f'<a href="{link}" style="color:#9ca3af">Unsubscribe</a>.{pa}</p>')

    def _unsub_plain(self, addr: str) -> str:
        if not self.unsubscribe_footer: return ""
        link = f"https://yourdomain.com/unsubscribe?email={addr}"
        return f"\n\n---\nUnsubscribe: {link}" + (f"\n{self.physical_address}" if self.physical_address else "")

    def _best_smtp(self) -> Optional[SMTPConfig]:
        alive = [s for s in self.smtp_configs if s.health > 0.1 and not s.is_dead]
        if not alive: return None
        alive.sort(key=lambda s: (-s.health, s.last_used))
        return alive[0]

    def run_campaign(self, cid: str):
        camp = self.campaigns.get(cid)
        if not camp:
            return
        camp.status = "running"
        camp.total = len(self.recipients)
        self._stop_event.clear()
        self.active_campaign_id = cid
    
        def worker(rec):
            if self._stop_event.is_set():
                return None
            cfg = self._best_smtp()
            if not cfg:
                return SendResult(rec.address, False, "No healthy SMTP", datetime.now().isoformat(), "")
            result = self._send_one(cfg, rec, camp.subject, camp.body, camp.is_html, camp.id, camp.attachments)
            time.sleep(self.delay_between)
            return result
    
        done = 0
        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            futures = {pool.submit(worker, rec): rec for rec in self.recipients}
            for fut in as_completed(futures):
                result = fut.result()
                if result:
                    with self._lock:
                        camp.results.append(result)
                        if result.success:
                            camp.sent += 1
                            self.session_sent += 1
                        else:
                            camp.failed += 1
                            self.session_failed += 1
                done += 1
                camp.progress = (done / camp.total) * 100
    
        camp.status = "done" if not self._stop_event.is_set() else "paused"
        self.active_campaign_id = None

    def stop(self): self._stop_event.set()

    def export_results(self, cid: str) -> str:
        camp = self.campaigns.get(cid)
        if not camp: return ""
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["Timestamp","Recipient","Status","Error","SMTP","Duration_ms","Opened","Clicked","TrackingID"])
        for r in camp.results:
            evt = self.tracking_events.get(r.tracking_id)
            w.writerow([r.timestamp, r.recipient, "Sent" if r.success else "Failed",
                        r.error, r.smtp_used, r.duration_ms,
                        "Yes" if (evt and evt.opened) else "No",
                        "Yes" if (evt and evt.clicked) else "No",
                        r.tracking_id])
        return out.getvalue()

engine = CampaignEngine()

# ─────────────────────────────────────────────
# RECIPIENTS API - Enhanced
# ─────────────────────────────────────────────

@app.route("/api/recipients/list", methods=["GET"])
def get_recipients_list():
    return jsonify({
        "success": True,
        "count": len(engine.recipients),
        "recipients": [
            {
                "address": r.address,
                "name": r.name,
                "channel": r.channel,
                "carrier": r.carrier,
                "tags": r.tags,
                "subscribed": r.subscribed
            }
            for r in engine.recipients
        ]
    })

@app.route("/api/recipients/remove", methods=["POST"])
def remove_recipient():
    data = request.json or {}
    address = data.get("address", "")
    if not address:
        return jsonify({"success": False, "message": "No address provided"})
    original_count = len(engine.recipients)
    engine.recipients = [r for r in engine.recipients if r.address != address]
    new_count = len(engine.recipients)
    if new_count < original_count:
        return jsonify({"success": True, "message": f"Removed {address}"})
    return jsonify({"success": False, "message": "Recipient not found"})

@app.route("/api/recipients/clear", methods=["POST"])
def clear_recipients():
    count = len(engine.recipients)
    engine.recipients = []
    return jsonify({"success": True, "message": f"Cleared {count} recipients"})

@app.route("/api/recipients/search", methods=["POST"])
def search_recipients():
    data = request.json or {}
    query = data.get("query", "").lower().strip()
    if not query:
        return jsonify({"success": True, "recipients": [asdict(r) for r in engine.recipients]})
    results = [
        r for r in engine.recipients 
        if query in r.address.lower() or (r.name and query in r.name.lower())
    ]
    return jsonify({
        "success": True,
        "count": len(results),
        "recipients": [asdict(r) for r in results]
    })

# ─────────────────────────────────────────────
# TRACKING ROUTES
# ─────────────────────────────────────────────
@app.route("/track/open/<tid>")
def track_open(tid):
    with engine._lock:
        evt = engine.tracking_events.get(tid)
        if evt and not evt.opened:
            evt.opened = True
            evt.opened_at = datetime.now().isoformat()
            for camp in engine.campaigns.values():
                for r in camp.results:
                    if r.tracking_id == tid: camp.opens += 1; break
    return Response(TRACKING_PIXEL, mimetype="image/gif",
                    headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"})

@app.route("/track/click/<tid>")
def track_click(tid):
    raw = request.args.get("url", "https://example.com")
    try:
        padded = raw + "=" * (-len(raw) % 4)
        destination = base64.urlsafe_b64decode(padded).decode()
    except Exception:
        destination = raw
    with engine._lock:
        evt = engine.tracking_events.get(tid)
        if evt and not evt.clicked:
            evt.clicked = True; evt.clicked_at = datetime.now().isoformat(); evt.click_url = destination
            for camp in engine.campaigns.values():
                for r in camp.results:
                    if r.tracking_id == tid: camp.clicks += 1; break
    return redirect(destination, code=302)

@app.route("/api/spam/score", methods=["POST"])
def calculate_spam_score():
    data = request.json or {}
    subject = data.get("subject", "")
    body = data.get("body", "")
    is_html = data.get("is_html", False)
    result = SpamScoreCalculator.calculate_score(subject, body, is_html)
    return jsonify(result)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _base_url() -> str:
    if engine.tracking_base_url:
        return engine.tracking_base_url.rstrip("/")
    try:
        host = request.host
        return f"http://{host}"
    except Exception:
        return f"http://localhost:{APP_PORT}"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def auto_detect_base_url():
    try:
        host = request.host
        if ":" in host:
            host = host.split(":")[0]
        if host in ["localhost", "127.0.0.1"]:
            return f"http://localhost:{APP_PORT}"
        return f"http://{host}:{APP_PORT}"
    except Exception:
        return f"http://localhost:{APP_PORT}"

def fix_tracking_url(url):
    url = url.rstrip("/")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    return url
    
# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/app")
def app_dashboard():
    return render_template("app.html")

@app.route("/tracking")
@app.route("/tracking.html")
def tracking():
    return render_template("tracking.html")

# ─────────────────────────────────────────────
# API ROUTES (continued)
# ─────────────────────────────────────────────

@app.route("/api/carriers")
def get_carriers():
    return jsonify(CARRIER_GATEWAYS)

@app.route("/api/esp_whitelist")
def get_esp_whitelist():
    return jsonify(ESP_WHITELIST_INFO)

@app.route("/api/smtp/upload", methods=["POST"])
def upload_smtp():
    f = request.files.get("file")
    if not f: return jsonify({"success": False, "message": "No file provided"})
    count = engine.load_smtp(f.read().decode("utf-8", errors="ignore").splitlines())
    if count == 0: return jsonify({"success": False, "count": 0, "message": "No valid SMTP entries found"})
    test_results = engine.auto_test_all(engine.test_recipient, engine.test_recipient_name, _base_url()) if engine.auto_test_on_upload else []
    return jsonify({"success": True, "count": count, "message": f"Loaded {count} SMTP server(s)",
                    "auto_tested": engine.auto_test_on_upload, "test_results": test_results})

@app.route("/api/smtp/paste", methods=["POST"])
def paste_smtp():
    data = request.json or {}
    count = engine.load_smtp(data.get("content", "").splitlines())
    test_results = engine.auto_test_all(engine.test_recipient, engine.test_recipient_name, _base_url()) if (engine.auto_test_on_upload and count > 0) else []
    return jsonify({"success": count > 0, "count": count, "message": f"Loaded {count} SMTP server(s)",
                    "auto_tested": engine.auto_test_on_upload, "test_results": test_results})

@app.route("/api/smtp/test_all", methods=["POST"])
def test_all_smtp():
    data = request.json or {}
    results = engine.auto_test_all(
        data.get("recipient", engine.test_recipient),
        data.get("recipient_name", engine.test_recipient_name),
        _base_url()
    )
    return jsonify({"success": True, "results": results})

@app.route("/api/smtp/test_one", methods=["POST"])
def test_one_smtp():
    data = request.json or {}
    idx = int(data.get("index", 0))
    mode = data.get("mode", "full")
    recipient = data.get("recipient", engine.test_recipient)
    recipient_name = data.get("recipient_name", engine.test_recipient_name)
    if mode == "connect_only":
        ok, msg = engine.test_connection(idx)
        return jsonify({"success": ok, "message": msg, "spam_score": 0})
    ok, msg, tid, spam = engine.send_test_email(idx, recipient, recipient_name, _base_url())
    return jsonify({
        "success": ok,
        "message": msg,
        "tid": tid,
        "spam_score": spam.get("score", 0),
        "spam_grade": spam.get("grade", ""),
        "spam_warnings": spam.get("warnings", [])
    })

@app.route("/api/smtp/kill_dead", methods=["POST"])
def kill_dead_smtps():
    data = request.json or {}
    action = data.get("action", "mark")
    if action == "purge":
        removed = engine.purge_failed_tests()
    else:
        removed = engine.kill_dead_smtps()
    return jsonify({"success": True, "removed": removed, "count": len(removed)})

@app.route("/api/smtp/list")
def list_smtp():
    return jsonify([{
        "index": i, "server": s.server, "port": s.port, "email": s.email, 
        "label": s.label, "spoof_email": s.spoof_email, "use_spoof": s.use_spoof,
        "security": s.security,
        "health": round(s.health, 2), "sent": s.sent_count, "failed": s.fail_count,
        "test_status": s.test_status, "test_message": s.test_message, 
        "test_send_id": s.test_send_id, "test_spam_score": s.test_spam_score,
        "is_dead": s.is_dead, "last_tested_at": s.last_tested_at
    } for i, s in enumerate(engine.smtp_configs)])

@app.route("/api/smtp/toggle_spoof", methods=["POST"])
def toggle_smtp_spoof():
    data = request.json or {}
    idx = int(data.get("index", -1))
    use_spoof = data.get("use_spoof", False)
    if 0 <= idx < len(engine.smtp_configs):
        engine.smtp_configs[idx].use_spoof = use_spoof
        return jsonify({"success": True, "message": f"Spoof mode {'enabled' if use_spoof else 'disabled'}"})
    return jsonify({"success": False, "message": "Invalid index"})

@app.route("/api/smtp/update_security", methods=["POST"])
def update_smtp_security():
    data = request.json or {}
    idx = int(data.get("index", -1))
    security = data.get("security", "TLS")
    if security not in ["TLS", "SSL", "NONE"]:
        security = "TLS"
    if 0 <= idx < len(engine.smtp_configs):
        engine.smtp_configs[idx].security = security
        return jsonify({"success": True, "message": f"Security updated to {security}"})
    return jsonify({"success": False, "message": "Invalid index"})

# Recipients routes
@app.route("/api/recipients/upload", methods=["POST"])
def upload_recipients():
    f = request.files.get("file")
    if not f:
        return jsonify({"success": False, "message": "No file provided"})
    channel = request.form.get("channel", "email")
    country = request.form.get("country", "USA")
    carrier = request.form.get("carrier", "AT&T")
    content = f.read().decode("utf-8", errors="ignore")
    lines = content.splitlines()
    v, sk = engine.load_recipients(lines, channel, country, carrier)
    return jsonify({
        "success": v > 0,
        "valid": v,
        "skipped": sk,
        "message": f"Loaded {v} recipient(s) ({sk} skipped)",
        "count": len(engine.recipients)
    })

@app.route("/api/recipients/paste", methods=["POST"])
def paste_recipients():
    data = request.json or {}
    v, sk = engine.load_recipients(
        data.get("content", "").splitlines(),
        data.get("channel", "email"),
        data.get("country", ""), 
        data.get("carrier", "")
    )
    return jsonify({
        "success": v > 0, 
        "valid": v, 
        "skipped": sk, 
        "message": f"Loaded {v} recipient(s) ({sk} skipped)",
        "count": len(engine.recipients)
    })

@app.route("/api/recipients/count")
def recipient_count():
    return jsonify({"count": len(engine.recipients),
                    "email": sum(1 for r in engine.recipients if r.channel == "email"),
                    "sms":   sum(1 for r in engine.recipients if r.channel == "sms")})

@app.route("/api/recipients/add_batch", methods=["POST"])
def add_recipients_batch():
    data = request.json or {}
    recipients_data = data.get("recipients", [])
    if not recipients_data:
        return jsonify({"success": False, "message": "No recipients provided"})
    added = 0
    skipped = 0
    for r in recipients_data:
        address = r.get("address", "")
        name = r.get("name", "")
        channel = r.get("channel", "email")
        carrier = r.get("carrier", "")
        if not address:
            skipped += 1
            continue
        if any(existing.address == address for existing in engine.recipients):
            skipped += 1
            continue
        recipient = Recipient(
            address=address,
            name=name,
            channel=channel,
            carrier=carrier
        )
        engine.recipients.append(recipient)
        added += 1
    return jsonify({
        "success": True,
        "added": added,
        "skipped": skipped,
        "message": f"Added {added} recipients ({skipped} skipped)"
    })

# Tracking routes
@app.route("/api/tracking/events")
def tracking_events_api():
    evts = sorted(engine.tracking_events.values(), key=lambda e: e.sent_at, reverse=True)
    return jsonify([asdict(e) for e in evts[:300]])

@app.route("/api/tracking/smtp_report")
def smtp_tracking_report():
    report = {}
    for cfg in engine.smtp_configs:
        report[cfg.email] = {
            "server": cfg.server, "email": cfg.email, "security": cfg.security,
            "test_status": cfg.test_status, "test_message": cfg.test_message,
            "test_send_id": cfg.test_send_id, "test_spam_score": cfg.test_spam_score,
            "total_sent": cfg.sent_count, "total_failed": cfg.fail_count,
            "opens": 0, "clicks": 0, "health": round(cfg.health, 2), "is_dead": cfg.is_dead
        }
    for evt in engine.tracking_events.values():
        if evt.smtp_email in report:
            if evt.opened:  report[evt.smtp_email]["opens"]  += 1
            if evt.clicked: report[evt.smtp_email]["clicks"] += 1
    return jsonify(list(report.values()))

@app.route("/api/tracking/event/<tid>")
def get_tracking_event(tid):
    evt = engine.tracking_events.get(tid)
    if not evt: return jsonify({"error": "not found"}), 404
    return jsonify(asdict(evt))

# Tracking stats
tracking_stats = {
    'total_opens': 0,
    'total_clicks': 0,
    'unique_visitors': set(),
    'events': []
}

@app.route("/api/tracking/record", methods=["POST"])
def record_tracking():
    data = request.json or {}
    event_type = data.get('type', 'open')
    tracking_id = data.get('tid') or data.get('tracking_id', str(uuid.uuid4())[:8])
    device_id = data.get('device_id', 'unknown')
    ip = request.remote_addr
    event = {
        'id': tracking_id,
        'type': event_type,
        'timestamp': datetime.now().isoformat(),
        'ip': ip,
        'device_id': device_id,
        'user_agent': request.headers.get('User-Agent', ''),
        'referer': request.headers.get('Referer', ''),
        'campaign': data.get('campaign', ''),
        'recipient': data.get('recipient', ''),
        'url': data.get('url', '')
    }
    with engine._lock:
        tracking_stats['events'].append(event)
        if event_type == 'open':
            tracking_stats['total_opens'] += 1
        elif event_type == 'click':
            tracking_stats['total_clicks'] += 1
        tracking_stats['unique_visitors'].add(device_id)
    return jsonify({
        'success': True,
        'event_id': tracking_id,
        'type': event_type,
        'timestamp': event['timestamp']
    })

@app.route("/api/tracking/stats", methods=["GET"])
def get_tracking_stats():
    return jsonify({
        'total_opens': tracking_stats['total_opens'],
        'total_clicks': tracking_stats['total_clicks'],
        'unique_visitors': len(tracking_stats['unique_visitors']),
        'total_events': len(tracking_stats['events'])
    })

@app.route("/api/tracking/events", methods=["GET"])
def get_tracking_events():
    limit = request.args.get('limit', 100, type=int)
    events = sorted(tracking_stats['events'], key=lambda x: x['timestamp'], reverse=True)[:limit]
    return jsonify({
        'success': True,
        'count': len(events),
        'events': events
    })

@app.route("/api/tracking/clear", methods=["POST"])
def clear_tracking():
    global tracking_stats
    tracking_stats = {
        'total_opens': 0,
        'total_clicks': 0,
        'unique_visitors': set(),
        'events': []
    }
    return jsonify({'success': True, 'message': 'Tracking data cleared'})

@app.route("/api/tracking/campaign/<campaign_id>", methods=["GET"])
def get_campaign_tracking(campaign_id):
    events = [e for e in tracking_stats['events'] if e.get('campaign') == campaign_id]
    opens = len([e for e in events if e['type'] == 'open'])
    clicks = len([e for e in events if e['type'] == 'click'])
    unique = len(set(e.get('device_id', '') for e in events if e.get('device_id')))
    return jsonify({
        'campaign_id': campaign_id,
        'opens': opens,
        'clicks': clicks,
        'unique_visitors': unique,
        'total_events': len(events)
    })

# Campaign routes
@app.route("/api/campaign/create", methods=["POST"])
def create_campaign():
    data = request.json or {}
    cid = str(uuid.uuid4())[:8]
    attachments = data.get("attachments", [])
    engine.campaigns[cid] = Campaign(
        id=cid,
        name=data.get("name", f"Campaign {cid}"),
        subject=data.get("subject", ""),
        body=data.get("body", ""),
        is_html=data.get("is_html", False),
        channel=data.get("channel", "email"),
        created_at=datetime.now().isoformat(),
        attachments=attachments
    )
    return jsonify({"success": True, "campaign_id": cid})

@app.route("/api/campaign/upload_attachment", methods=["POST"])
def upload_attachment():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file provided"})
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "No file selected"})
    try:
        import base64
        filename = file.filename
        content_type = file.content_type or "application/octet-stream"
        content = file.read()
        content_b64 = base64.b64encode(content).decode("utf-8")
        size = len(content)
        return jsonify({
            "success": True,
            "attachment": {
                "filename": filename,
                "content_type": content_type,
                "content": content_b64,
                "size": size
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/campaign/start/<cid>", methods=["POST"])
def start_campaign(cid):
    if cid not in engine.campaigns: return jsonify({"success": False, "message": "Campaign not found"})
    if not engine.smtp_configs:     return jsonify({"success": False, "message": "No SMTP servers loaded"})
    if not engine.recipients:       return jsonify({"success": False, "message": "No recipients loaded"})
    threading.Thread(target=engine.run_campaign, args=(cid,), daemon=True).start()
    return jsonify({"success": True, "message": "Campaign started"})

@app.route("/api/campaign/stop", methods=["POST"])
def stop_campaign():
    engine.stop(); return jsonify({"success": True})

@app.route("/api/campaign/status/<cid>")
def campaign_status(cid):
    camp = engine.campaigns.get(cid)
    if not camp: return jsonify({"error": "not found"})
    return jsonify({
        "id": camp.id, "name": camp.name, "status": camp.status,
        "sent": camp.sent, "failed": camp.failed, "total": camp.total,
        "progress": round(camp.progress, 1), "opens": camp.opens, "clicks": camp.clicks,
        "open_rate":  round(camp.opens  / camp.sent * 100, 1) if camp.sent else 0,
        "click_rate": round(camp.clicks / camp.sent * 100, 1) if camp.sent else 0,
        "recent_results": [asdict(r) for r in camp.results[-30:]]
    })

@app.route("/api/campaign/export/<cid>")
def export_campaign(cid):
    csv_data = engine.export_results(cid)
    if not csv_data: return jsonify({"error": "not found"})
    buf = io.BytesIO(csv_data.encode()); buf.seek(0)
    return send_file(buf, mimetype="text/csv",
                     download_name=f"campaign_{cid}_results.csv", as_attachment=True)

@app.route("/api/campaigns")
def list_campaigns():
    return jsonify([{
        "id": c.id, "name": c.name, "status": c.status,
        "sent": c.sent, "failed": c.failed, "total": c.total,
        "opens": c.opens, "clicks": c.clicks,
        "created_at": c.created_at, "channel": c.channel
    } for c in engine.campaigns.values()])

# Settings routes
@app.route("/api/settings", methods=["GET"])
def get_settings():
    tracking_url = engine.tracking_base_url
    if not tracking_url:
        tracking_url = auto_detect_base_url()
    else:
        tracking_url = fix_tracking_url(tracking_url)
    return jsonify({
        "concurrency": engine.concurrency,
        "delay_between": engine.delay_between,
        "max_retries": engine.max_retries,
        "timeout": engine.timeout,
        "daily_limit": engine.daily_limit,
        "from_name": engine.from_name,
        "from_address": engine.from_address,
        "reply_to": engine.reply_to,
        "physical_address": engine.physical_address,
        "unsubscribe_footer": engine.unsubscribe_footer,
        "whitelist_mode": engine.whitelist_mode,
        "whitelist_esp": engine.whitelist_esp,
        "test_recipient": engine.test_recipient,
        "test_recipient_name": engine.test_recipient_name,
        "tracking_base_url": tracking_url,
        "auto_test_on_upload": engine.auto_test_on_upload,
        "enable_spoofing": engine.enable_spoofing,
    })

@app.route("/api/settings", methods=["POST"])
def save_settings():
    d = request.json or {}
    engine.concurrency        = max(1, min(10, int(d.get("concurrency", 3))))
    engine.delay_between      = max(0.1, float(d.get("delay_between", 0.5)))
    engine.max_retries        = max(0, min(5, int(d.get("max_retries", 2))))
    engine.timeout            = max(5, int(d.get("timeout", 20)))
    engine.daily_limit        = int(d.get("daily_limit", 0))
    engine.from_name          = d.get("from_name", "")
    engine.from_address       = d.get("from_address", "")
    engine.reply_to           = d.get("reply_to", "")
    engine.physical_address   = d.get("physical_address", "")
    engine.unsubscribe_footer = bool(d.get("unsubscribe_footer", True))
    engine.whitelist_mode     = bool(d.get("whitelist_mode", False))
    engine.whitelist_esp      = d.get("whitelist_esp", "Custom SMTP")
    engine.test_recipient     = d.get("test_recipient", "")
    engine.test_recipient_name = d.get("test_recipient_name", "")
    engine.auto_test_on_upload = bool(d.get("auto_test_on_upload", True))
    engine.enable_spoofing     = bool(d.get("enable_spoofing", False))
    tracking_url = d.get("tracking_base_url", "").rstrip("/")
    if not tracking_url:
        tracking_url = auto_detect_base_url()
    else:
        tracking_url = fix_tracking_url(tracking_url)
    engine.tracking_base_url = tracking_url
    return jsonify({
        "success": True, 
        "message": "Settings saved",
        "tracking_url": tracking_url
    })

@app.route("/api/stats")
def global_stats():
    total_opens  = sum(1 for e in engine.tracking_events.values() if e.opened)
    total_clicks = sum(1 for e in engine.tracking_events.values() if e.clicked)
    return jsonify({
        "smtp_count":      len(engine.smtp_configs),
        "smtp_healthy":    sum(1 for s in engine.smtp_configs if s.health > 0.5 and not s.is_dead),
        "smtp_failed":     sum(1 for s in engine.smtp_configs if s.health <= 0.1 or s.is_dead),
        "smtp_dead":       sum(1 for s in engine.smtp_configs if s.is_dead),
        "recipient_count": len(engine.recipients),
        "campaign_count":  len(engine.campaigns),
        "session_sent":    engine.session_sent,
        "session_failed":  engine.session_failed,
        "total_opens":     total_opens,
        "total_clicks":    total_clicks,
        "active_campaign": engine.active_campaign_id,
        "smtp_health":     [round(s.health, 2) for s in engine.smtp_configs],
    })

if __name__ == "__main__":
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"
    
    print("\n" + "="*70)
    print("CampaignForge v3.0  |  Email & SMS Campaign Platform")
    print("="*70)
    print(f"Local Access: http://localhost:{APP_PORT}")
    print(f"Network Access: http://{local_ip}:{APP_PORT}")
    print(f"Tracking URL: http://localhost:{APP_PORT}/tracking.html")
    print("-"*70)
    print("Features: SMTP Killing • Spoofing • Spam Scoring • TLS/SSL/NONE")
    print("Supported: TLS | SSL | NONE")
    print("="*70)
    print(f"Running on port {APP_PORT}")
    if APP_PORT == 80:
        print("Note: Port 80 requires admin/sudo privileges")
        print("Linux/Mac: sudo python app.py")
        print("Windows:   Run as Administrator")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=APP_PORT, threaded=True)