
import asyncio
import json
import os
import sys
import shutil
import zipfile
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright

# PlaywrightのChromiumリビジョン（バージョンに合わせて更新が必要）
# Playwright 1.40.0に対応するChromiumのリビジョン
CHROMIUM_REVISION = "1091" 
DOWNLOAD_URL = f"https://playwright.azureedge.net/builds/chromium/{CHROMIUM_REVISION}/chromium-win64.zip"

def get_browser_path():
    """ローカルのブラウザ実行ファイルのパスを取得"""
    base_dir = Path(os.getcwd())
    browser_dir = base_dir / "bin" / f"chromium-{CHROMIUM_REVISION}" / "chrome-win"
    executable_path = browser_dir / "chrome.exe"
    return executable_path

def download_progress_hook(count, block_size, total_size):
    """ダウンロードの進捗を表示"""
    percent = int(count * block_size * 100 / total_size)
    sys.stdout.write(f"\rダウンロード中... {percent}% ({count * block_size / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB)")
    sys.stdout.flush()

def setup_browser():
    """ブラウザのセットアップ（ダウンロードと展開）"""
    executable_path = get_browser_path()
    
    if executable_path.exists():
        return str(executable_path)
    
    print("\nブラウザが見つかりません。セットアップを開始します...")
    print(f"ダウンロード先: {DOWNLOAD_URL}")
    
    # binディレクトリの作成
    bin_dir = Path(os.getcwd()) / "bin"
    bin_dir.mkdir(exist_ok=True)
    
    zip_path = bin_dir / "chromium.zip"
    
    try:
        # ダウンロード
        print("ブラウザをダウンロードしています...")
        urllib.request.urlretrieve(DOWNLOAD_URL, zip_path, download_progress_hook)
        print("\nダウンロード完了。")
        
        # 展開
        print("ファイルを展開しています...")
        extract_dir = bin_dir / f"chromium-{CHROMIUM_REVISION}"
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        print("展開完了。")
        
        # zipファイルの削除
        os.remove(zip_path)
        
        if executable_path.exists():
            print("ブラウザのセットアップが完了しました。")
            return str(executable_path)
        else:
            print("エラー: ブラウザの実行ファイルが見つかりません。")
            return None
            
    except Exception as e:
        print(f"\nセットアップ中にエラーが発生しました: {e}")
        if zip_path.exists():
            os.remove(zip_path)
        return None

async def extract_session():
    """Xのログインセッションを取得してJSONファイルに保存"""
    print("=" * 60)
    print("X セッション取得ツール（完全自立型）")
    print("=" * 60)
    
    # ブラウザのセットアップ
    executable_path = setup_browser()
    if not executable_path:
        print("ブラウザの準備に失敗しました。終了します。")
        input("終了するにはEnterキーを押してください...")
        return

    print("\nブラウザが起動します。")
    print("Xのログイン画面でログインしてください。")
    print("ログインが完了したら、ブラウザを閉じてください。")
    print("=" * 60)
    
    print("Starting async_playwright...")
    try:
        async with async_playwright() as p:
            print("async_playwright started.")
            # 一時的なユーザーデータディレクトリを使用
            temp_dir = Path("./.temp_session")
            temp_dir.mkdir(exist_ok=True)
            
            print(f"Launching browser from: {executable_path}")
            try:
                browser = await p.chromium.launch_persistent_context(
                    user_data_dir=str(temp_dir),
                    executable_path=executable_path, # ローカルのブラウザを指定
                    headless=False,
                    viewport=None,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                    ],
                )
            except Exception as e:
                print(f"ブラウザの起動に失敗しました (launch): {e}")
                raise e
            
            try:
                page = await browser.new_page()
                
                # ログインページに移動
                print("\nログインページを開いています...")
                await page.goto("https://x.com/login")
                
                # ログイン完了を待つ（URLが/homeになるまで）
                print("\nログインを待機しています...")
                try:
                    await page.wait_for_url("https://x.com/home", timeout=0)
                    print("ログインが完了しました！")
                except Exception as e:
                    print(f"エラー: {e}")
                    print("ログインが完了していない可能性があります。")
                    await browser.close()
                    return
                
                # ホームページに移動してセッション情報を取得
                await page.goto("https://x.com/home")
                await asyncio.sleep(2)  # ページの読み込みを待つ
                
                print("\nセッション情報を取得しています...")
                
                # クッキーを取得
                cookies = await browser.cookies()
                
                # ローカルストレージとセッションストレージを取得
                localStorage = await page.evaluate("() => { return JSON.parse(JSON.stringify(localStorage)); }")
                sessionStorage = await page.evaluate("() => { return JSON.parse(JSON.stringify(sessionStorage)); }")
                
                # セッション情報を辞書にまとめる
                session_data = {
                    "cookies": cookies,
                    "localStorage": localStorage,
                    "sessionStorage": sessionStorage
                }
                
                # JSONファイルに保存
                output_file = Path("twitter_state.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                
                print(f"\nセッション情報を {output_file} に保存しました。")
                print("=" * 60)
                
            finally:
                # ブラウザを閉じる
                try:
                    await browser.close()
                except:
                    pass
                
                # 一時ディレクトリを削除
                if temp_dir.exists():
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(extract_session())
    except KeyboardInterrupt:
        print("\n\n処理が中断されました。")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
    finally:
        input("\n終了するにはEnterキーを押してください...")
