# CampaignForge v3.0

**Professional Email & SMS Campaign Platform**

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Stable-brightgreen.svg)]()

CampaignForge is a self-hosted email and SMS marketing platform with multi-SMTP support, real-time tracking, and advanced deliverability features. Built with Flask and Python, it provides a professional interface for managing bulk email and SMS campaigns.

---

## Features

### Core Features
- **Multi-SMTP Server Management** - Add unlimited SMTP servers with health monitoring
- **Email Campaigns** - Create and launch campaigns with HTML/Plain Text support
- **SMS Delivery** - Send SMS via carrier gateways (Email-to-SMS)
- **Real-time Tracking** - Open and click tracking with pixel and redirect
- **Spam Score Analysis** - Check content before sending
- **Campaign Analytics** - Dashboard with performance metrics
- **Session Persistence** - Save and restore sessions with localStorage

### SMTP Features
- TLS, SSL, and NONE security support
- Automatic health monitoring and dead server detection
- Connection timeout handling
- Auto-detection of security protocols
- Global From Address override (spoofing)
- Per-SMTP spoof email support

### Campaign Features
- HTML and Plain Text email support
- Personalization variables (`{{name}}`, `{{email}}`)
- Built-in email templates (Welcome, Newsletter, Promo, Transactional, Survey, Announcement)
- Campaign scheduling
- Live send logging
- CSV export of campaign results

### Tracking Features
- Invisible 1x1 pixel tracking for opens
- URL redirect tracking for clicks
- Campaign-specific analytics
- Real-time tracking statistics
- Unsubscribe handling with redirect

### Recipient Management
- Bulk upload from CSV/TXT files
- Paste recipient lists
- Email format: `email@domain.com` or `email,Name`
- Phone to email conversion for SMS
- Carrier gateway support (USA, Canada, Australia, UK)
- Search and filter recipients
- Export recipients to CSV

### User Interface
- Dark/Light mode toggle
- Responsive mobile design
- Collapsible sidebar
- Toast notifications
- Activity logging
- Session export/import

---

## Screenshots

### Dashboard
```
+--------------------------------------------------+
|  CampaignForge  | SMTP: 3  Recipients: 150       |
+--------------------------------------------------+
|  SMTP Servers   |  Recipients  |  Campaigns      |
|  5 configured   |  150 loaded  |  12 created     |
+--------------------------------------------------+
|  Active Campaign: June Newsletter                |
|  ████████████░░░░░░░░ 65%                        |
|  650 sent / 350 failed / 1000 total              |
+--------------------------------------------------+
|  SMTP Server Health                              |
|  smtp.gmail.com    ████████████░░ 85%            |
|  smtp.sendgrid.net ██████████░░░░ 72%            |
|  smtp.mailgun.org  ██████████████ 92%            |
+--------------------------------------------------+
```

### Compose Campaign
```
+--------------------------------------------------+
|  Compose Campaign                                |
+--------------------------------------------------+
|  Campaign Name: [June Newsletter 2025           ]|
|  Subject Line:  [Your monthly update is here    ]|
|  Channel:       [Email ▼]                        |
|  Schedule:      [2025-06-15 09:00] [Schedule]    |
+--------------------------------------------------+
|  Plain | HTML | Preview                          |
|  +--------------------------------------------+  |
|  | Dear {{name}},                             |  |
|  |                                            |  |
|  | Here's what's new this month...            |  |
|  |                                            |  |
|  | Best regards,                              |  |
|  | The Team                                   |  |
|  +--------------------------------------------+  |
|  245 characters  |  2 SMS segments               |
+--------------------------------------------------+
|  [Create & Launch]  [Save Draft]  [Spam Score]   |
+--------------------------------------------------+
```

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/campaignforge.git
cd campaignforge

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir templates uploads reports

