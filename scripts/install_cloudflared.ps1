<#
Install cloudflared on Windows.
This script tries to use Chocolatey if available; otherwise instructs manual install.
Run in an elevated PowerShell if you want Chocolatey install privileges.
#>

Write-Host "Installing cloudflared (or showing manual steps)..."

function Has-Command($name) {
    $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

if (Has-Command choco) {
    Write-Host "Chocolatey detected. Installing cloudflared..."
    choco install cloudflared -y
    Write-Host "Installed via choco. Run `cloudflared tunnel login` to authenticate."
} else {
    Write-Host "Chocolatey not found. Please install cloudflared manually:"
    Write-Host "  1. Visit: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/"
    Write-Host "  2. Download the Windows package and install."
    Write-Host "After installation, run: `cloudflared tunnel login`"
}

Write-Host "\nNext steps (after login):"
Write-Host "  cloudflared tunnel create rps-tunnel"
Write-Host "  (note the tunnel UUID, then create config at .cloudflared\config.yml)"
