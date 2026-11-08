#!/usr/bin/env bash
# Creates a small Azure VM that runs n8n (Docker) behind Caddy with automatic HTTPS.
# Usage:  ./deploy-azure.sh <dns-label> [region]
# Result: https://<dns-label>.<region>.cloudapp.azure.com
set -euo pipefail

LABEL="${1:?usage: deploy-azure.sh <dns-label> [region]}"
REGION="${2:-southafricanorth}"
RG="ray-n8n-rg"
VM="ray-n8n-vm"
DOMAIN="$LABEL.$REGION.cloudapp.azure.com"
MYIP="$(curl -s https://api.ipify.org)"
KEY="$(openssl rand -hex 24)"

echo "Encryption key (store safely): $KEY"
sed -e "s/__DOMAIN__/$DOMAIN/" -e "s/__KEY__/$KEY/" "$(dirname "$0")/cloud-init.yaml" > /tmp/cloud-init.rendered.yaml

az group create -n "$RG" -l "$REGION" -o none
az vm create -g "$RG" -n "$VM" -l "$REGION" \
  --image Ubuntu2404 --size Standard_B2als_v2 \
  --storage-sku StandardSSD_LRS --os-disk-size-gb 30 \
  --admin-username azureuser --ssh-key-values ~/.ssh/id_rsa.pub \
  --public-ip-sku Standard --public-ip-address-dns-name "$LABEL" \
  --custom-data /tmp/cloud-init.rendered.yaml --nsg-rule NONE -o table

NSG="${VM}NSG"
az network nsg rule create -g "$RG" --nsg-name "$NSG" -n https --priority 100 --destination-port-ranges 80 443 --access Allow --protocol Tcp -o none
az network nsg rule create -g "$RG" --nsg-name "$NSG" -n ssh-admin --priority 110 --destination-port-ranges 22 --source-address-prefixes "$MYIP" --access Allow --protocol Tcp -o none

echo "Done. n8n will be live in ~3 minutes at: https://$DOMAIN"
