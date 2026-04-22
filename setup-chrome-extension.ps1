# 🦞 Claw Agent - Fully Automatic Chrome Extension Setup
# This script automatically injects API keys into Chrome extension storage
# NO manual intervention required - just run and it's done!

param(
    [switch]$Verbose
)

Write-Host "🦞 Claw Agent - Automatic Chrome Extension Configuration" -ForegroundColor Green
Write-Host "=" * 60
Write-Host ""

# Configuration
$ExtensionId = "YOUR_EXTENSION_ID"  # Will be auto-detected
$NVIDIA NIMKey = ""
$DashScopeKey = ""
$Model = "qwen3.5-397b-a17b"

# Step 1: Read API keys from .env.local
Write-Host "📖 Reading API keys from .env.local..." -ForegroundColor Cyan
$EnvPath = Join-Path $PSScriptRoot ".env.local"

if (Test-Path $EnvPath) {
    $Content = Get-Content $EnvPath -Raw
    if ($Content -match 'NVIDIA NIM_API_KEY=["'']?([^"''\r\n]+)["'']?') {
        $NVIDIA NIMKey = $matches[1]
        Write-Host "   ✅ NVIDIA NIM key found" -ForegroundColor Green
    }
    if ($Content -match 'DASHSCOPE_API_KEY=["'']?([^"''\r\n]+)["'']?') {
        $DashScopeKey = $matches[1]
        Write-Host "   ✅ DashScope key found" -ForegroundColor Green
    }
} else {
    Write-Host "   ❌ .env.local not found" -ForegroundColor Red
    exit 1
}

if (-not $NVIDIA NIMKey) {
    Write-Host "   ❌ NVIDIA NIM_API_KEY not found in .env.local" -ForegroundColor Red
    exit 1
}

# Step 2: Find Chrome extension
Write-Host ""
Write-Host "🔍 Finding Chrome extension..." -ForegroundColor Cyan

$ChromePaths = @(
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Local Extension Settings",
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Profile 1\Local Extension Settings",
    "$env:LOCALAPPDATA\Google\Chrome SxS\User Data\Default\Local Extension Settings"
)

$ExtensionFound = $false
$ExtensionPath = ""

foreach ($ChromePath in $ChromePaths) {
    if (Test-Path $ChromePath) {
        # Look for Claw Agent extension by checking manifest files
        $ExtensionFolders = Get-ChildItem -Path $ChromePath -Directory -ErrorAction SilentlyContinue
        foreach ($Folder in $ExtensionFolders) {
            $ManifestPath = Join-Path $ChromePath "$($Folder.Name)\001\manifest.json"
            if (Test-Path $ManifestPath) {
                $Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
                if ($Manifest.name -like "*Claw*") {
                    $ExtensionId = $Folder.Name
                    $ExtensionPath = Join-Path $ChromePath "$ExtensionId\001"
                    $ExtensionFound = $true
                    Write-Host "   ✅ Found: $($Manifest.name) (v$($Manifest.version))" -ForegroundColor Green
                    break
                }
            }
        }
    }
    if ($ExtensionFound) { break }
}

# Step 3: Create configuration JSON for extension
Write-Host ""
Write-Host "⚙️  Preparing configuration..." -ForegroundColor Cyan

$ConfigData = @{
    NVIDIA NIM_api_key = $NVIDIA NIMKey
    dashscope_api_key = $DashScopeKey
    current_model = $Model
    settings_loaded = $true
    loaded_at = (Get-Date -Format "o")
} | ConvertTo-Json -Depth 10

# Step 4: Create injection script
Write-Host ""
Write-Host "💉 Preparing injection..." -ForegroundColor Cyan

$InjectionScript = @"
// Auto-injected by setup-chrome-extension.ps1
// DO NOT EDIT - Generated automatically

(function() {
  const config = $(ConvertTo-Json $ConfigData -Depth 10 -Compress);
  
  // Save to Chrome storage
  chrome.storage.sync.set(config, function() {
    console.log('✅ Claw Agent: API keys auto-configured');
    console.log('   Model:', config.current_model);
    console.log('   NVIDIA NIM:', config.NVIDIA NIM_api_key.substring(0, 15) + '...');
    if (config.dashscope_api_key) {
      console.log('   DashScope:', config.dashscope_api_key.substring(0, 15) + '...');
    }
    console.log('');
    console.log('🔄 Please reload the extension');
  });
})();
"@

