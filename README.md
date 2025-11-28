# X タグスクレイパー

X（旧Twitter）のハッシュタグ検索ツイートを収集するWebアプリケーションです。

## 構成

- **フロントエンド**: Next.js (Vercelでデプロイ)
- **バックエンド**: FastAPI (Railway/Renderでデプロイ)
- **セッション取得ツール**: Python実行ファイル

## セットアップ

### 1. セッション取得ツール

ユーザーがXにログインし、セッション情報を取得するためのツールです。

```bash
cd session_extractor
pip install -r requirements.txt
playwright install chromium
python extract_session.py
```

実行ファイルを作成する場合:

```bash
pip install pyinstaller
python build.py
```

### 2. バックエンドAPI

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload
```

### 3. フロントエンド

```bash
cd frontend
npm install
npm run dev
```

環境変数を設定:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## デプロイ

### Vercel（フロントエンド）

1. Vercelにプロジェクトをインポート
2. ルートディレクトリを `frontend` に設定
3. 環境変数 `NEXT_PUBLIC_API_BASE_URL` を設定

### Railway/Render（バックエンド）

#### Railway

1. Railwayにプロジェクトをインポート
2. `backend` ディレクトリをルートとして設定
3. Dockerfileを使用してデプロイ

#### Render

1. Renderに新しいWebサービスを作成
2. `backend` ディレクトリをルートとして設定
3. ビルドコマンド: `pip install -r requirements.txt && playwright install chromium && playwright install-deps chromium`
4. スタートコマンド: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## 使用方法

1. セッション取得ツールを実行し、`twitter_state.json` を生成
2. Webアプリケーションにアクセス
3. `twitter_state.json` をアップロード
4. ハッシュタグ、期間、取得件数を入力
5. ツイート収集を開始
6. 完了後、CSVファイルをダウンロード

## 注意事項

- セッション情報は機密情報です。HTTPSを使用してください
- Playwrightのヘッドレスブラウザはメモリを多く消費します
- バックエンドのリソース設定に注意してください

