#!/usr/bin/env bash
set -euo pipefail

TARGET_HOST="${TARGET_HOST:-root@172.236.110.179}"
TARGET_DIR="${TARGET_DIR:-/opt/the-courter}"
ENV_SOURCE="${ENV_SOURCE:-.env.test}"

if [[ ! -f "${ENV_SOURCE}" ]]; then
  echo "${ENV_SOURCE} is required in the repo root before deployment."
  exit 1
fi

rsync -az --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude 'node_modules' \
  --exclude '.next' \
  --exclude '__pycache__' \
  ./ "${TARGET_HOST}:${TARGET_DIR}/"

ssh "${TARGET_HOST}" "mkdir -p ${TARGET_DIR}"
rsync -az "${ENV_SOURCE}" "${TARGET_HOST}:${TARGET_DIR}/.env.production"

ssh "${TARGET_HOST}" "cd ${TARGET_DIR} && \
  apt-get update && \
  apt-get install -y python3-venv && \
  python3 -m venv .venv && \
  .venv/bin/pip install --upgrade pip && \
  .venv/bin/pip install ."

ssh "${TARGET_HOST}" "cp ${TARGET_DIR}/infra/systemd/courter-api.service /etc/systemd/system/courter-api.service && \
  cp ${TARGET_DIR}/infra/systemd/courter-telegram-bot.service /etc/systemd/system/courter-telegram-bot.service && \
  systemctl daemon-reload && \
  systemctl enable courter-api courter-telegram-bot && \
  systemctl restart courter-api courter-telegram-bot"

ssh "${TARGET_HOST}" "systemctl status --no-pager courter-api courter-telegram-bot"
