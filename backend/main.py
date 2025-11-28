"""
FastAPIアプリケーションのメインエントリーポイント
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api.routes import router

# 出力ディレクトリを作成
os.makedirs("./output", exist_ok=True)

app = FastAPI(
    title="X Tag Scraper API",
    description="X（旧Twitter）のハッシュタグ検索ツイート収集API",
    version="1.0.0"
)

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターを登録
app.include_router(router)


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "X Tag Scraper API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """ヘルスチェックエンドポイント"""
    return {"status": "ok"}

