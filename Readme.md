# CampaignForge v3.0

Professional Email & SMS Campaign Platform with multi-SMTP management, real-time tracking, and advanced deliverability features.

## Features

### Core Features
- Multi-SMTP Server Management with health monitoring
- Email Campaign Creation and Launch
- SMS Delivery via Carrier Gateways (Email-to-SMS)
- Real-time Open and Click Tracking
- Spam Score Analysis
- Campaign Analytics Dashboard
- Session persistence with localStorage

### SMTP Features
- TLS, SSL, and NONE security support
- Automatic health monitoring and dead server detection
- Connection timeout handling
- Auto-detection of security protocols
- Global From Address override (spoofing)
- Per-SMTP spoof email support

### Campaign Features
- HTML and Plain Text email support
- Personalization variables ({{name}}, {{email}})
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
- Email format: email@domain.com or email,Name
- Phone to email conversion for SMS
- Carrier gateway support for SMS (USA, Canada, Australia, UK)
- Search and filter recipients
- Export recipients to CSV

### User Interface
- Dark/Light mode toggle
- Responsive mobile design
- Collapsible sidebar
- Toast notifications
- Activity logging
- Session export/import

## System Requirements

### Hardware
- CPU: 1 core minimum, 2+ cores recommended
- RAM: 512MB minimum, 2GB+ recommended for large campaigns
- Storage: 100MB for application + space for logs and reports
- Network: Internet connection for SMTP communication

### Software
- Operating System: Windows 7+, macOS 10.14+, Linux (Ubuntu 18.04+, Debian 10+, CentOS 7+)
- Python: Python 3.7 or higher
- Web Browser: Chrome 80+, Firefox 75+, Safari 13+, Edge 80+
- SMTP Access: Valid SMTP credentials from email service providers

### Python Dependencies
```
Flask==2.3.3
flask-cors==4.0.1
```

### Supported SMTP Providers
- Gmail (with App Password)
- SendGrid
- Mailgun
- Amazon SES
- Postmark
- Office 365
- Any standard SMTP server

## Installation

### Step 1: Install Python
Download and install Python 3.7 or higher from https://www.python.org/downloads/

### Step 2: Clone or Download
```
git clone https://github.com/yourusername/campaignforge.git
cd campaignforge
```

### Step 3: Install Dependencies
```
pip install -r requirements.txt
```

Or manually:
```
pip install Flask==2.3.3 flask-cors==4.0.1
```

### Step 4: Create Required Directories
```
mkdir templates uploads reports
```

### Step 5: Place Template Files
Place the following files in the templates directory:
- index.html (Landing page)
- app.html (Main dashboard)
- tracking.html (Tracking endpoint)

### Step 6: Run the Application
```
# Linux/Mac (requires sudo for port 80)
sudo python app.py

# Windows (Run as Administrator)
python app.py
```

### Step 7: Access the Application
- Dashboard: http://localhost:80/app
- Landing Page: http://localhost:80/
- Tracking: http://localhost:80/tracking.html

## SMTP Configuration Format

### Basic Format
```
server|port|email|password
```

### With Label
```
server|port|email|password|My Server
```

### With Spoof Email
```
server|port|email|password|My Server|spoof@domain.com
```

### With Security Override
```
server|port|email|password|My Server|spoof@domain.com|TLS
```

### Security Types
- TLS (STARTTLS) - Default
- SSL (SMTPS) - Port 465
- NONE (No encryption) - Testing only

### Examples
```
smtp.gmail.com|587|you@gmail.com|app_password
smtp.sendgrid.net|587|apikey|SG.xxxxx
smtp.mailgun.org|587|postmaster@domain|key|Mailgun
smtp.gmail.com|465|you@gmail.com|app_password|Gmail||SSL
smtp.office365.com|587|user@domain|pass|Office365
```

## Recipient Formats

### Email Mode
```
email@domain.com
email@domain.com,John Doe
john@example.com,John Smith
```

### SMS Mode (Phone to Email)
```
6465386464
3135243034
9542140997
9152271883
```

### Supported Carriers

USA:
- AT&T: txt.att.net
- T-Mobile: tmomail.net
- Verizon: vtext.com
- Sprint: messaging.sprintpcs.com
- Google Fi: msg.fi.google.com
- US Cellular: email.uscc.net
- Cricket: sms.cricketwireless.net
- MetroPCS: mymetropcs.com
- Boost Mobile: sms.myboostmobile.com
- Consumer Cellular: mailmymobile.net
- Simple Mobile: smtext.com
- Tracfone: mmst5.tracfone.com
- Xfinity Mobile: vtext.com
- C-Spire: cspire1.com
- Virgin Mobile: vmobl.com
- Republic Wireless: text.republicwireless.com

Canada:
- Bell: txt.bell.ca
- Rogers: pcs.rogers.com
- Telus: msg.telus.com
- Fido: fido.ca
- Koodo: msg.koodomobile.com
- Freedom Mobile: txt.freedommobile.ca
- Virgin Mobile: vmobile.ca
- SaskTel: sms.sasktel.com
- MTS: text.mtsmobility.com

Australia:
- Telstra: sms.telstra.com.au
- Optus: optusmobile.com.au
- Vodafone: voda.com.au
- Boost: sms.boost.com.au
- Amaysim: amaysim.com.au
- TPG: tpg.com.au

