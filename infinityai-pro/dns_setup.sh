#!/bin/bash

# InfinityAI.Pro DNS Setup Script for Hetzner API
# Automates DNS record creation for the domain

# Configuration - Update these values
API_TOKEN="6983RicsIssimNgJrwhFy8GQ3AUCvQsS"
ZONE_ID="YOUR_ZONE_ID_HERE"  # Get from Hetzner console or API
HETZNER_IP="YOUR_HETZNER_IP_HERE"  # Your Hetzner VPS IP

# Function to create A record
create_a_record() {
    local name=$1
    local value=$2
    local ttl=${3:-86400}

    curl -X POST "https://dns.hetzner.com/api/v1/records" \
         -H "Auth-API-Token: $API_TOKEN" \
         -H "Content-Type: application/json" \
         -d "{
             \"zone_id\": \"$ZONE_ID\",
             \"type\": \"A\",
             \"name\": \"$name\",
             \"value\": \"$value\",
             \"ttl\": $ttl
         }" | jq .
}

echo "Setting up DNS records for infinityai.pro..."

# Root domain
create_a_record "@" "$HETZNER_IP"

# WWW subdomain
create_a_record "www" "$HETZNER_IP"

# API subdomain
create_a_record "api" "$HETZNER_IP"

# AI service subdomains (for RunPod routing via Traefik)
create_a_record "sd" "$HETZNER_IP"
create_a_record "yolo" "$HETZNER_IP"
create_a_record "whisper" "$HETZNER_IP"

echo "DNS setup complete!"
echo "Records created:"
echo "- infinityai.pro -> $HETZNER_IP"
echo "- www.infinityai.pro -> $HETZNER_IP"
echo "- api.infinityai.pro -> $HETZNER_IP"
echo "- sd.infinityai.pro -> $HETZNER_IP"
echo "- yolo.infinityai.pro -> $HETZNER_IP"
echo "- whisper.infinityai.pro -> $HETZNER_IP"
echo ""
echo "Note: DNS propagation may take 5-30 minutes."