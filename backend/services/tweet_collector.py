"""
ツイート収集サービス
既存のcollect_tweets.pyを拡張してAPIから呼び出せるようにする
"""
import asyncio
import csv
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# 親ディレクトリをパスに追加して、twitter_api_browser_pythonモジュールをインポート可能にする
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from twitter_api_browser_python.main import TwitterAPIBrowser


async def collect_tweets_from_session(
    session_json: Dict[str, Any],
    keyword: str,
    start_date: str,
    end_date: str,
    output_file: str,
    limit: int = 100,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    セッションJSONを使用してツイートを収集
    
    Args:
        session_json: セッションJSONデータ
        keyword: 検索ワード（ハッシュタグまたはキーワード）
        start_date: 開始日（YYYY-MM-DD形式）
        end_date: 終了日（YYYY-MM-DD形式）
        output_file: 出力CSVファイルのパス
        limit: 最大取得件数
        progress_callback: 進捗を報告するコールバック関数（current, total, message）
        
    Returns:
        収集結果の辞書（tweet_count, output_file, error）
    """
    try:
        # 検索クエリを構築
        query = f"{keyword} since:{start_date} until:{end_date}"
        
        if progress_callback:
            await progress_callback(0, limit, f"検索クエリ: {query}")
        
        # セッションJSONを使用してブラウザを起動
        async with TwitterAPIBrowser(session_json=session_json, headless=True) as browser:
            if progress_callback:
                await progress_callback(0, limit, "ブラウザを起動しています...")
            
            # インジェクションスクリプトを実行
            inject = await browser.inject(sleep=2)  # 初期化待機時間を短縮
            
            if progress_callback:
                await progress_callback(0, limit, "ツイート収集を開始しています...")
            
            collected_tweets = []
            cursor = None
            
            while len(collected_tweets) < limit:
                if progress_callback:
                    await progress_callback(
                        len(collected_tweets), 
                        limit, 
                        f"収集中... (現在: {len(collected_tweets)}件)"
                    )
                
                variables = {
                    "rawQuery": query,
                    "count": 50,
                    "querySource": "typed_query",
                    "product": "Latest",
                    "withGrokTranslatedBio": False,
                }
                
                if cursor:
                    variables["cursor"] = cursor

                # リトライロジック
                max_retries = 3
                retry_count = 0
                res = None
                
                while retry_count < max_retries:
                    try:
                        print(f"[DEBUG] Requesting SearchTimeline (cursor: {cursor[:20] if cursor else 'None'})... (Attempt {retry_count + 1}/{max_retries})")
                        
                        # 30秒のタイムアウトを設定
                        res = await asyncio.wait_for(
                            inject.request("SearchTimeline", variables),
                            timeout=30.0
                        )
                        print("[DEBUG] Response received.")
                        break # 成功したらループを抜ける
                        
                    except asyncio.TimeoutError:
                        retry_count += 1
                        print(f"[WARN] Request timed out. Retrying... ({retry_count}/{max_retries})")
                        if retry_count < max_retries:
                            await asyncio.sleep(5.0) # リトライ前に少し待つ
                        
                    except Exception as e:
                        error_msg = f"リクエストエラー: {e}"
                        print(f"[ERROR] {error_msg}")
                        # その他のエラーはリトライせずに終了
                        if progress_callback:
                            await progress_callback(len(collected_tweets), limit, error_msg)
                        res = None
                        break
                
                if res is None:
                    print("[ERROR] Failed to fetch data after retries.")
                    break

                # レスポンスをパース
                try:
                    timeline = res["data"]["search_by_raw_query"]["search_timeline"]["timeline"]
                    instructions = timeline["instructions"]
                    
                    entries = []
                    for instruction in instructions:
                        if instruction["type"] == "TimelineAddEntries":
                            entries = instruction["entries"]
                            break
                        elif instruction["type"] == "TimelineReplaceEntry":
                            if instruction["entry"]["entryIdToReplace"] == "cursor-bottom-0":
                                entries.append(instruction["entry"])

                    new_tweets_found = False
                    bottom_cursor = None

                    for entry in entries:
                        try:
                            content = entry["content"]
                            
                            # カーソルを処理
                            if content["entryType"] == "TimelineTimelineCursor":
                                if content["cursorType"] == "Bottom" or content["cursorType"] == "ShowMore":
                                    bottom_cursor = content["value"]
                                continue

                            # ツイートを処理
                            if content["entryType"] == "TimelineTimelineItem":
                                item_result = content["itemContent"]["tweet_results"].get("result")
                                
                                if not item_result:
                                    continue
                                    
                                if "tweet" in item_result:
                                    item_result = item_result["tweet"]
                                    
                                if "legacy" not in item_result:
                                    continue

                                legacy = item_result["legacy"]
                                
                                # ユーザーデータをチェック
                                if "core" not in item_result or "user_results" not in item_result["core"]:
                                    continue
                                    
                                user_result = item_result["core"]["user_results"]["result"]
                                
                                if "legacy" in user_result:
                                    user_legacy = user_result["legacy"]
                                elif "user" in user_result and "legacy" in user_result["user"]:
                                    user_legacy = user_result["user"]["legacy"]
                                else:
                                    continue
                                
                                # データを抽出
                                tweet_id = legacy["id_str"]
                                
                                screen_name = user_legacy.get("screen_name")
                                author_name = user_legacy.get("name")
                                
                                if not screen_name and "core" in user_result:
                                    screen_name = user_result["core"].get("screen_name")
                                if not author_name and "core" in user_result:
                                    author_name = user_result["core"].get("name")

                                if not screen_name and "screen_name" in user_result:
                                    screen_name = user_result["screen_name"]
                                if not author_name and "name" in user_result:
                                    author_name = user_result["name"]
                                    
                                if not screen_name:
                                    screen_name = "Unknown"
                                if not author_name:
                                    author_name = "Unknown"

                                # 日付を変換
                                post_date = legacy["created_at"]
                                try:
                                    dt = datetime.strptime(post_date, "%a %b %d %H:%M:%S %z %Y")
                                    formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                                except:
                                    formatted_date = post_date

                                post_link = f"https://x.com/{screen_name}/status/{tweet_id}"
                                
                                # メトリクス
                                repost_count = legacy.get("retweet_count", 0)
                                favorite_count = legacy.get("favorite_count", 0)
                                
                                impression_count = 0
                                if "views" in item_result and "count" in item_result["views"]:
                                    impression_count = int(item_result["views"]["count"])

                                # ハッシュタグ
                                hashtags = [tag["text"] for tag in legacy.get("entities", {}).get("hashtags", [])]
                                search_tag_clean = keyword.replace("#", "").lower()
                                other_tags = [f"#{tag}" for tag in hashtags if tag.lower() != search_tag_clean]
                                
                                tweet_data = {
                                    "Author Name": author_name,
                                    "Post Date": formatted_date,
                                    "Post Link": post_link,
                                    "Other Hashtags": ", ".join(other_tags),
                                    "Repost Count": repost_count,
                                    "Impression Count": impression_count,
                                    "Like Count": favorite_count
                                }
                                
                                collected_tweets.append(tweet_data)
                                new_tweets_found = True
                                
                                if len(collected_tweets) >= limit:
                                    break
                        except Exception as e:
                            continue
                    
                    if len(collected_tweets) >= limit:
                        break

                    # カーソルを抽出
                    print(f"[DEBUG] Extracting cursor from instructions: {len(instructions)} items")
                    for instruction in instructions:
                        # print(f"[DEBUG] Instruction type: {instruction.get('type')}")
                        if instruction["type"] == "TimelineAddEntries":
                            for entry in instruction["entries"]:
                                if entry["content"]["entryType"] == "TimelineTimelineCursor" and entry["content"]["cursorType"] == "Bottom":
                                    bottom_cursor = entry["content"]["value"]
                                    print(f"[DEBUG] Found cursor in TimelineAddEntries: {bottom_cursor[:20]}...")
                        elif instruction["type"] == "TimelineReplaceEntry":
                            if instruction["entry"]["content"]["entryType"] == "TimelineTimelineCursor" and instruction["entry"]["content"]["cursorType"] == "Bottom":
                                bottom_cursor = instruction["entry"]["content"]["value"]
                                print(f"[DEBUG] Found cursor in TimelineReplaceEntry: {bottom_cursor[:20]}...")

                    if not bottom_cursor:
                        for entry in entries:
                            if entry["content"]["entryType"] == "TimelineTimelineCursor" and entry["content"]["cursorType"] == "Bottom":
                                bottom_cursor = entry["content"]["value"]
                                print(f"[DEBUG] Found cursor in entries: {bottom_cursor[:20]}...")

                    if not bottom_cursor:
                        print("[DEBUG] No cursor found in response")
                        # デバッグ用にレスポンス構造の一部を出力（必要なら）
                        # print(json.dumps(instructions, indent=2)[:500])

                    if not bottom_cursor or bottom_cursor == cursor:
                        if progress_callback:
                            msg = "タイムラインの終端に到達しました" if not bottom_cursor else "カーソルが更新されませんでした（終端）"
                            print(f"[DEBUG] {msg}")
                            await progress_callback(len(collected_tweets), limit, msg)
                        break
                    
                    cursor = bottom_cursor
                    print(f"[DEBUG] Sleeping for 2.0 seconds...")
                    await asyncio.sleep(2.0)  # 待機時間を0.5秒から2.0秒に延長して負荷軽減

                except KeyError as e:
                    error_msg = f"レスポンスパースエラー: {e}"
                    if progress_callback:
                        await progress_callback(len(collected_tweets), limit, error_msg)
                    break
                except Exception as e:
                    error_msg = f"予期しないエラー: {e}"
                    if progress_callback:
                        await progress_callback(len(collected_tweets), limit, error_msg)
                    break

        # CSVに書き込み
        if collected_tweets:
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
            with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=collected_tweets[0].keys())
                writer.writeheader()
                writer.writerows(collected_tweets)
            
            if progress_callback:
                await progress_callback(len(collected_tweets), limit, f"完了: {len(collected_tweets)}件のツイートを収集しました")
            
            return {
                "tweet_count": len(collected_tweets),
                "output_file": output_file,
                "error": None
            }
        else:
            return {
                "tweet_count": 0,
                "output_file": None,
                "error": "ツイートが収集されませんでした"
            }
            
    except Exception as e:
        error_msg = f"収集エラー: {str(e)}"
        if progress_callback:
            await progress_callback(0, limit, error_msg)
        return {
            "tweet_count": 0,
            "output_file": None,
            "error": error_msg
        }

