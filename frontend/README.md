# フロントエンド

Xタグスクレイパーのフロントエンドアプリケーションです。

## セットアップ

```bash
npm install
```

## 開発サーバーの起動

```bash
npm run dev
```

ブラウザで [http://localhost:3000](http://localhost:3000) を開きます。

## 環境変数

`.env.local` ファイルを作成して、以下の環境変数を設定してください:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

本番環境では、Vercelの環境変数設定で `NEXT_PUBLIC_API_BASE_URL` をバックエンドAPIのURLに設定してください。

## ビルド

```bash
npm run build
npm start
```

## デプロイ

Vercelにデプロイする場合:

1. Vercelにプロジェクトをインポート
2. ルートディレクトリを `frontend` に設定
3. 環境変数 `NEXT_PUBLIC_API_BASE_URL` をバックエンドAPIのURLに設定
