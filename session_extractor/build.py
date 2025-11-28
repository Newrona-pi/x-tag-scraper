"""
PyInstallerを使用して実行ファイルをビルドするスクリプト
"""
import subprocess
import sys
import os

def build_executable():
    """実行ファイルをビルド"""
    print("実行ファイルをビルドしています...")
    
    # PyInstallerのコマンドを構築
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "x-session-extractor",
        "--console",
        "--add-data", "extract_session.py;.",
        "extract_session.py"
    ]
    
    # Windows用のアイコンがある場合は追加
    # cmd.extend(["--icon", "icon.ico"])
    
    try:
        subprocess.run(cmd, check=True)
        print("\nビルドが完了しました！")
        print("dist/x-session-extractor.exe が生成されました。")
    except subprocess.CalledProcessError as e:
        print(f"ビルドエラー: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("エラー: PyInstallerがインストールされていません。")
        print("以下のコマンドでインストールしてください:")
        print("pip install pyinstaller")
        sys.exit(1)


if __name__ == "__main__":
    build_executable()

