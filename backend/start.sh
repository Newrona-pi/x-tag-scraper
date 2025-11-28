#!/bin/bash
# バックエンド起動スクリプト

# Playwrightブラウザをインストール（初回のみ）
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    playwright install chromium
    playwright install-deps chromium
fi

# アプリケーションを起動
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

