#!/usr/bin/env python3
import requests
import json
import sys

def check_voicevox_available(url="http://localhost:50021"):
    """VOICEVOXエンジンが利用可能かチェックする"""
    try:
        response = requests.get(f"{url}/version")
        return response.status_code == 200
    except:
        return False

def get_voicevox_speakers(url="http://localhost:50021"):
    """VOICEVOXから利用可能な話者リストを取得する"""
    try:
        if check_voicevox_available(url):
            response = requests.get(f"{url}/speakers")
            if response.status_code == 200:
                return response.json()
        return []
    except Exception as e:
        print(f"エラー: {e}")
        return []

def format_speaker_dict(speakers):
    """話者情報を整形されたPython辞書形式で出力"""
    print("\n# script_reader.pyに追加できる話者辞書:")
    print("VOICEVOX_SPEAKERS = {")
    
    for speaker in speakers:
        name = speaker["name"]
        for style in speaker["styles"]:
            style_id = style["id"]
            style_name = style["name"]
            full_name = f"{name}（{style_name}）" if style_name != "ノーマル" else name
            print(f"    \"{full_name}\": {style_id},")
    
    print("}")

if __name__ == "__main__":
    url = "http://localhost:50021"
    
    if not check_voicevox_available(url):
        print("VOICEVOXエンジンが実行されていないか、接続できません。")
        print("VOICEVOXエンジンを起動してから再試行してください。")
        sys.exit(1)
    
    speakers = get_voicevox_speakers(url)
    
    if not speakers:
        print("話者情報を取得できませんでした。")
        sys.exit(1)
    
    print("= VOICEVOXの話者一覧 =")
    for speaker in speakers:
        print(f"\n## {speaker['name']}")
        for style in speaker["styles"]:
            print(f"ID: {style['id']} - {style['name']}")
    
    format_speaker_dict(speakers)