#!/usr/bin/env bash
set -euo pipefail

: "${TRANSFER_PUBLIC_KEY:?TRANSFER_PUBLIC_KEY is required}"

mkdir -p /home/transfer/.ssh /run/sshd
chmod 700 /home/transfer/.ssh
printf 'restrict,command="/usr/local/bin/managed-rsync-wrapper" %s\n' "${TRANSFER_PUBLIC_KEY}" > /home/transfer/.ssh/authorized_keys
chmod 600 /home/transfer/.ssh/authorized_keys
chown -R transfer:transfer /home/transfer/.ssh /transfer
passwd -d transfer >/dev/null

ssh-keygen -A

cat > /etc/ssh/sshd_config <<'SSHD_CONFIG'
Port 2222
ListenAddress 0.0.0.0
HostKey /etc/ssh/ssh_host_ed25519_key
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile /home/transfer/.ssh/authorized_keys
PermitRootLogin no
PermitTTY no
X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
PermitTunnel no
GatewayPorts no
AllowUsers transfer
Subsystem sftp internal-sftp
SSHD_CONFIG

exec /usr/sbin/sshd -D -e