# Real PowerShell 7 cmdlets, running on Linux. Windows-only modules
# (ActiveDirectory, LocalAccounts, Get-Service, execution policy) are not
# available here, so those stay as knowledge questions rather than live tasks.
FROM mcr.microsoft.com/powershell:7.4-debian-12
RUN useradd -m -s /bin/bash agent
USER agent
WORKDIR /home/agent
