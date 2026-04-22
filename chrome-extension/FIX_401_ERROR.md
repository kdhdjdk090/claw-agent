# 🔧 Fix: 401 API Error in Chrome Extension

## Problem
```
⚠ Cloud API error: API error: 401. Check your internet connection.
```

This means the Chrome extension doesn't have your API keys configured.

---

## ✅ QUICK FIX (2 Options)

### Option 1: Auto-Configure Script (Fastest - 30 seconds)

1. **Open Chrome Extensions Page**
   - Go to `chrome://extensions/`
   - Find "Claw Agent"
   - Click "Reload" icon (🔄)

2. **Open Claw Agent Side Panel**
   - Click the Claw Agent icon in toolbar
   - Side panel opens

3. **Open Developer Console**
   - Right-click anywhere in the side panel
   - Click "Inspect"
   - Console tab opens

4. **Run the Fix Script**
   - Open file: `claw-agent/chrome-extension/QUICK_FIX_API_KEYS.js`
   - Copy ALL the code
   - Paste into the Console
   - Press Enter

5. **Expected Output**
   ```
   🦞 Claw Agent - Auto-configuring API keys...
   
   ✅ SUCCESS! API keys configured:
   
      NVIDIA NIM Key: sk-or-v1-REDACTED...
      DashScope Key: sk-dd-REDACTED...
      Default Model: qwen3.5-397b-a17b
   
   🔄 Please RELOAD the extension...
   ```

6. **Reload Extension**
   - Go back to `chrome://extensions/`
   - Click reload on Claw Agent again
   - Close and reopen the side panel

7. **Test It**
   - Type: "What is 2+2?"
   - Should respond successfully ✅

---

### Option 2: Manual Configuration (Takes 2 minutes)

1. **Open Settings Page**
   - Right-click Claw Agent icon in toolbar
   - Click "Options"
   - Settings page opens

2. **Enter API Keys**
   
   **NVIDIA NIM API Key:**
   ```
   sk-or-v1-REDACTED
   ```
   
   **Alibaba DashScope API Key:**
   ```
   sk-dd-REDACTED
   ```

3. **Select Default Model**
   - Choose: `🏆 Qwen3.5+ 397B (Default - Most Powerful)`

4. **Save**
   - Click "Save Settings" button
   - Wait for success message

5. **Reload Extension**
   - Go to `chrome://extensions/`
   - Click reload on Claw Agent

6. **Test**
   - Open side panel
   - Type a query

---

## 🔍 Why This Happens

The Chrome extension stores API keys in `chrome.storage.sync` (separate from the main agent's `.env.local` file).

When you first install the extension, it has no API keys configured, so API calls return 401 (Unauthorized).

---

## ✅ Verification

After fixing, you should see:
- No 401 error message
- Model name displayed: `qwen3.5-397b-a17b`
- Successful responses to queries

---

## 🎯 Alternative: Use Without API Keys

The extension has **built-in shared API keys** that work without configuration. If you're still getting 401 errors after following the fix above, there might be a network issue.

**Check:**
1. Internet connection is active
2. Firewall isn't blocking `integrate.api.nvidia.com`
3. Extension has permission to access the internet

---

## 📚 Available Models

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| `qwen3.5-397b-a17b` | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | **Everything (Default)** |
| `qwen3-coder-480b` | ⚡⚡ | ⭐⭐⭐⭐⭐ | Coding tasks |
| `qwen3-max` | ⚡⚡ | ⭐⭐⭐⭐⭐ | Complex reasoning |
| `qwen-plus` | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Fast tasks |
| `qwen/qwen3.5-397b-a17b:free` | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | Free tier |

---

## 🐛 Troubleshooting

### Still Getting 401 After Fix?

1. **Check Storage**
   ```javascript
   // In console, run:
   chrome.storage.sync.get(['NVIDIA NIM_api_key', 'dashscope_api_key'], (result) => {
     console.log('Stored keys:', result);
   });
   ```
   Should show your keys (partially masked)

2. **Clear and Re-save**
   - Go to Options page
   - Clear both API key fields
   - Click Save
   - Re-enter keys
   - Click Save again

3. **Check Network**
   - Open DevTools → Network tab
   - Try a query
   - Look for failed requests to `integrate.api.nvidia.com`
   - Check error details

### Extension Not Loading?

1. Go to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Check for error messages under Claw Agent
4. Click "Reload" again
5. Check "View service worker" for errors

### Model Not Responding?

1. Check if model is available:
   ```javascript
   // In console
   fetch('https://integrate.api.nvidia.com/api/v1/models', {
     headers: { 'Authorization': 'Bearer YOUR_API_KEY' }
   }).then(r => r.json()).then(console.log);
   ```

2. Try a different model from the dropdown

---

## 📝 Notes

- API keys are stored **locally** in Chrome storage
- Keys never leave your browser except when calling the API
- You can use different keys for different Chrome profiles
- Free tier has rate limits but works great for testing

---

## 🎉 Success Indicators

You'll know it's working when:
- ✅ No red error messages
- ✅ Model name shows in status bar
- ✅ Queries get responses
- ✅ Token count increases
- ✅ Cost shows (even if FREE)

---

**Need more help?** Check `EXTENSIONS_UPDATE_SUMMARY.md` for complete documentation.
