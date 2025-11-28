"""
セッション管理モジュール
セッションJSONからクッキーとローカルストレージを復元する機能を提供
"""
import json
from typing import Dict, Any, Optional


def load_session_from_json(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    セッションJSONデータを検証し、正しい形式かチェック
    
    Args:
        session_data: セッションJSONデータ
        
    Returns:
        検証済みのセッションデータ
        
    Raises:
        ValueError: セッションデータが無効な場合
    """
    if not isinstance(session_data, dict):
        raise ValueError("セッションデータは辞書形式である必要があります")
    
    if "cookies" not in session_data:
        raise ValueError("セッションデータに'cookies'が含まれていません")
    
    # cookiesがリストであることを確認
    if not isinstance(session_data["cookies"], list):
        raise ValueError("'cookies'はリスト形式である必要があります")
    
    # localStorageとsessionStorageはオプション
    if "localStorage" not in session_data:
        session_data["localStorage"] = {}
    if "sessionStorage" not in session_data:
        session_data["sessionStorage"] = {}
    
    return session_data


def load_session_from_file(file_path: str) -> Dict[str, Any]:
    """
    ファイルからセッションJSONを読み込む
    
    Args:
        file_path: セッションJSONファイルのパス
        
    Returns:
        セッションデータ
    """
    with open(file_path, "r", encoding="utf-8") as f:
        session_data = json.load(f)
    
    return load_session_from_json(session_data)