UK:
- EE: mms.ee.co.uk
- O2: o2imail.co.uk
- Vodafone UK: vodafone.net
- Three: three.co.uk
- Virgin Mobile: vxtras.com
- Giffgaff: giffgaff.com

## Personalization Variables

Use these variables in email subject and body:

| Variable | Description |
|----------|-------------|
| {{name}} | Recipient's name |
| {{email}} | Recipient's email address |
| {{tracking_id}} | Unique tracking ID |

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
POST /api/recipients/add_batch - Add recipients (fallback)
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
POST /api/tracking/clear       - Clear tracking data
GET  /api/tracking/campaign/{id} - Get campaign tracking
```

### Settings
```
GET  /api/settings        - Get current settings
POST /api/settings        - Save settings
GET  /api/stats           - Get system statistics
```

### Misc
```
GET /api/carriers         - Get carrier gateways
GET /api/esp_whitelist    - Get ESP whitelist info
POST /api/spam/score      - Calculate spam score
```

## Usage Guide

### 1. Configure SMTP Servers

Navigate to the SMTP Servers tab. You can either:
- Upload a .txt or .csv file with SMTP configurations
- Paste SMTP configurations directly into the text area

Format: `server|port|email|password|label|spoof_email|security`

### 2. Load Recipients

Navigate to the Recipients tab:
1. Select Channel: Email or SMS
2. For SMS: Select Country and Carrier
3. Upload a file or paste your list

Email format: `email@domain.com` or `email@domain.com,Name`
SMS format: `6465386464` (10-digit phone numbers)

### 3. Create a Campaign

Navigate to the Compose tab:
1. Enter Campaign Name and Subject Line
2. Write your message (Plain Text or HTML)
3. Choose Channel (Email or SMS)
4. Optional: Schedule send time
5. Click "Create & Launch Campaign"

### 4. Monitor Campaigns

Navigate to the Campaigns tab:
- View all campaigns with status and progress
- Click "Watch" to see live send logs
- Click "Export" to download CSV results
- Click "Stop" to halt a running campaign

### 5. Track Performance

Navigate to the Analytics tab:
- View total opens and clicks
- See average open and click rates
- Identify best performing campaigns

### 6. Manage Settings

Navigate to the Settings tab:
- Adjust concurrency, delays, and retries
- Configure sender identity (From Name, From Address, Reply-To)
- Set physical address for compliance
- Enable/disable unsubscribe footer
- Configure tracking base URL

## Quick Start Commands

### Windows
```
# Install dependencies
pip install Flask==2.3.3 flask-cors==4.0.1

# Create directories
mkdir templates uploads reports

# Run as Administrator
python app.py

# Access
http://localhost:80/app
```

### Linux/Mac
```
# Install dependencies
pip install Flask==2.3.3 flask-cors==4.0.1

# Create directories
mkdir -p templates uploads reports

# Run with sudo (for port 80)
sudo python app.py

# Access
http://localhost:80/app
```

### Alternative Port (if port 80 is in use)
Edit app.py and change:
```python
app.run(debug=True, host='0.0.0.0', port=80, threaded=True)
```
to
```python
app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
```
Then access: http://localhost:5000/app

## Batch Files (Windows)

### start.bat
Creates directories, installs dependencies, and starts the application.

### install.bat
Installs dependencies and creates directories only.

### setup_and_start.bat
Complete setup with admin check and installation.

### start_silent.bat
Starts the application in the background.

### uninstall.bat
Removes CampaignForge files and data.

## Security Notes

### Authentication
- No built-in authentication (self-hosted)
- Implement your own auth layer if needed
- Consider using a reverse proxy with authentication

### Port Selection
- Default port 80 requires admin/sudo
- Change port in app.py if needed

### SMTP Security
- Supports TLS, SSL, and NONE security
- Use TLS for production
- Avoid NONE security except for testing

### Compliance
- Include physical address in emails
- Honor unsubscribe requests
- Only send to opted-in users
- Include unsubscribe footer

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
- Gmail requires App Password (not regular password)
- Some providers require API keys

### Connection Timeout
- Check firewall settings
- Verify SMTP server is accessible
- Increase timeout in settings

### Tracking Not Working
- Verify tracking_base_url in settings
- Use http://your-ip:80 for local network
- Check browser console for errors

### ModuleNotFoundError
```
pip install Flask==2.3.3 flask-cors==4.0.1
```

## Performance Recommendations

| Campaign Size | Concurrency | Delay (s) | Memory |
|---------------|-------------|-----------|--------|
| < 1,000       | 3           | 0.5       | 512MB  |
| 1,000 - 10,000| 5           | 0.5       | 1GB    |
| 10,000 - 50,000| 8          | 1.0       | 2GB    |
| > 50,000      | 10          | 1.5       | 4GB    |

## Deployment

### Bare Metal
```
# Install Python and pip
apt-get update && apt-get install python3 python3-pip

# Clone the application
git clone https://github.com/yourusername/campaignforge.git
cd campaignforge

# Install dependencies
pip3 install -r requirements.txt

# Create directories
mkdir -p templates uploads reports

# Copy template files
cp index.html templates/
cp app.html templates/
cp tracking.html templates/

# Run the application
sudo python3 app.py
```

### Docker
```
# Build Docker image
docker build -t campaignforge .

# Run container
docker run -d -p 80:80 --name campaignforge campaignforge
```

### Nginx Reverse Proxy
```
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Files Structure

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

## License

This software is provided as-is without warranty.

## Support

For issues and feature requests, please open an issue in the repository.