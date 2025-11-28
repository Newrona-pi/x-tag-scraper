# バックエンドAPI

XタグスクレイパーのバックエンドAPIです。

## セットアップ

```bash
pip install -r requirements.txt
playwright install chromium
```

## 実行

```bash
uvicorn main:app --reload
```

## 環境変数

- `PORT`: サーバーポート（デフォルト: 8000）

## APIエンドポイント

- `POST /api/collect`: ツイート収集を開始
- `GET /api/status/{job_id}`: ジョブの状態を取得
- `GET /api/download/{job_id}`: CSVファイルをダウンロード

## デプロイ

### Railway

1. Railwayにプロジェクトをインポート
2. Dockerfileを使用してデプロイ

### Render

1. Renderに新しいWebサービスを作成
2. ビルドコマンド: `pip install -r requirements.txt && playwright install chromium && playwright install-deps chromium`
3. スタートコマンド: `uvicorn main:app --host 0.0.0.0 --port $PORT`

