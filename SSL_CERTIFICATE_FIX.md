# SSL Certificate Error - Quick Fix

## Problem

You're seeing this error:
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: 
self-signed certificate in certificate chain
```

## Cause

The ArtsVision API server (av2.artsvision.net) is using a **self-signed SSL certificate**, which Python doesn't trust by default.

## Solution

### Quick Fix (For Testing)

1. **Open your `.env` file** in Notepad:
   ```
   notepad .env
   ```

2. **Add this line** (or change if it exists):
   ```
   ARTSVISION_VERIFY_SSL=false
   ```

3. **Save and close** the file

4. **Restart the application**:
   - Press `Ctrl+C` to stop
   - Run `run.bat` again

### Example `.env` File

```ini
# Flask Configuration
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///artsvision_monitors.db

# ArtsVision API
ARTSVISION_API_KEY=823264392764
ARTSVISION_API_URL=https://av2.artsvision.net/api/getdata

# SSL Certificate Verification
# Set to false if ArtsVision uses a self-signed certificate
ARTSVISION_VERIFY_SSL=false

# Polling Intervals (in seconds)
API_POLL_INTERVAL=1800
PROCESS_INTERVAL=60

# Theater Activation Windows (in minutes)
PRE_SHOW_MINUTES=30
POST_SHOW_MINUTES=60

# Display Settings
MAX_NEXT_EVENTS=6
```

## What This Does

Setting `ARTSVISION_VERIFY_SSL=false` tells the application to:
- Skip SSL certificate verification
- Accept the self-signed certificate
- Still use HTTPS encryption (but without verification)

## Expected Output

After the fix, you'll see this warning on startup:
```
======================================================================
SSL CERTIFICATE VERIFICATION IS DISABLED
This is INSECURE and should only be used for testing
with self-signed certificates on trusted networks!
======================================================================
```

Then it should work normally:
```
Discovering ArtsVision API schema...
Found 47 entities
Event entity discovered with 156 fields
Polling ArtsVision API...
Received 15 events from API
```

## Security Notes

### ⚠️ Is This Safe?

**For internal/corporate networks with self-signed certificates:**
- ✅ **YES** - Common and acceptable
- ✅ Your data is still encrypted (HTTPS)
- ✅ You're on a trusted internal network
- ✅ The server is controlled by your organization

**For public/untrusted networks:**
- ❌ **NO** - Don't use this setting
- ❌ Vulnerable to man-in-the-middle attacks
- ❌ Cannot verify server identity

### 🔒 Why Self-Signed Certificates?

Organizations often use self-signed certificates for internal servers because:
- Internal servers don't need public certificate authorities
- Cost savings (no need to purchase certificates)
- Full control over certificate management
- Common in corporate/enterprise environments

### Better Long-Term Solution

If you want proper SSL verification, ask your IT department to:

1. **Install the root CA certificate** on your computer
   - This makes Python trust your organization's certificates
   - More secure than disabling verification

2. **Use a proper SSL certificate** on the ArtsVision server
   - From a public CA like Let's Encrypt
   - Or install your organization's root CA

## Troubleshooting

### Still getting SSL errors?

**Double-check your `.env` file:**
```cmd
type .env
```

Look for this line:
```
ARTSVISION_VERIFY_SSL=false
```

**Make sure it's lowercase `false`** (not `False` or `FALSE`)

### Warning doesn't appear?

The setting might not be loading. Try:

1. Stop the application (`Ctrl+C`)
2. Delete the `.env` file
3. Copy `.env.example` to `.env`
4. Edit the new `.env` file
5. Run again

### Application won't start?

Check for typos in `.env`:
```
ARTSVISION_VERIFY_SSL=false
```

NOT:
```
ARTSVISION_VERIFY_SSL = false  # (extra spaces)
ARTSVISION_VERIFY_SSL='false'  # (quotes)
ARTSVISION_VERIFY_SSL=False    # (capital F)
```

## Alternative Solutions

### Option 1: Install ArtsVision Root Certificate

If your IT department provides a root certificate:

```cmd
# Install certificate to Windows trust store
# Then set back to true:
ARTSVISION_VERIFY_SSL=true
```

### Option 2: Use HTTP Instead (If Available)

If ArtsVision supports HTTP (not recommended):

```ini
ARTSVISION_API_URL=http://av2.artsvision.net/api/getdata
ARTSVISION_VERIFY_SSL=true
```

### Option 3: Certificate Bundle File

If you have the certificate file:

```python
# In api_poller.py, use:
verify='/path/to/certificate.crt'
# instead of:
verify=False
```

## Verification

After applying the fix, you should see:

1. **Warning on startup** (showing SSL verification is disabled)
2. **Successful API calls**:
   ```
   Fetching entity names from API...
   Found 47 entities
   ```
3. **Dashboard works** at http://localhost:5000
4. **Locations appear** in dropdown
5. **No more SSL errors** in the logs

## Questions?

**Q: Is this a bug in the application?**
A: No, this is expected behavior when connecting to servers with self-signed certificates.

**Q: Will this affect security?**
A: Only if you're on an untrusted network. On your corporate network, it's fine.

**Q: Should I use this in production?**
A: On internal corporate networks with self-signed certificates, yes. On public networks, no.

**Q: Can I trust the ArtsVision server?**
A: If it's your organization's server on your corporate network, yes.

**Q: Why does the Lua version work without this?**
A: The Lua version might not verify SSL certificates by default, or uses different SSL libraries.

---

## Summary

**One-Line Fix:**
Add `ARTSVISION_VERIFY_SSL=false` to your `.env` file and restart.

**Why:**
ArtsVision uses a self-signed SSL certificate that Python doesn't trust by default.

**Safe?:**
Yes, on your internal corporate network. No, on untrusted public networks.

**Next Steps:**
1. Edit `.env`
2. Add `ARTSVISION_VERIFY_SSL=false`
3. Restart application
4. Enjoy! 🎉
