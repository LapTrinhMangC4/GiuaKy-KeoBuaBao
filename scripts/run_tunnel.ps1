<#
Run a named cloudflared tunnel. Usage: .\run_tunnel.ps1 -Name rps-tunnel
Requires that you have created a tunnel and a config at .cloudflared\config.yml
#>

param(
    [string]$Name = "rps-tunnel"
)

Write-Host "Running cloudflared tunnel: $Name"

if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "cloudflared not found in PATH. Run scripts\install_cloudflared.ps1 first or install manually."
    exit 1
}

cloudflared tunnel run $Name
