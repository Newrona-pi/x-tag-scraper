# X セッション取得ツール

このツールは、X（旧Twitter）のログインセッション情報を取得するためのツールです。

## 使用方法

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 実行

```bash
python extract_session.py
```

### 3. 実行ファイルのビルド（オプション）

実行ファイルを作成する場合:

```bash
pip install pyinstaller
python build.py
```

`dist/x-session-extractor.exe` が生成されます。

## 動作説明

1. ツールを実行すると、自動操作用のブラウザが起動します
2. Xのログイン画面が表示されます
3. ユーザーは通常通りXにログインします
4. ログインが完了したら、ブラウザを閉じます
5. ブラウザが閉じられたタイミングで、セッション情報が `twitter_state.json` として保存されます

## 出力ファイル

`twitter_state.json` には以下の情報が含まれます:

- `cookies`: ブラウザのクッキー情報
- `localStorage`: ローカルストレージの内容
- `sessionStorage`: セッションストレージの内容

このファイルを、XタグスクレイパーのWebアプリケーションにアップロードすることで、ログイン済み状態でツイートを収集できます。

