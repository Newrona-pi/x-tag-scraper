"""
FastAPIルート定義
"""
import os
import uuid
import json
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from services.session_manager import load_session_from_json
from services.tweet_collector import collect_tweets_from_session

router = APIRouter()

# ジョブの状態を保存する辞書（本番環境ではRedisなどを使用）
jobs: Dict[str, Dict[str, Any]] = {}

# 出力ファイルを保存するディレクトリ
OUTPUT_DIR = "./output"


class CollectRequest(BaseModel):
    """ツイート収集リクエスト"""
    hashtag: str
    start_date: str
    end_date: str
    limit: int = 100


async def run_collection_job(job_id: str, session_data: Dict[str, Any], params: CollectRequest):
    """バックグラウンドでツイート収集を実行"""
    jobs[job_id]["status"] = "running"
    jobs[job_id]["progress"] = 0
    jobs[job_id]["message"] = "開始しています..."
    
    output_file = os.path.join(OUTPUT_DIR, f"{job_id}.csv")
    
    async def progress_callback(current: int, total: int, message: str):
        """進捗を更新"""
        jobs[job_id]["progress"] = current
        jobs[job_id]["total"] = total
        jobs[job_id]["message"] = message
    
    try:
        result = await collect_tweets_from_session(
            session_json=session_data,
            hashtag=params.hashtag,
            start_date=params.start_date,
            end_date=params.end_date,
            output_file=output_file,
            limit=params.limit,
            progress_callback=progress_callback
        )
        
        if result["error"]:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = result["error"]
        else:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["output_file"] = result["output_file"]
            jobs[job_id]["tweet_count"] = result["tweet_count"]
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


@router.post("/api/collect")
async def collect_tweets(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    hashtag: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100
):
    """
    ツイート収集を開始
    
    リクエストボディにJSONパラメータを含めることも可能:
    {
        "hashtag": "#Python",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "limit": 100
    }
    """
    # デバッグ用ログ
    print(f"[DEBUG] Received request - hashtag: {hashtag}, start_date: {start_date}, end_date: {end_date}, limit: {limit}")
    print(f"[DEBUG] File: {file.filename}, content_type: {file.content_type}")
    
    # ファイルからセッションJSONを読み込む
    try:
        content = await file.read()
        print(f"[DEBUG] File content length: {len(content)} bytes")
        session_data = load_session_from_json(json.loads(content))
        print(f"[DEBUG] Session data loaded successfully")
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decode error: {e}")
        raise HTTPException(status_code=400, detail=f"無効なJSONファイルです: {str(e)}")
    except ValueError as e:
        print(f"[ERROR] Value error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Unexpected error reading file: {e}")
        raise HTTPException(status_code=400, detail=f"ファイル読み込みエラー: {str(e)}")
    
    # パラメータを取得（クエリパラメータまたはリクエストボディから）
    if not all([hashtag, start_date, end_date]):
        missing = []
        if not hashtag: missing.append("hashtag")
        if not start_date: missing.append("start_date")
        if not end_date: missing.append("end_date")
        error_msg = f"必須パラメータが不足しています: {', '.join(missing)}"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # ジョブIDを生成
    job_id = str(uuid.uuid4())
    print(f"[INFO] Created job: {job_id}")
    
    # ジョブを初期化
    jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "total": limit,
        "message": "待機中...",
        "hashtag": hashtag,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit
    }
    
    # バックグラウンドタスクとして実行
    params = CollectRequest(
        hashtag=hashtag,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    background_tasks.add_task(run_collection_job, job_id, session_data, params)
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "ツイート収集を開始しました"
    }


@router.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """ジョブの状態を取得"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="ジョブが見つかりません")
    
    job = jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
        "total": job.get("total", 0),
        "message": job.get("message", ""),
        "tweet_count": job.get("tweet_count"),
        "error": job.get("error")
    }


@router.get("/api/download/{job_id}")
async def download_csv(job_id: str):
    """完了したCSVファイルをダウンロード"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="ジョブが見つかりません")
    
    job = jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="ジョブがまだ完了していません")
    
    output_file = job.get("output_file")
    if not output_file or not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="出力ファイルが見つかりません")
    
    return FileResponse(
        output_file,
        media_type="text/csv",
        filename=f"tweets_{job_id}.csv"
    )

