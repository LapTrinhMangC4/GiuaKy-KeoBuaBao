<#
Interactive helper: create .cloudflared\config.yml from template.
You need the tunnel UUID (from `cloudflared tunnel create NAME`) and your hostname.
#>

Param()

if (-not (Test-Path ".cloudflared")) {
    New-Item -ItemType Directory -Path ".cloudflared" | Out-Null
}

$tunnelId = Read-Host "Enter the tunnel UUID (from 'cloudflared tunnel create <name>')"
$hostname = Read-Host "Enter hostname to use (e.g. rps.example.com)"
$user = $env:USERNAME

$configPath = ".cloudflared\config.yml"

$content = @"
tunnel: $tunnelId
credentials-file: C:\Users\$user\\.cloudflared\$tunnelId.json
ingress:
  - hostname: $hostname
    service: tcp://localhost:5555
  - service: http_status:404
"@

Set-Content -Path $configPath -Value $content -Encoding UTF8
Write-Host "Created $configPath"
Write-Host "Review the file and then run: cloudflared tunnel run <tunnel-name>"
