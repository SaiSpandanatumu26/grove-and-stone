#!/usr/bin/env bash
set -euo pipefail
node -e 'const u = new URL(process.env.EXPO_PUBLIC_API_URL); if (u.protocol !== "https:" || u.username || u.password || u.search || u.hash || u.pathname.replace(/\/$/, "") !== "/api/v1") throw new Error("Set EXPO_PUBLIC_API_URL to the deployed HTTPS Flask URL ending in /api/v1.");'
cd mobile
npm ci
node --dns-result-order=ipv4first node_modules/expo/bin/cli export --platform web --output-dir dist