# Run the application
sudo python app.py   # Linux/Mac
# OR
python app.py        # Windows (as Administrator)
```

### Access
- Dashboard: http://localhost:80/app
- Landing Page: http://localhost:80/
- Tracking: http://localhost:80/tracking.html

---

## SMTP Configuration

### Format
```
server|port|email|password|label|spoof_email|security
```

### Examples
```
smtp.gmail.com|587|you@gmail.com|app_password|Gmail||TLS
smtp.sendgrid.net|587|apikey|SG.xxxxx|SendGrid
smtp.mailgun.org|587|postmaster@domain|key|Mailgun|spoof@domain.com
smtp.gmail.com|465|you@gmail.com|app_password|Gmail SSL||SSL
```

### Security Types
- `TLS` - STARTTLS (Default)
- `SSL` - SMTPS (Port 465)
- `NONE` - No encryption (Testing only)

---

## Recipient Formats

### Email Mode
```
email@domain.com
email@domain.com,John Doe
jane@example.com,Jane Smith
```

### SMS Mode (Phone to Email)
```
6465386464
3135243034
9542140997
9152271883
```

---

## API Endpoints

### SMTP
```
POST /api/smtp/upload       - Upload SMTP config file
POST /api/smtp/paste        - Paste SMTP configs
POST /api/smtp/test_all     - Test all SMTP connections
POST /api/smtp/test_one     - Test single SMTP
POST /api/smtp/kill_dead    - Remove dead SMTP servers
GET  /api/smtp/list         - List all SMTP configs
```

### Recipients
```
POST /api/recipients/upload - Upload recipient file
POST /api/recipients/paste  - Paste recipients
POST /api/recipients/remove - Remove recipient
POST /api/recipients/clear  - Clear all recipients
GET  /api/recipients/list   - List all recipients
GET  /api/recipients/count  - Get recipient counts
```

### Campaigns
```
POST /api/campaign/create       - Create campaign
POST /api/campaign/start/{id}   - Start campaign
POST /api/campaign/stop         - Stop campaign
GET  /api/campaign/status/{id}  - Get campaign status
GET  /api/campaign/export/{id}  - Export campaign results
GET  /api/campaigns             - List all campaigns
```

### Tracking
```
GET  /track/open/{id}          - Track email open
GET  /track/click/{id}         - Track email click
POST /api/tracking/record      - Record tracking event
GET  /api/tracking/stats       - Get tracking stats
GET  /api/tracking/events      - Get tracking events
```

### Settings
```
GET  /api/settings        - Get current settings
POST /api/settings        - Save settings
GET  /api/stats           - Get system statistics
```

---

## System Requirements

### Hardware
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | 1 core  | 2+ cores    |
| RAM       | 512MB   | 2GB+        |
| Storage   | 100MB   | 1GB+        |

### Software
- Python 3.7 or higher
- pip package manager
- Modern web browser (Chrome, Firefox, Edge, Safari)
- SMTP server credentials

---

## Supported Platforms

### Operating Systems
- Windows 7+
- macOS 10.14+
- Linux (Ubuntu 18.04+, Debian 10+, CentOS 7+)

### SMTP Providers
- Gmail (with App Password)
- SendGrid
- Mailgun
- Amazon SES
- Postmark
- Office 365
- Any standard SMTP server

---

## Security Considerations

### Authentication
- No built-in authentication (self-hosted)
- Implement your own auth layer if needed
- Consider using a reverse proxy with authentication

### SMTP Security
- Use TLS for production environments
- Avoid NONE security except for testing
- Use App Passwords for Gmail

### Compliance
- Include physical address in emails
- Honor unsubscribe requests
- Only send to opted-in users
- Include unsubscribe footer

---

## Performance Recommendations

| Campaign Size | Concurrency | Delay (s) | Memory |
|---------------|-------------|-----------|--------|
| < 1,000       | 3           | 0.5       | 512MB  |
| 1,000 - 10,000| 5           | 0.5       | 1GB    |
| 10,000 - 50,000| 8          | 1.0       | 2GB    |
| > 50,000      | 10          | 1.5       | 4GB    |

---

## File Structure

```
campaignforge/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   ├── index.html        # Landing page
│   ├── app.html          # Main dashboard
│   └── tracking.html     # Tracking endpoint
├── uploads/               # Temporary file uploads
├── reports/               # Campaign reports
├── start.bat              # Windows start script
├── install.bat            # Windows install script
├── setup_and_start.bat    # Windows complete setup
├── start_silent.bat       # Windows silent start
├── uninstall.bat          # Windows uninstall script
└── README.md              # Documentation
```

---

## Windows Batch Scripts

| Script | Purpose |
|--------|---------|
| `start.bat` | Creates directories, installs dependencies, starts the application |
| `install.bat` | Installs dependencies and creates directories only |
| `setup_and_start.bat` | Complete setup with admin check |
| `start_silent.bat` | Starts the application in the background |
| `uninstall.bat` | Removes CampaignForge files and data |

---

## Quick Commands

### Install Dependencies
```bash
pip install -r requirements.txt
# OR
pip install Flask==2.3.3 flask-cors==4.0.1
```

### Run Application
```bash
# Linux/Mac (requires sudo for port 80)
sudo python app.py

# Windows (Run as Administrator)
python app.py

# Alternative port (change in app.py)
python app.py
```

### Access Application
```
http://localhost:80/app
http://localhost:80/
http://localhost:80/tracking.html
```

---

## Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

CMD ["python", "app.py"]
```

### Build and Run
```bash
# Build image
docker build -t campaignforge .

# Run container
docker run -d -p 80:80 --name campaignforge campaignforge

# With volume mounts
docker run -d -p 80:80 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/reports:/app/reports \
  --name campaignforge campaignforge
```

---

## Troubleshooting

### Permission Denied (Port 80)
```
# Linux/Mac
sudo python app.py

# Windows
Run as Administrator
```

### SMTP Authentication Failed
- Check email and password
- Gmail requires App Password
- Some providers require API keys

### Connection Timeout
- Check firewall settings
- Verify SMTP server is accessible
- Increase timeout in settings

### Tracking Not Working
- Verify `tracking_base_url` in settings
- Use `http://your-ip:80` for local network
- Check browser console for errors

### ModuleNotFoundError
```bash
pip install Flask==2.3.3 flask-cors==4.0.1
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

For issues and feature requests, please open an issue in the repository.

---

## Roadmap

- [x] Multi-SMTP management
- [x] Email campaign creation and sending
- [x] SMS via carrier gateways
- [x] Open and click tracking
- [x] Spam score analysis
- [x] Campaign analytics
- [x] Dark/Light mode
- [x] Mobile responsive
- [x] Session persistence
- [x] Export/Import sessions
- [ ] User authentication
- [ ] Database integration
- [ ] A/B testing
- [ ] API rate limiting
- [ ] Webhook support

---

## Acknowledgments

- Flask framework
- All contributors and users

---

## Repository Tags

`email-marketing` `sms-marketing` `smtp` `flask` `python` `bulk-email` `email-campaign` `tracking` `self-hosted` `opensource` `email-automation` `sms-gateway` `email-deliverability` `spam-checker`
