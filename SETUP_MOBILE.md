# Access from Mobile Device

## Quick Setup

### Step 1: Find Your Computer's IP Address

**On Mac/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```
Look for something like `192.168.1.100` or `10.0.0.5`

**On Windows:**
```bash
ipconfig
```
Look for "IPv4 Address" under your network adapter (usually `192.168.x.x`)

### Step 2: Update config.js

Open `config.js` and set your IP:
```javascript
window.API_BASE_URL = 'http://YOUR_IP_ADDRESS:8000';
// Example: window.API_BASE_URL = 'http://192.168.1.100:8000';
```

### Step 3: Start API Server (Important!)

The API server MUST be running on `0.0.0.0` (all interfaces), not just `127.0.0.1`:

```bash
cd smartplanner
source venv/bin/activate
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

**Important:** Use `--host 0.0.0.0` not `--host 127.0.0.1`

### Step 4: Start Web Server

```bash
cd smartplanner
python3 -m http.server 8080
```

### Step 5: Access from Phone

1. Make sure your phone is on the **same WiFi network** as your computer
2. Open browser on phone
3. Go to: `http://YOUR_IP_ADDRESS:8080/index.html`
   - Example: `http://192.168.1.100:8080/index.html`

## Troubleshooting

### Can't connect from phone?
1. **Check firewall**: Make sure ports 8000 and 8080 are open
   - Mac: System Settings → Network → Firewall
   - Windows: Windows Defender Firewall

2. **Check IP address**: Make sure you're using the correct IP
   - It should start with `192.168.` or `10.0.`
   - NOT `127.0.0.1` (that's localhost only)

3. **Check network**: Both devices must be on same WiFi

4. **Check API server**: Make sure it's running with `--host 0.0.0.0`

### Test API from phone:
Open in phone browser: `http://YOUR_IP:8000/`
Should see: `{"status":"ok","message":"API is running"}`

### Quick Test Script

Run this to get your setup info:
```bash
IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo "Your IP: $IP"
echo "API URL: http://$IP:8000"
echo "Web URL: http://$IP:8080/index.html"
```
