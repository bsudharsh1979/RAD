#!/bin/bash
set -euo pipefail
: "${NEXT_PUBLIC_API_BASE:?NEXT_PUBLIC_API_BASE must be set to bake the Next standalone build.}"
cd /web
npm ci
export MODAL_WEB_BUILD=1 NEXT_TELEMETRY_DISABLED=1
npm run build
mkdir -p /web/.next/standalone/.next
cp -a /web/.next/static /web/.next/standalone/.next/static
if [ -d /web/public ]; then
  cp -a /web/public /web/.next/standalone/public
fi
ls -la /web/.next/standalone
test -f /web/.next/standalone/server.js || test -f /web/.next/standalone/apps/web/server.js
