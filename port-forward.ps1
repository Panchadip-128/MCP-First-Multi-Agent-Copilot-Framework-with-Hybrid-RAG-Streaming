# WSL2 Port Forwarding Script
# Run this in PowerShell as Administrator

# Get WSL2 IP address
$wslIp = (wsl hostname -I).Trim()
Write-Host "WSL2 IP: $wslIp"

# Forward ports
$ports = @(3000, 8000, 8080)

foreach ($port in $ports) {
    Write-Host "Forwarding port $port..."
    
    # Remove existing rule if it exists
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null
    
    # Add new rule
    netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=$wslIp
}

Write-Host "`nPort forwarding configured!"
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend: http://localhost:8000"
Write-Host "Weaviate: http://localhost:8080"

# Show current rules
Write-Host "`nActive port forwarding rules:"
netsh interface portproxy show all