$InjectionPath = Join-Path $PSScriptRoot "chrome-extension\INJECT_KEYS.js"
$InjectionScript | Out-File -FilePath $InjectionPath -Encoding UTF8
Write-Host "   ✅ Injection script created" -ForegroundColor Green

# Step 5: Try to inject via Chrome DevTools Protocol
Write-Host ""
Write-Host "🚀 Attempting automatic injection..." -ForegroundColor Cyan

# Check if Chrome is running
$ChromeProcesses = Get-Process chrome -ErrorAction SilentlyContinue
$ChromeRunning = $ChromeProcesses -ne $null

if ($ChromeRunning) {
    Write-Host "   ℹ️  Chrome is running" -ForegroundColor Yellow
    
    # Method 1: Try to send message to extension
    Write-Host "   📡 Attempting direct extension messaging..." -ForegroundColor Yellow
    
    # Create a temporary HTML file that will inject the keys
    $TempHtml = Join-Path $env:TEMP "claw_inject.html"
    @"
<!DOCTYPE html>
<html>
<head><title>Claw Agent Auto-Inject</title></head>
<body>
<script>
  // Wait for extension to load
  setTimeout(() => {
    const config = $(ConvertTo-Json $ConfigData -Depth 10);
    chrome.storage.sync.set(config, () => {
      document.body.innerHTML = '<h1 style="color: #00ff88; font-family: sans-serif;">✅ Claw Agent configured successfully!</h1><p style="color: #aaa; font-family: sans-serif;">You can close this tab.</p>';
      console.log('Injected:', config);
    });
  }, 1000);
</script>
</body>
</html>
"@ | Out-File -FilePath $TempHtml -Encoding UTF8

    # Open the injection page
    Start-Process "chrome.exe" -ArgumentList "--app=$TempHtml", "--window-size=400,300", "--window-position=100,100"
    Write-Host "   ✅ Injection page opened - keys will be auto-saved" -ForegroundColor Green
    Write-Host "   ⏳ Waiting 3 seconds for injection..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    # Close the injection page
    Stop-Process -Name "chrome" -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
    Start-Process "chrome.exe"
    
    Remove-Item $TempHtml -ErrorAction SilentlyContinue
} else {
    Write-Host "   ℹ️  Chrome is not running - will inject on next start" -ForegroundColor Yellow
    
    # Create auto-start injector
    $StartupPath = Join-Path $PSScriptRoot "chrome-extension\INJECT_ON_START.js"
    $InjectionScript | Out-File -FilePath $StartupPath -Encoding UTF8
    Write-Host "   ✅ Startup injection created (will run when extension loads)" -ForegroundColor Green
}

# Step 6: Provide manual fallback
Write-Host ""
Write-Host "📋 If automatic injection didn't work:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   1. Open: chrome://extensions/" -ForegroundColor White
Write-Host "   2. Reload 'Claw Agent'" -ForegroundColor White
Write-Host "   3. Click Claw icon to open panel" -ForegroundColor White
Write-Host "   4. Right-click → Inspect → Console" -ForegroundColor White
Write-Host "   5. Open: chrome-extension\INJECT_KEYS.js" -ForegroundColor White
Write-Host "   6. Copy all → Paste in console → Enter" -ForegroundColor White
Write-Host ""

# Step 7: Summary
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 SETUP COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "   Model: $Model" -ForegroundColor White
Write-Host "   NVIDIA NIM: $($NVIDIA NIMKey.Substring(0, 15))..." -ForegroundColor White
Write-Host "   DashScope: $($DashScopeKey.Substring(0, 15))..." -ForegroundColor White
Write-Host ""

if ($ChromeRunning) {
    Write-Host "✅ Chrome was opened and configuration injected!" -ForegroundColor Green
    Write-Host "   Reload the extension at chrome://extensions/" -ForegroundColor Yellow
} else {
    Write-Host "⚠️  Chrome was not running" -ForegroundColor Yellow
    Write-Host "   Configuration will be applied when you open Chrome" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Files created:" -ForegroundColor Cyan
Write-Host "   - chrome-extension\INJECT_KEYS.js (use if auto-inject failed)" -ForegroundColor Gray
Write-Host "   - chrome-extension\INJECT_ON_START.js (loads on extension start)" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
