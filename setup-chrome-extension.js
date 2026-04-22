#!/usr/bin/env node

/**
 * 🦞 Claw Agent - Automatic Chrome Extension Setup
 * 
 * This script automatically configures the Chrome extension with API keys.
 * 
 * USAGE:
 *   node setup-chrome-extension.js
 * 
 * What it does:
 * 1. Reads API keys from .env.local
 * 2. Creates a Chrome extension loader script
 * 3. Provides instructions to load keys into Chrome
 */

const fs = require('fs');
const path = require('path');

console.log('🦞 Claw Agent - Automatic Chrome Extension Setup\n');
console.log('='.repeat(50));

// Read .env.local
const envPath = path.join(__dirname, '.env.local');
console.log(`\n📖 Reading ${envPath}...`);

if (!fs.existsSync(envPath)) {
  console.error('❌ .env.local not found!');
  console.log('Please create .env.local with your API keys first.');
  process.exit(1);
}

const envContent = fs.readFileSync(envPath, 'utf-8');
const envVars = {};

envContent.split('\n').forEach(line => {
  const match = line.match(/^([^=#]+)=(.*)$/);
  if (match) {
    const key = match[1].trim();
    let value = match[2].trim();
    // Remove quotes
    value = value.replace(/^["']|["']$/g, '');
    envVars[key] = value;
  }
});

const NVIDIA_KEY = envVars.NVIDIA_API_KEY || envVars.NIM_API_KEY || '';
const DASHSCOPE_KEY = envVars.DASHSCOPE_API_KEY || '';

console.log('✅ Found API keys:');
console.log(`   NVIDIA:    ${NVIDIA_KEY ? NVIDIA_KEY.substring(0, 15) + '...' : '❌ Not found'}`);
console.log(`   DashScope:  ${DASHSCOPE_KEY ? DASHSCOPE_KEY.substring(0, 15) + '...' : '❌ Not found'}`);

// Create auto-load script
const loaderScript = `// 🦞 Claw Agent - Auto-Load API Keys
// Generated automatically by setup-chrome-extension.js
// 
// INSTRUCTIONS:
// 1. Open Chrome extension side panel (click Claw icon)
// 2. Right-click → Inspect
// 3. Console tab
// 4. Paste this ENTIRE script
// 5. Press Enter
// 6. Reload extension

(async function autoLoadApiKeys() {
  console.log('🦞 Loading API keys from .env.local...\\n');
  
  const CONFIG = {
    nvidia_api_key: '${NVIDIA_KEY}',
    dashscope_api_key: '${DASHSCOPE_KEY}',
    current_model: 'qwen3.5-397b-a17b'
  };
  
  try {
    await chrome.storage.sync.set(CONFIG);
    
    console.log('✅ SUCCESS! API keys configured:\\n');
    console.log('   NVIDIA Key:    ' + CONFIG.nvidia_api_key.substring(0, 15) + '...');
    console.log('   DashScope Key:  ' + CONFIG.dashscope_api_key.substring(0, 15) + '...');
    console.log('   Default Model:  ' + CONFIG.current_model);
    console.log('\\n🔄 RELOAD the extension now:');
    console.log('   1. Go to chrome://extensions/');
    console.log('   2. Click reload on Claw Agent');
    console.log('   3. Open side panel and test!\\n');
    
    chrome.runtime.sendMessage({ type: 'settings-updated', ...CONFIG });
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
})();
`;

const loaderPath = path.join(__dirname, 'chrome-extension', 'AUTO_LOAD_KEYS.local.js');
fs.writeFileSync(loaderPath, loaderScript);
console.log(`\n💾 Created: ${loaderPath}`);

// Create PowerShell script for Windows
const psScript = `# 🦞 Claw Agent - Chrome Extension Auto-Setup (PowerShell)
# Run this script to automatically configure Chrome extension

Write-Host "🦞 Claw Agent - Chrome Extension Setup" -ForegroundColor Green
Write-Host "=" * 50
Write-Host ""

$chromePath = "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\Default"
$extensionPath = "$PSScriptRoot\\chrome-extension"

Write-Host "📖 Reading API keys from .env.local..."
$envContent = Get-Content "$PSScriptRoot\\.env.local" -Raw
$nvidiaKey = ""
$dashscopeKey = ""

foreach ($line in $envContent -split "\\n") {
    if ($line -match '^(NVIDIA_API_KEY|NIM_API_KEY)=(.*)$') {
        $nvidiaKey = $matches[2].Trim('"', "'")
    }
    if ($line -match '^DASHSCOPE_API_KEY=(.*)$') {
        $dashscopeKey = $matches[1].Trim('"', "'")
    }
}

Write-Host "✅ Found API keys:"
Write-Host "   NVIDIA:    $($nvidiaKey.Substring(0, [Math]::Min(15, $nvidiaKey.Length)))..."
Write-Host "   DashScope:  $($dashscopeKey.Substring(0, [Math]::Min(15, $dashscopeKey.Length)))..."
Write-Host ""

Write-Host "📋 INSTRUCTIONS:" -ForegroundColor Yellow
Write-Host "1. Open Chrome and go to: chrome://extensions/"
Write-Host "2. Enable 'Developer mode' (top right)"
Write-Host "3. Find 'Claw Agent' and click 'Reload'"
Write-Host "4. Click the Claw Agent icon to open side panel"
Write-Host "5. Right-click in the panel → Inspect"
Write-Host "6. Go to Console tab"
Write-Host "7. Open file: AUTO_LOAD_KEYS.local.js"
Write-Host "8. Copy ALL content and paste into Console"
Write-Host "9. Press Enter"
Write-Host "10. Reload extension again"
Write-Host ""
Write-Host "✅ Done! The extension will now work with your API keys." -ForegroundColor Green
`;

const psPath = path.join(__dirname, 'setup-chrome-extension.ps1');
fs.writeFileSync(psPath, psScript);
console.log(`💾 Created: ${psPath}`);

// Create batch script for Windows
const batScript = `@echo off
REM 🦞 Claw Agent - Chrome Extension Setup (Batch)
echo 🦞 Claw Agent - Chrome Extension Setup
echo ==================================================
echo.
echo 📋 INSTRUCTIONS:
echo 1. Open Chrome and go to: chrome://extensions/
echo 2. Enable 'Developer mode' (top right)
echo 3. Find 'Claw Agent' and click 'Reload'
echo 4. Click the Claw Agent icon to open side panel
echo 5. Right-click in the panel → Inspect
echo 6. Go to Console tab
echo 7. Open file: chrome-extension\AUTO_LOAD_KEYS.js
echo 8. Copy ALL content and paste into Console
echo 9. Press Enter
echo 10. Reload extension again
echo.
echo ✅ The AUTO_LOAD_KEYS.js file has been generated with your API keys.
echo.
pause
`;

const batPath = path.join(__dirname, 'setup-chrome-extension.bat');
fs.writeFileSync(batPath, batScript);
console.log(`💾 Created: ${batPath}`);

// Print summary
console.log('\n' + '='.repeat(50));
console.log('\n🎉 SETUP COMPLETE!\n');
console.log('📁 Files created:');
console.log('   - chrome-extension/AUTO_LOAD_KEYS.local.js (contains your local API keys)');
console.log('   - setup-chrome-extension.ps1 (PowerShell helper)');
console.log('   - setup-chrome-extension.bat (Batch helper)');
console.log('');
console.log('🚀 NEXT STEP - Run ONE of these:');
console.log('');
console.log('   Option 1 (PowerShell):');
console.log('     .\\setup-chrome-extension.ps1');
console.log('');
console.log('   Option 2 (Batch):');
console.log('     .\\setup-chrome-extension.bat');
console.log('');
console.log('   Option 3 (Manual):');
console.log('     1. Open chrome-extension/AUTO_LOAD_KEYS.local.js');
console.log('     2. Copy all content');
console.log('     3. Paste into Chrome extension console');
console.log('     4. Press Enter');
console.log('');
console.log('✅ After running: Reload extension and test!');
console.log('');
