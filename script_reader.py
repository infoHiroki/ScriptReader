import tkinter as tk
from tkinter import scrolledtext, Button, Label, Frame, filedialog, Scale, OptionMenu, StringVar, Checkbutton, IntVar
import os.path
import subprocess
import threading
import tempfile
import time
import re
import json
import sys
import atexit
import platform
import datetime

# 音声合成用ライブラリ
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("Info: gTTSライブラリが見つかりません。標準の音声合成を使用します。")

# VOICEVOX用のrequestsライブラリ
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Info: requestsライブラリが見つかりません。VOICEVOXは利用できません。")

# 台本ファイルへのデフォルトパス
DEFAULT_SCRIPT_PATH = "/Users/hirokitakamura/Documents/Obsidian Vault/200_projects/AI福岡勉強会/Claude_MCP_LT_script.md"

# VOICEVOXの設定
VOICEVOX_URL = "http://localhost:50021"  # VOICEVOXエンジンのURL

# ログ関連のユーティリティ
def log_message(message, level="INFO", prefix=None):
    """アプリケーションログを一貫した形式で出力する
    
    Args:
        message (str): ログメッセージ
        level (str): ログレベル (INFO, WARN, ERROR, DEBUG)
        prefix (str): メッセージの前に付ける追加情報
    """
    timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
    
    # ログレベルに応じたプレフィックス
    level_prefix = {
        "INFO": "ℹ️",
        "WARN": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍",
        "SUCCESS": "✅"
    }.get(level.upper(), "")
    
    # プレフィックスがあれば追加
    prefix_str = f"[{prefix}] " if prefix else ""
    
    # 整形されたログメッセージを出力
    print(f"{timestamp} {level_prefix} {prefix_str}{message}")

# macOSの場合のVOICEVOXデフォルトパス
DEFAULT_VOICEVOX_PATH = "/Applications/VOICEVOX.app"

# VOICEVOXの話者リスト
VOICEVOX_SPEAKERS = {
    "四国めたん": 2,
    "四国めたん（あまあま）": 0,
    "四国めたん（ツンツン）": 6,
    "四国めたん（セクシー）": 4,
    "四国めたん（ささやき）": 36,
    "四国めたん（ヒソヒソ）": 37,
    "ずんだもん": 3,
    "ずんだもん（あまあま）": 1,
    "ずんだもん（ツンツン）": 7,
    "ずんだもん（セクシー）": 5,
    "ずんだもん（ささやき）": 22,
    "ずんだもん（ヒソヒソ）": 38,
    "ずんだもん（ヘロヘロ）": 75,
    "ずんだもん（なみだめ）": 76,
    "春日部つむぎ": 8,
    "雨晴はう": 10,
    "波音リツ": 9,
    "波音リツ（クイーン）": 65,
    "玄野武宏": 11,
    "玄野武宏（喜び）": 39,
    "玄野武宏（ツンギレ）": 40,
    "玄野武宏（悲しみ）": 41,
    "白上虎太郎（ふつう）": 12,
    "白上虎太郎（わーい）": 32,
    "白上虎太郎（びくびく）": 33,
    "白上虎太郎（おこ）": 34,
    "白上虎太郎（びえーん）": 35,
    "青山龍星": 13,
    "青山龍星（熱血）": 81,
    "青山龍星（不機嫌）": 82,
    "青山龍星（喜び）": 83,
    "青山龍星（しっとり）": 84,
    "青山龍星（かなしみ）": 85,
    "青山龍星（囁き）": 86,
    "冥鳴ひまり": 14,
    "九州そら": 16,
    "九州そら（あまあま）": 15,
    "九州そら（ツンツン）": 18,
    "九州そら（セクシー）": 17,
    "九州そら（ささやき）": 19,
    "もち子さん": 20,
    "もち子さん（セクシー／あん子）": 66,
    "もち子さん（泣き）": 77,
    "もち子さん（怒り）": 78,
    "もち子さん（喜び）": 79,
    "もち子さん（のんびり）": 80,
    "剣崎雌雄": 21,
}

# VOICEVOXエンジンプロセス
voicevox_process = None

def validate_voicevox_path(path):
    """指定されたVOICEVOXパスが有効かどうかを確認する
    
    Args:
        path (str): 検証するVOICEVOXパス
        
    Returns:
        bool: パスが有効な場合はTrue、そうでない場合はFalse
    """
    if not path or not os.path.exists(path):
        return False
        
    # macOSの場合
    if platform.system() == 'Darwin':
        # VOICEVOXアプリバンドルの存在確認
        if path.endswith('.app') and os.path.isdir(path):
            # エンジン実行ファイルの存在確認
            engine_path = os.path.join(path, 'Contents', 'Resources', 'vv-engine', 'run')
            return os.path.exists(engine_path) and os.access(engine_path, os.X_OK)
        return False
    
    # Windowsの場合（将来的に対応）
    elif platform.system() == 'Windows':
        # VOICEVOX実行ファイルの存在確認
        exe_path = os.path.join(path, 'VOICEVOX.exe')
        return os.path.exists(exe_path) and os.access(exe_path, os.X_OK)
    
    return False

def find_voicevox_path(user_path=None):
    """VOICEVOXのインストールパスを検出する
    
    Args:
        user_path (str, optional): ユーザーが指定したVOICEVOXパス
        
    Returns:
        str or None: 有効なVOICEVOXパス、見つからない場合はNone
    """
    # ユーザー指定のパスがあり、それが有効な場合はそれを使用
    if user_path and validate_voicevox_path(user_path):
        log_message(f"ユーザー指定のVOICEVOXパスを使用: {user_path}", level="INFO", prefix="VOICEVOX")
        return user_path
        
    # macOSの場合
    if platform.system() == 'Darwin':
        # デフォルトのインストールパスをチェック
        if os.path.exists(DEFAULT_VOICEVOX_PATH) and validate_voicevox_path(DEFAULT_VOICEVOX_PATH):
            log_message(f"デフォルトのVOICEVOXパスを使用: {DEFAULT_VOICEVOX_PATH}", level="INFO", prefix="VOICEVOX")
            return DEFAULT_VOICEVOX_PATH
        
        # Applicationsフォルダを検索
        try:
            result = subprocess.run(['find', '/Applications', '-name', 'VOICEVOX.app', '-maxdepth', '1'], 
                                  capture_output=True, text=True, check=False)
            if result.stdout:
                found_path = result.stdout.strip()
                if validate_voicevox_path(found_path):
                    log_message(f"検索で見つかったVOICEVOXパスを使用: {found_path}", level="INFO", prefix="VOICEVOX")
                    return found_path
        except Exception as e:
            log_message(f"VOICEVOXパスの検索中にエラー: {e}", level="ERROR", prefix="VOICEVOX")
    
    # Windowsの場合（将来的に対応）
    elif platform.system() == 'Windows':
        # Windowsでの一般的なインストールパスをチェック
        paths = [
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'VOICEVOX'),
            os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'VOICEVOX')
        ]
        for path in paths:
            if validate_voicevox_path(path):
                log_message(f"Windows標準パスでVOICEVOXを発見: {path}", level="INFO", prefix="VOICEVOX")
                return path
    
    log_message("有効なVOICEVOXパスが見つかりませんでした", level="WARN", prefix="VOICEVOX")
    return None

def is_voicevox_engine_running():
    """VOICEVOXエンジンが起動しているか確認する"""
    if not REQUESTS_AVAILABLE:
        return False
    
    try:
        response = requests.get(f"{VOICEVOX_URL}/version", timeout=1)
        return response.status_code == 200
    except Exception:
        return False

def start_voicevox_engine(user_specified_path=None):
    """VOICEVOXエンジンを起動する
    
    Args:
        user_specified_path (str, optional): ユーザーが指定したVOICEVOXパス
        
    Returns:
        bool: 起動に成功した場合はTrue、失敗した場合はFalse
    """
    global voicevox_process
    
    if is_voicevox_engine_running():
        log_message("VOICEVOXエンジンはすでに実行中です", level="INFO", prefix="VOICEVOX")
        return True
    
    # パスを検索（ユーザー指定のパスがある場合はそれを優先）
    voicevox_path = find_voicevox_path(user_specified_path)
    if not voicevox_path:
        log_message("VOICEVOXのインストールパスが見つかりません", level="ERROR", prefix="VOICEVOX")
        return False
    
    try:
        # macOS
        if platform.system() == 'Darwin':
            # VOICEVOX.app内のengineを起動
            engine_path = os.path.join(voicevox_path, 'Contents', 'Resources', 'vv-engine', 'run')
            if os.path.exists(engine_path):
                log_message(f"VOICEVOXエンジンを起動しています: {engine_path}", level="INFO", prefix="VOICEVOX")
                voicevox_process = subprocess.Popen([engine_path, '--host=localhost', '--port=50021'], 
                                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # プロセスが終了しないよう、atexitで登録
                atexit.register(stop_voicevox_engine)
                
                # 起動を待機
                max_retries = 10
                for i in range(max_retries):
                    time.sleep(1)  # 1秒待機
                    if is_voicevox_engine_running():
                        log_message("VOICEVOXエンジンが起動しました", level="SUCCESS", prefix="VOICEVOX")
                        return True
                    log_message(f"VOICEVOXエンジン起動待機中... ({i+1}/{max_retries})", level="INFO", prefix="VOICEVOX")
                
                log_message("VOICEVOXエンジンの起動がタイムアウトしました", level="ERROR", prefix="VOICEVOX")
                return False
            else:
                log_message(f"VOICEVOXエンジン実行ファイルが見つかりません: {engine_path}", level="ERROR", prefix="VOICEVOX")
                return False
        
        # Windows（将来的に対応）
        elif platform.system() == 'Windows':
            # Windowsでの起動方法（将来実装）
            log_message("Windows環境でのVOICEVOX自動起動は現在サポートされていません", level="WARN", prefix="VOICEVOX")
            return False
        
        else:
            log_message(f"サポートされていないOS: {platform.system()}", level="ERROR", prefix="VOICEVOX")
            return False
        
    except Exception as e:
        log_message(f"VOICEVOXエンジン起動エラー: {e}", level="ERROR", prefix="VOICEVOX")
        import traceback
        traceback.print_exc()
        return False

def stop_voicevox_engine():
    """VOICEVOXエンジンを停止する"""
    global voicevox_process
    if voicevox_process:
        try:
            print("VOICEVOXエンジンを停止します")
            voicevox_process.terminate()
            voicevox_process.wait(timeout=5)
            voicevox_process = None
        except Exception as e:
            print(f"VOICEVOXエンジン停止エラー: {e}")
            try:
                voicevox_process.kill()
            except:
                pass

class SimpleScriptReader:
    def __init__(self, root):
        self.root = root
        self.root.title("シンプル台本リーダー")
        self.root.geometry("800x720")  # 高さを少し大きくしてVOICEVOX設定用のスペースを確保
        
        # ダークモードのカラースキーム
        self.bg_color = "#2b2b2b"  # 背景色
        self.text_bg_color = "#383838"  # テキストエリア背景
        self.text_fg_color = "#e0e0e0"  # テキスト色
        self.btn_bg = "#6a6a6a"  # 標準ボタン背景
        self.btn_fg = "#ffffff"  # 標準ボタン文字
        self.accent_green = "#4caf50"  # アクセントグリーン
        self.accent_red = "#ff5252"  # アクセントレッド
        self.accent_blue = "#2196f3"  # アクセントブルー
        
        # 読み上げ設定
        self.speech_rate = 220  # 高速に設定 (sayコマンド用レート)
        self.pause_time = 0.08  # 改行間のポーズ時間をより短く
        self.min_rate = 100     # 最小読み上げ速度
        self.max_rate = 660     # 最大読み上げ速度（VOICEVOXで3倍速まで対応）
        
        # 音声合成エンジンの設定
        self.use_gtts = False   # Google TTS
        self.use_voicevox = True  # デフォルトでVOICEVOXを使用
        self.voicevox_speaker = 1  # デフォルト話者ID
        self.voicevox_url = VOICEVOX_URL  # VOICEVOXエンジンのURL
        
        # VOICEVOX関連設定
        self.voicevox_path = StringVar(value=find_voicevox_path() or "")  # VOICEVOXのパス
        self.auto_start_voicevox = IntVar(value=1)  # 自動起動設定（デフォルトで有効）
        
        # 音声キャッシュ用の辞書
        self.audio_cache = {}  # キー: スライドインデックス, 値: 一時ファイルパス
        self.is_loading = {}   # キー: スライドインデックス, 値: True/False（読み込み中か）
        self.is_loaded = {}    # キー: スライドインデックス, 値: True/False（ロード済みか）
        
        # ルートウィンドウの背景色設定
        self.root.configure(bg=self.bg_color)
        
        # 現在のファイルパス
        self.script_path = DEFAULT_SCRIPT_PATH if os.path.exists(DEFAULT_SCRIPT_PATH) else None
        self.slides = []
        self.current_slide = 0
        
        # UI作成
        self.create_ui()
        
        # ファイルがあれば読み込み
        if self.script_path:
            self.load_file(self.script_path)
        else:
            self.slides = ["ファイルを開いていません。「ファイルを開く」ボタンをクリックしてください。"]
            self.show_slide()
        
        # アプリケーション終了時の処理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # VOICEVOXエンジンを自動起動
        if self.auto_start_voicevox.get() == 1:
            self.start_voicevox_if_needed()
    
    def browse_voicevox_path(self):
        """VOICEVOXアプリを選択するダイアログを表示"""
        # macOSの場合はアプリバンドルを選択
        if platform.system() == 'Darwin':
            file_types = [("VOICEVOXアプリ", "*.app")]
            initial_dir = "/Applications"
        # Windowsの場合は実行ファイルを選択
        elif platform.system() == 'Windows':
            file_types = [("VOICEVOX実行ファイル", "*.exe")]
            initial_dir = "C:\\Program Files"
        else:
            file_types = [("すべてのファイル", "*.*")]
            initial_dir = "/"
        
        # ファイル選択ダイアログを表示
        path = filedialog.askdirectory(
            title="VOICEVOXアプリケーションを選択",
            initialdir=initial_dir
        )
        
        if path:
            self.voicevox_path.set(path)
            # 自動的に検証する
            self.validate_and_save_voicevox_path()
    
    def validate_and_save_voicevox_path(self):
        """入力されたVOICEVOXパスを検証して保存する"""
        path = self.voicevox_path.get()
        
        if not path:
            self.status_label.config(text="VOICEVOXパスが指定されていません")
            return
        
        # パスを検証
        if validate_voicevox_path(path):
            self.status_label.config(text=f"VOICEVOXパスの検証に成功しました: {path}")
            log_message(f"有効なVOICEVOXパスを設定: {path}", level="SUCCESS", prefix="VOICEVOX")
            # インスタンス変数に保存
            self.voicevox_path.set(path)
        else:
            self.status_label.config(text=f"無効なVOICEVOXパス: {path}")
            log_message(f"VOICEVOXパスの検証に失敗: {path}", level="ERROR", prefix="VOICEVOX")
    
    def start_voicevox_if_needed(self):
        """VOICEVOXエンジンが起動していなければ自動起動"""
        if not is_voicevox_engine_running():
            # 指定されたパスがあれば使用
            user_path = self.voicevox_path.get() if self.voicevox_path.get() else None
            
            if start_voicevox_engine(user_path):
                self.status_label.config(text="VOICEVOXエンジンを自動起動しました")
                # 起動に成功したらVOICEVOXエンジンを選択
                self.root.after(2000, lambda: self.change_engine("voicevox"))
            else:
                self.status_label.config(text="VOICEVOXエンジンの自動起動に失敗しました")
        else:
            self.status_label.config(text="VOICEVOXエンジンは既に起動しています")
    
    def load_file(self, file_path):
        """指定されたファイルを読み込む"""
        self.script_path = file_path
        self.slides = self.parse_slides(file_path)
        self.current_slide = 0
        self.show_slide()
        
        # ウィンドウタイトルにファイル名を表示
        filename = os.path.basename(file_path)
        self.root.title(f"シンプル台本リーダー - {filename}")
    
    def parse_slides(self, file_path):
        """マークダウンファイルからスライドを読み込む"""
        if not os.path.exists(file_path):
            return ["ファイルが見つかりません: " + file_path]
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # スライドの区切り（## で始まる行）で分割
            slides = []
            current_slide = ""
            
            for line in content.split('\n'):
                if line.startswith('## '):
                    if current_slide:
                        slides.append(current_slide)
                    current_slide = line
                else:
                    current_slide += '\n' + line
                    
            # 最後のスライドを追加
            if current_slide:
                slides.append(current_slide)
                
            return slides
        except Exception as e:
            print(f"ファイル読み込みエラー: {e}")
            return ["ファイルの読み込みに失敗しました\n{str(e)}"]
        
    def create_ui(self):
        """UIコンポーネントを作成"""
        # テキスト表示エリア
        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, font=("Helvetica", 14),
                                               bg=self.text_bg_color, fg=self.text_fg_color,
                                               insertbackground=self.text_fg_color)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.text_area.config(state=tk.DISABLED)
        
        # コントロールフレーム
        control_frame = Frame(self.root, bg=self.bg_color)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 前へボタン
        self.prev_btn = Button(control_frame, text="前へ", command=self.prev_slide, 
                              font=("Helvetica", 12), bg="#aaaaaa", fg="black")
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        # 次へボタン
        self.next_btn = Button(control_frame, text="次へ", command=self.next_slide, 
                              font=("Helvetica", 12), bg="#aaaaaa", fg="black")
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # 音声再生ボタン
        self.speak_btn = Button(control_frame, text="▶ 音声再生", command=self.speak_slide, 
                               font=("Helvetica", 12), bg=self.accent_green, fg="black")
        self.speak_btn.pack(side=tk.LEFT, padx=5)
        
        # 音声停止ボタン
        self.stop_btn = Button(control_frame, text="停止", command=self.stop_speaking, 
                              font=("Helvetica", 12), bg=self.accent_red, fg="black")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 音声読み込みボタン（手動読み込み用） - 重要なボタンなのでさらに目立たせる
        self.load_audio_btn = Button(control_frame, text="音声読み込み (B) ⬇", command=self.start_audio_preload, 
                                  font=("Helvetica", 12, "bold"), bg="#FF9800", fg="black",
                                  relief=tk.RAISED, borderwidth=3)
        self.load_audio_btn.pack(side=tk.LEFT, padx=8)
        
        # ファイルを開くボタン
        self.open_btn = Button(control_frame, text="ファイルを開く", command=self.open_file, 
                              font=("Helvetica", 12), bg=self.accent_blue, fg="black")
        self.open_btn.pack(side=tk.LEFT, padx=5)
        
        # スライド番号表示
        self.slide_label = Label(control_frame, text="", font=("Helvetica", 12), 
                                bg=self.bg_color, fg=self.text_fg_color)
        self.slide_label.pack(side=tk.RIGHT, padx=5)
        
        # 音声速度調整用のフレーム
        speed_frame = Frame(self.root, bg=self.bg_color)
        speed_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 音声速度調整ラベル
        speed_label = Label(speed_frame, text="読み上げ速度:", font=("Helvetica", 12),
                           bg=self.bg_color, fg=self.text_fg_color)
        speed_label.pack(side=tk.LEFT, padx=5)
        
        # 音声速度スライダー
        self.speed_slider = Scale(speed_frame, from_=self.min_rate, to=self.max_rate, 
                                 orient=tk.HORIZONTAL, length=200, 
                                 bg=self.bg_color, fg=self.text_fg_color,
                                 troughcolor=self.text_bg_color, highlightthickness=0,
                                 command=self.update_speech_rate)
        self.speed_slider.set(self.speech_rate)  # 現在の値を設定
        self.speed_slider.pack(side=tk.LEFT, padx=5)
        
        # 速度表示ラベル
        self.speed_value_label = Label(speed_frame, text=f"{self.speech_rate} WPM", 
                                     font=("Helvetica", 12),
                                     bg=self.bg_color, fg=self.text_fg_color)
        self.speed_value_label.pack(side=tk.LEFT, padx=5)
        
        # 音声エンジン選択用のフレーム
        engine_frame = Frame(self.root, bg=self.bg_color)
        engine_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 音声エンジン選択ラベル
        engine_label = Label(engine_frame, text="音声エンジン:", font=("Helvetica", 12),
                           bg=self.bg_color, fg=self.text_fg_color)
        engine_label.pack(side=tk.LEFT, padx=5)
        
        # 音声エンジン選択ボタン - macOSのsayコマンド
        self.say_btn = Button(engine_frame, text="macOS say", 
                            command=lambda: self.change_engine("say"),
                            font=("Helvetica", 12), 
                            bg=self.accent_blue if not (self.use_gtts or self.use_voicevox) else self.btn_bg, 
                            fg="black")
        self.say_btn.pack(side=tk.LEFT, padx=5)
        
        # 音声エンジン選択ボタン - Google TTS
        self.gtts_btn = Button(engine_frame, text="Google TTS", 
                             command=lambda: self.change_engine("gtts"),
                             font=("Helvetica", 12), 
                             bg=self.accent_blue if self.use_gtts and GTTS_AVAILABLE else self.btn_bg, 
                             fg="black",
                             state=tk.NORMAL if GTTS_AVAILABLE else tk.DISABLED)
        self.gtts_btn.pack(side=tk.LEFT, padx=5)
        
        # 音声エンジン選択ボタン - VOICEVOX
        self.voicevox_btn = Button(engine_frame, text="VOICEVOX", 
                                command=lambda: self.change_engine("voicevox"),
                                font=("Helvetica", 12), 
                                bg=self.accent_blue if self.use_voicevox else self.btn_bg, 
                                fg="black",
                                state=tk.NORMAL if REQUESTS_AVAILABLE else tk.DISABLED)
        self.voicevox_btn.pack(side=tk.LEFT, padx=5)
        
        # VOICEVOX話者選択フレーム
        voice_frame = Frame(self.root, bg=self.bg_color)
        voice_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # VOICEVOX話者選択ラベル
        voice_label = Label(voice_frame, text="VOICEVOX話者:", font=("Helvetica", 12),
                          bg=self.bg_color, fg=self.text_fg_color)
        voice_label.pack(side=tk.LEFT, padx=5)
        
        # VOICEVOX話者選択ドロップダウン
        self.speaker_var = StringVar(self.root)
        self.speaker_var.set(list(VOICEVOX_SPEAKERS.keys())[0])  # デフォルト値を設定
        
        self.speaker_dropdown = OptionMenu(voice_frame, self.speaker_var, *VOICEVOX_SPEAKERS.keys())
        self.speaker_dropdown.config(font=("Helvetica", 12), bg=self.btn_bg, fg="black")
        self.speaker_dropdown.pack(side=tk.LEFT, padx=5)
        
        # 話者選択変更時のコールバック設定
        self.speaker_var.trace('w', self.change_speaker)
        
        # 話者情報表示ラベル
        self.speaker_info_label = Label(voice_frame, text="", font=("Helvetica", 12),
                                      bg=self.bg_color, fg=self.text_fg_color)
        self.speaker_info_label.pack(side=tk.LEFT, padx=5)
        
        # VOICEVOX設定フレーム
        voicevox_frame = Frame(self.root, bg=self.bg_color)
        voicevox_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # VOICEVOXパスラベル
        voicevox_path_label = Label(voicevox_frame, text="VOICEVOXパス:", font=("Helvetica", 12),
                                  bg=self.bg_color, fg=self.text_fg_color)
        voicevox_path_label.pack(side=tk.LEFT, padx=5)
        
        # VOICEVOXパス入力フィールド
        self.voicevox_path_entry = tk.Entry(voicevox_frame, textvariable=self.voicevox_path, 
                                        font=("Helvetica", 12), width=30)
        self.voicevox_path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # VOICEVOXパス選択ボタン
        self.browse_voicevox_btn = Button(voicevox_frame, text="参照...", 
                                      command=self.browse_voicevox_path,
                                      font=("Helvetica", 10), 
                                      bg=self.btn_bg, fg="black")
        self.browse_voicevox_btn.pack(side=tk.LEFT, padx=2)
        
        # VOICEVOXパス検証ボタン
        self.validate_voicevox_btn = Button(voicevox_frame, text="検証", 
                                        command=self.validate_and_save_voicevox_path,
                                        font=("Helvetica", 10), 
                                        bg=self.accent_green, fg="black")
        self.validate_voicevox_btn.pack(side=tk.LEFT, padx=2)
        
        # VOICEVOX自動起動フレーム (新規追加)
        auto_frame = Frame(self.root, bg=self.bg_color)
        auto_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # VOICEVOX自動起動チェックボックス
        self.auto_start_checkbox = Checkbutton(auto_frame, text="VOICEVOXを自動起動する", 
                                           variable=self.auto_start_voicevox,
                                           font=("Helvetica", 12),
                                           bg=self.bg_color, fg=self.text_fg_color,
                                           selectcolor=self.bg_color,
                                           activebackground=self.bg_color,
                                           command=self.toggle_auto_start)
        self.auto_start_checkbox.pack(side=tk.LEFT, padx=5)
        
        # VOICEVOX手動起動ボタン
        self.start_voicevox_btn = Button(auto_frame, text="VOICEVOXを起動", 
                                     command=self.start_voicevox_if_needed,
                                     font=("Helvetica", 12), 
                                     bg=self.accent_green, fg="black")
        self.start_voicevox_btn.pack(side=tk.LEFT, padx=5)
        
        # ステータスフレーム
        status_frame = Frame(self.root, bg=self.bg_color)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # ステータス表示ラベル
        self.status_label = Label(status_frame, text="", font=("Helvetica", 11),
                               bg=self.bg_color, fg=self.text_fg_color)
        self.status_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 読み込み進捗インジケーター
        self.progress_var = StringVar()
        self.progress_var.set("")  # 最初は非表示
        self.progress_label = Label(status_frame, textvariable=self.progress_var, 
                                  font=("Helvetica", 11),
                                  bg=self.bg_color, fg=self.accent_green)
        self.progress_label.pack(side=tk.RIGHT, padx=5)
        
        # 初期話者を設定
        self.change_speaker()
        
        # 音声再生のステータス
        self.is_speaking = False
        self.speak_process = None
        
        # キーボードショートカット
        self.root.bind('<Left>', lambda event: self.prev_slide())
        self.root.bind('<Right>', lambda event: self.next_slide())
        self.root.bind('<space>', lambda event: self.speak_slide())
        self.root.bind('<Escape>', lambda event: self.stop_speaking())
        self.root.bind('<Control-o>', lambda event: self.open_file())
        self.root.bind('<Up>', lambda event: self.increase_speed())
        self.root.bind('<Down>', lambda event: self.decrease_speed())
        # 音声読み込みショートカット
        self.root.bind('b', lambda event: self.start_audio_preload())
        self.root.bind('B', lambda event: self.start_audio_preload())
    
    def toggle_auto_start(self):
        """VOICEVOX自動起動オプションの切り替え"""
        if self.auto_start_voicevox.get() == 1:
            self.status_label.config(text="VOICEVOXの自動起動が有効になりました")
            # 設定が有効になった場合、VOICEVOXエンジンを起動
            self.start_voicevox_if_needed()
        else:
            self.status_label.config(text="VOICEVOXの自動起動が無効になりました")
    
    def change_speaker(self, *args):
        """VOICEVOXの話者を変更する"""
        selected_speaker = self.speaker_var.get()
        self.voicevox_speaker = VOICEVOX_SPEAKERS[selected_speaker]
        self.speaker_info_label.config(text=f"ID: {self.voicevox_speaker}")
        log_message(f"VOICEVOX話者を {selected_speaker} (ID: {self.voicevox_speaker}) に変更しました", 
                  level="INFO", prefix="VOICEVOX")
        
        # 話者を変更した場合、現在のスライドの音声キャッシュをクリア
        if self.current_slide in self.audio_cache:
            try:
                if os.path.exists(self.audio_cache[self.current_slide]):
                    os.unlink(self.audio_cache[self.current_slide])
                    log_message(f"話者変更により音声キャッシュを削除: {self.audio_cache[self.current_slide]}", 
                             level="INFO", prefix="キャッシュ")
            except Exception as e:
                log_message(f"キャッシュ削除エラー: {e}", level="ERROR", prefix="キャッシュ")
            
            # キャッシュ情報をリセット
            self.audio_cache.pop(self.current_slide, None)
            self.is_loaded.pop(self.current_slide, None)
            
            # 音声の読み込みが必要であることを表示
            self.status_label.config(text="話者を変更しました。音声の再読み込みが必要です")
            # 再生ボタンをグレーアウト
            self.speak_btn.config(bg="#cccccc", fg="black", text="音声未読込", state=tk.DISABLED)
    
    def show_slide(self):
        """現在のスライドを表示"""
        if not self.slides:
            return
            
        # テキストエリアを更新
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, self.slides[self.current_slide])
        self.text_area.config(state=tk.DISABLED)
        
        # スライド番号を更新
        self.slide_label.config(text=f"スライド: {self.current_slide + 1}/{len(self.slides)}")
        
        # ボタンの有効/無効状態を更新
        self.prev_btn.config(state=tk.NORMAL if self.current_slide > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_slide < len(self.slides) - 1 else tk.DISABLED)
        
        # 古いキャッシュを整理
        self._clean_other_caches()
        
        # 現在のスライドインデックス
        current_idx = self.current_slide
        
        # 音声が既に読み込まれている場合はボタンの表示を更新
        if current_idx in self.is_loaded and self.is_loaded[current_idx]:
            self.speak_btn.config(bg=self.accent_green, fg="black", text="▶ 音声再生", state=tk.NORMAL)
            self.status_label.config(text="音声は読み込み済みです")
            log_message(f"スライド {current_idx+1}/{len(self.slides)} は既に読み込み済みです", 
                      level="INFO", prefix="音声読み込み")
        else:
            # 音声が読み込まれていない場合は再生ボタンをグレーアウト
            self.speak_btn.config(bg="#cccccc", fg="black", text="音声未読込", state=tk.DISABLED)
            self.status_label.config(text="「音声読み込み」ボタンを押して音声を準備してください")
            log_message(f"スライド {current_idx+1}/{len(self.slides)} の音声は未読み込みです", 
                      level="INFO", prefix="音声読み込み")
        
    def next_slide(self):
        """次のスライドへ移動"""
        if self.current_slide < len(self.slides) - 1:
            # 音声再生を確実に停止
            self.stop_speaking()
            
            # 次のスライドに移動
            self.current_slide += 1
            self.show_slide()
            
    def prev_slide(self):
        """前のスライドへ移動"""
        if self.current_slide > 0:
            # 音声再生を確実に停止
            self.stop_speaking()
            
            # 前のスライドに移動
            self.current_slide -= 1
            self.show_slide()
            
    def speak_slide(self):
        """現在のスライドを音声で読み上げる"""
        # 既に再生中の場合は停止する
        if self.is_speaking:
            self.stop_speaking()
            return
            
        if not self.slides:
            return
            
        current_idx = self.current_slide
        
        # 読み込み中なら待つように促す
        if current_idx in self.is_loading and self.is_loading[current_idx]:
            self.status_label.config(text="音声読み込み中です。完了するまでお待ちください")
            return
            
        # キャッシュされた音声がある場合のみ再生
        if current_idx in self.audio_cache and os.path.exists(self.audio_cache[current_idx]):
            self.is_speaking = True
            self.speak_btn.config(text="⏸ 再生中...", state=tk.DISABLED)
            
            # 音声ファイルを再生
            audio_file = self.audio_cache[current_idx]
            self.status_label.config(text="音声再生中...")
            
            # スレッドで再生
            self.speak_thread = threading.Thread(target=self._play_cached_audio, args=(audio_file,))
            self.speak_thread.daemon = True
            self.speak_thread.start()
        else:
            # 読み込まれていない場合は読み込みを促す
            self.status_label.config(text="音声が読み込まれていません。「音声読み込み」ボタンを押してください")
            return
    
    def _play_cached_audio(self, audio_file):
        """キャッシュされた音声ファイルを再生する"""
        try:
            # 現在のスライド情報を取得
            current_idx = self.current_slide
            slide_info = f"スライド {current_idx+1}/{len(self.slides)}"
            
            log_message(f"キャッシュ音声の再生を開始します ({slide_info})", 
                      level="INFO", prefix="音声再生")
            
            # 再生プロセスを開始
            self.speak_process = subprocess.Popen(['afplay', audio_file])
            
            # プロセスが終了するまで待機
            while self.is_speaking and self.speak_process.poll() is None:
                time.sleep(0.01)
            
            if self.is_speaking:
                # 正常終了の場合（停止ボタンが押されなかった場合）
                log_message(f"キャッシュ音声の再生が完了しました ({slide_info})", 
                          level="SUCCESS", prefix="音声再生")
            else:
                # 停止ボタンが押された場合
                log_message(f"キャッシュ音声の再生が停止されました ({slide_info})", 
                          level="INFO", prefix="音声再生")
                
        except Exception as e:
            log_message(f"キャッシュ音声再生エラー: {e}", level="ERROR", prefix="音声再生")
            import traceback
            traceback.print_exc()
        finally:
            # UI更新
            self.root.after(0, self._reset_speak_button)
    
    def start_audio_preload(self):
        """現在のスライドの音声読み込みを開始"""
        # すでに読み込み済みの場合はスキップ
        current_idx = self.current_slide
        if current_idx in self.is_loaded and self.is_loaded[current_idx]:
            self.status_label.config(text="音声は読み込み済みです")
            log_message(f"スライド {current_idx+1}/{len(self.slides)} は既に読み込み済みです", 
                      level="INFO", prefix="音声読み込み")
            # 読み込み済みの場合は再生ボタンの表示を更新して有効化
            self.speak_btn.config(bg=self.accent_green, fg="black", text="音声再生 ▶", state=tk.NORMAL)
            return
            
        # 読み込み中の場合はスキップ (安全のため残しておく)
        if current_idx in self.is_loading and self.is_loading[current_idx]:
            self.status_label.config(text="音声読み込み中です...")
            log_message(f"スライド {current_idx+1}/{len(self.slides)} の音声を読み込み中です", 
                      level="INFO", prefix="音声読み込み")
            return
            
        # エンジン種別を取得
        engine_type = "VOICEVOX" if self.use_voicevox else "Google TTS" if self.use_gtts else "macOS say"
        
        # 読み込み中表示（詳細情報を含める）
        self.is_loading[current_idx] = True
        load_message = f"音声を読み込んでいます... ({engine_type}, {self.speech_rate}WPM)"
        
        # VOICEVOX使用時は話者情報も表示
        if self.use_voicevox:
            speaker_name = self.speaker_var.get()
            load_message = f"音声を読み込んでいます... ({engine_type}, {speaker_name}, {self.speech_rate}WPM)"
        
        self.status_label.config(text=load_message)
        
        # 進行状況表示
        self.progress_var.set("⏳")
        
        # 読み込み中は再生ボタンを無効化
        self.speak_btn.config(state=tk.DISABLED)
        
        # エンジン情報をログに出力
        log_message(f"スライド {current_idx+1}/{len(self.slides)} の音声読み込みを開始します", 
                  level="INFO", prefix="音声読み込み")
        log_message(f"使用エンジン: {engine_type}, 速度: {self.speech_rate}WPM", 
                  level="DEBUG", prefix="音声読み込み")
        
        # UI更新を反映するために一度処理を譲る
        self.root.update()
        
        try:
            # 音声読み込み処理をメインスレッドで実行 (UIブロックするが、スレッド競合を防ぐ)
            self._load_audio_synchronous(current_idx)
        except Exception as e:
            log_message(f"音声読み込みエラー: {e}", level="ERROR", prefix="音声読み込み")
            import traceback
            traceback.print_exc()
            self.is_loading[current_idx] = False
            self._update_load_status(False, f"エラー: {str(e)}")
    
    def _load_audio_synchronous(self, slide_idx):
        """同期的に音声を読み込む（スレッドを使わずにメインスレッドで実行）"""
        # スライドのテキストを取得
        text = self.slides[slide_idx]
        
        # テキスト処理
        lines = self._process_text_for_speech(text)
        combined_text = " ".join([l for l in lines if l.strip()])
        
        # スライドIDのプレフィックス
        slide_prefix = f"スライド{slide_idx+1}/{len(self.slides)}"
        
        log_message(f"処理テキスト: {len(combined_text)}文字, {len(lines)}行", 
                  level="DEBUG", prefix=slide_prefix)
        
        if not combined_text:
            # テキストが空の場合は何もしない
            self.is_loading[slide_idx] = False
            log_message("テキストが空のため読み込みをスキップします", level="WARN", prefix=slide_prefix)
            self._update_load_status(False, "テキストが空です")
            return
            
        # 選択した音声エンジンに応じて処理
        # VOICEVOXの場合、必要に応じて起動
        if self.use_voicevox:
            if self.auto_start_voicevox.get() == 1 and not is_voicevox_engine_running():
                log_message("VOICEVOXエンジンの自動起動を試みます", level="INFO", prefix=slide_prefix)
                self.status_label.config(text="VOICEVOXエンジンを起動中...")
                self.root.update()  # UI更新を反映
                
                if not start_voicevox_engine():
                    self.is_loading[slide_idx] = False
                    log_message("VOICEVOXエンジンの起動に失敗しました", level="ERROR", prefix=slide_prefix)
                    self._update_load_status(False, "VOICEVOXエンジンを起動できません")
                    return
                else:
                    log_message("VOICEVOXエンジンの起動に成功しました", level="SUCCESS", prefix=slide_prefix)
        
        # 音声ファイル生成
        temp_file = None
        
        # ファイル生成開始ログ
        engine_type = "VOICEVOX" if self.use_voicevox and is_voicevox_engine_running() else "Google TTS" if self.use_gtts and GTTS_AVAILABLE else "macOS say"
        log_message(f"{engine_type}で音声ファイル生成を開始します", level="INFO", prefix=slide_prefix)
        
        # 状態更新
        self.status_label.config(text=f"{engine_type}で音声を生成中...")
        self.root.update()  # UI更新を反映
        
        if self.use_voicevox and is_voicevox_engine_running():
            # VOICEVOXで音声ファイル生成
            temp_file = self._generate_voicevox_audio(combined_text)
        elif self.use_gtts and GTTS_AVAILABLE:
            # Google TTSで音声ファイル生成
            temp_file = self._generate_gtts_audio(combined_text)
        else:
            # macOSのsayコマンドで音声ファイル生成
            temp_file = self._generate_say_audio(combined_text)
        
        if temp_file:
            # 既存のキャッシュがあれば削除
            if slide_idx in self.audio_cache and os.path.exists(self.audio_cache[slide_idx]):
                try:
                    os.unlink(self.audio_cache[slide_idx])
                    log_message(f"既存のキャッシュファイルを削除しました: {self.audio_cache[slide_idx]}", 
                              level="DEBUG", prefix=slide_prefix)
                except Exception as e:
                    log_message(f"キャッシュファイル削除エラー: {e}", level="WARN", prefix=slide_prefix)
            
            # キャッシュに保存
            self.audio_cache[slide_idx] = temp_file
            self.is_loaded[slide_idx] = True
            self.is_loading[slide_idx] = False
            
            file_size = os.path.getsize(temp_file) / 1024  # KB単位
            log_message(f"音声ファイル生成完了: {temp_file} ({file_size:.1f}KB)", 
                      level="SUCCESS", prefix=slide_prefix)
            
            # 成功ステータスを更新
            self._update_load_status(True)
        else:
            self.is_loading[slide_idx] = False
            log_message("音声ファイル生成に失敗しました", level="ERROR", prefix=slide_prefix)
            self._update_load_status(False, "音声合成に失敗しました")

    def _load_audio_thread(self, slide_idx, is_current=True):
        """バックグラウンドで音声を読み込む（互換性のために残す）"""
        try:
            # スライドのテキストを取得
            text = self.slides[slide_idx]
            
            # テキスト処理
            lines = self._process_text_for_speech(text)
            combined_text = " ".join([l for l in lines if l.strip()])
            
            # スライドIDのプレフィックス
            slide_prefix = f"スライド{slide_idx+1}/{len(self.slides)}"
            
            log_message(f"処理テキスト: {len(combined_text)}文字, {len(lines)}行", 
                      level="DEBUG", prefix=slide_prefix)
            
            if not combined_text:
                # テキストが空の場合は何もしない
                self.is_loading[slide_idx] = False
                log_message("テキストが空のため読み込みをスキップします", level="WARN", prefix=slide_prefix)
                if is_current:
                    self.root.after(0, lambda: self._update_load_status(False, "テキストが空です"))
                return
                
            # 選択した音声エンジンに応じて処理
            # VOICEVOXの場合、必要に応じて起動
            if self.use_voicevox:
                if self.auto_start_voicevox.get() == 1 and not is_voicevox_engine_running():
                    log_message("VOICEVOXエンジンの自動起動を試みます", level="INFO", prefix=slide_prefix)
                    if not start_voicevox_engine():
                        self.is_loading[slide_idx] = False
                        log_message("VOICEVOXエンジンの起動に失敗しました", level="ERROR", prefix=slide_prefix)
                        if is_current:
                            self.root.after(0, lambda: self._update_load_status(False, "VOICEVOXエンジンを起動できません"))
                        return
                    else:
                        log_message("VOICEVOXエンジンの起動に成功しました", level="SUCCESS", prefix=slide_prefix)
            
            # 音声ファイル生成
            temp_file = None
            
            # ファイル生成開始ログ
            engine_type = "VOICEVOX" if self.use_voicevox and is_voicevox_engine_running() else "Google TTS" if self.use_gtts and GTTS_AVAILABLE else "macOS say"
            log_message(f"{engine_type}で音声ファイル生成を開始します", level="INFO", prefix=slide_prefix)
            
            if self.use_voicevox and is_voicevox_engine_running():
                # VOICEVOXで音声ファイル生成
                temp_file = self._generate_voicevox_audio(combined_text)
            elif self.use_gtts and GTTS_AVAILABLE:
                # Google TTSで音声ファイル生成
                temp_file = self._generate_gtts_audio(combined_text)
            else:
                # macOSのsayコマンドで音声ファイル生成
                temp_file = self._generate_say_audio(combined_text)
            
            if temp_file:
                # キャッシュに保存
                if slide_idx in self.audio_cache and os.path.exists(self.audio_cache[slide_idx]):
                    try:
                        os.unlink(self.audio_cache[slide_idx])
                        log_message(f"既存のキャッシュファイルを削除しました: {self.audio_cache[slide_idx]}", 
                                  level="DEBUG", prefix=slide_prefix)
                    except Exception as e:
                        log_message(f"キャッシュファイル削除エラー: {e}", level="WARN", prefix=slide_prefix)
                
                self.audio_cache[slide_idx] = temp_file
                self.is_loaded[slide_idx] = True
                self.is_loading[slide_idx] = False
                
                file_size = os.path.getsize(temp_file) / 1024  # KB単位
                log_message(f"音声ファイル生成完了: {temp_file} ({file_size:.1f}KB)", 
                          level="SUCCESS", prefix=slide_prefix)
                
                if is_current:
                    self.root.after(0, lambda: self._update_load_status(True))
            else:
                self.is_loading[slide_idx] = False
                log_message("音声ファイル生成に失敗しました", level="ERROR", prefix=slide_prefix)
                if is_current:
                    self.root.after(0, lambda: self._update_load_status(False, "音声合成に失敗しました"))
        except Exception as e:
            log_message(f"音声読み込みエラー: {e}", level="ERROR", prefix=f"スライド{slide_idx+1}")
            import traceback
            traceback.print_exc()  # スタックトレースを出力
            self.is_loading[slide_idx] = False
            if is_current:
                self.root.after(0, lambda: self._update_load_status(False, f"エラー: {str(e)}"))
    
    def _update_load_status(self, success, message=None):
        """読み込み状態とステータスを更新する（同期的に実行）"""
        try:
            current_idx = self.current_slide
            slide_info = f"スライド {current_idx+1}/{len(self.slides)}"
            
            if success:
                # エンジン種別を取得
                engine_type = "VOICEVOX" if self.use_voicevox else "Google TTS" if self.use_gtts else "macOS say"
                
                # 音声ファイルの情報を取得
                file_info = ""
                if current_idx in self.audio_cache and os.path.exists(self.audio_cache[current_idx]):
                    file_path = self.audio_cache[current_idx]
                    file_size = os.path.getsize(file_path) / 1024  # KB単位
                    file_info = f"({file_size:.1f}KB)"
                
                # ログメッセージを生成
                log_message(f"音声の読み込みが完了しました {file_info} ({slide_info})", 
                          level="SUCCESS", prefix="音声読み込み")
                
                # 成功メッセージを表示 (エンジン情報を含める)
                success_msg = f"音声の読み込みが完了しました {file_info}"
                
                # VOICEVOX使用時は話者情報も表示
                if self.use_voicevox:
                    speaker_name = self.speaker_var.get()
                    success_msg = f"音声の読み込みが完了しました - {engine_type}, {speaker_name} {file_info}"
                
                # 直接UI更新（同期的な処理のため）
                self.status_label.config(text=success_msg)
                self.progress_var.set("✅")  # 完了マーク
                self.speak_btn.config(bg=self.accent_green, fg="black", text="▶ 音声再生", state=tk.NORMAL)
                
                # UIを更新
                self.root.update()
                
                # 数秒後に進捗表示を消す（タイマーはそのまま使用）
                self.root.after(3000, self._clear_progress_var_safe)
            else:
                error_msg = message or "音声の読み込みに失敗しました"
                log_message(f"音声読み込みエラー: {error_msg} ({slide_info})", level="ERROR", prefix="音声読み込み")
                
                # 詳細なエラーメッセージをコンソールに出力（デバッグ用）
                engine_type = "VOICEVOX" if self.use_voicevox else "Google TTS" if self.use_gtts else "macOS say"
                log_message(f"エンジン: {engine_type}", level="DEBUG", prefix="詳細情報")
                log_message(f"読み上げ速度: {self.speech_rate} WPM", level="DEBUG", prefix="詳細情報")
                if self.use_voicevox:
                    log_message(f"話者ID: {self.voicevox_speaker}", level="DEBUG", prefix="詳細情報")
                    engine_status = "起動中" if is_voicevox_engine_running() else "停止中"
                    log_message(f"VOICEVOXエンジン状態: {engine_status}", level="DEBUG", prefix="詳細情報")
                
                # UI表示を更新（直接更新）
                self.status_label.config(text=error_msg)
                self.progress_var.set("❌")  # エラーマーク
                # 再生ボタンを標準状態に戻して有効化
                self.speak_btn.config(bg=self.accent_green, fg="black", text="音声再生", state=tk.NORMAL)
                
                # UIを更新
                self.root.update()
                
                # 数秒後に進捗表示を消す
                self.root.after(3000, self._clear_progress_var_safe)
        except Exception as e:
            log_message(f"ステータス更新エラー: {e}", level="ERROR", prefix="UI更新")
            import traceback
            traceback.print_exc()  # スタックトレースを出力して問題箇所を特定しやすくする
            # 最低限のUIリカバリーを試みる
            try:
                self.status_label.config(text="ステータス更新中にエラーが発生しました")
                self.progress_var.set("⚠️")  # 警告マーク
                self.speak_btn.config(state=tk.NORMAL)
                # UIを更新
                self.root.update()
                # 数秒後に進捗表示を消す
                self.root.after(5000, self._clear_progress_var_safe)
            except:
                pass  # この時点でさらにエラーが発生しても無視
    
    # アニメーション関連のメソッドを削除（同期的な処理に変更したため不要）
    # アニメーションが必要な場合は、別の方法で実装
    
    
    def _clean_other_caches(self):
        """現在のスライド以外のキャッシュをすべて削除する"""
        current_idx = self.current_slide
        slides_to_clean = []
        
        # 削除対象のスライドを特定
        for idx in list(self.audio_cache.keys()):
            if idx != current_idx:
                slides_to_clean.append(idx)
        
        # 削除処理
        for idx in slides_to_clean:
            if idx in self.audio_cache and os.path.exists(self.audio_cache[idx]):
                try:
                    # ファイルを削除
                    os.unlink(self.audio_cache[idx])
                    log_message(f"スライド {idx+1} のキャッシュを削除しました", 
                              level="INFO", prefix="キャッシュ整理")
                except Exception as e:
                    log_message(f"キャッシュ削除エラー: {e}", level="ERROR", prefix="キャッシュ整理")
            
            # キャッシュ情報をリセット
            self.audio_cache.pop(idx, None)
            self.is_loaded.pop(idx, None)
            self.is_loading.pop(idx, None)
            
        # 削除したスライド数をログに出力
        if slides_to_clean:
            log_message(f"{len(slides_to_clean)}個のキャッシュを整理しました", 
                      level="INFO", prefix="キャッシュ整理")
    
    def _clear_progress_var_safe(self):
        """進捗表示を安全にクリアする（タイマーコールバック用）"""
        try:
            # 既に破棄されているウィジェットでの操作を避ける
            if not self.root or not self.root.winfo_exists():
                return
                
            # progress_var属性が存在するか確認
            if hasattr(self, 'progress_var'):
                self.progress_var.set("")
                log_message("進捗表示をクリアしました", level="DEBUG", prefix="UI")
        except Exception as e:
            log_message(f"進捗表示クリアエラー: {e}", level="ERROR", prefix="UI")
            import traceback
            traceback.print_exc()  # スタックトレースを出力
    
    def _generate_voicevox_audio(self, text):
        """VOICEVOXを使用してテキストから音声ファイルを生成する"""
        temp_file = None
        try:
            # 音声合成クエリ作成
            log_message(f"VOICEVOX音声合成クエリを作成中 (文字数: {len(text)})", level="DEBUG", prefix="VOICEVOX")
            query_response = requests.post(
                f"{self.voicevox_url}/audio_query",
                params={'text': text, 'speaker': self.voicevox_speaker}
            )
            
            if query_response.status_code != 200:
                log_message(f"VOICEVOX音声合成クエリエラー: {query_response.status_code}", level="ERROR", prefix="VOICEVOX")
                return None
                
            query = query_response.json()
            
            # 速度を設定（speech_rateから適切な比率に変換）
            # 標準速度（220WPM）との比率を計算
            speed_ratio = self.speech_rate / 220.0
            # 範囲を拡大（0.5～3.0）してより速い再生をサポート
            speed_scale = max(0.5, min(3.0, speed_ratio))
            query['speedScale'] = speed_scale
            
            log_message(f"VOICEVOX合成パラメータ: speedScale={speed_scale:.2f}, speaker={self.voicevox_speaker}", 
                      level="DEBUG", prefix="VOICEVOX")
            
            # 音声合成実行
            log_message(f"VOICEVOX音声合成を実行中", level="DEBUG", prefix="VOICEVOX")
            synthesis_response = requests.post(
                f"{self.voicevox_url}/synthesis",
                params={'speaker': self.voicevox_speaker},
                data=json.dumps(query)
            )
            
            if synthesis_response.status_code != 200:
                log_message(f"VOICEVOX音声合成実行エラー: {synthesis_response.status_code}", level="ERROR", prefix="VOICEVOX")
                return None
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as fp:
                temp_file = fp.name
                fp.write(synthesis_response.content)
                log_message(f"VOICEVOXの一時ファイルを作成しました: {temp_file}", level="INFO", prefix="VOICEVOX")
            
            return temp_file
        except Exception as e:
            log_message(f"VOICEVOX音声ファイル生成エラー: {e}", level="ERROR", prefix="VOICEVOX")
            import traceback
            traceback.print_exc()
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    log_message(f"エラーにより一時ファイルを削除しました: {temp_file}", level="DEBUG", prefix="VOICEVOX")
                except:
                    pass
            return None
    
    def _generate_gtts_audio(self, text):
        """Google TTSを使用してテキストから音声ファイルを生成する"""
        temp_file = None
        try:
            # Google TTSで音声合成
            log_message(f"Google TTS音声合成を開始 (文字数: {len(text)})", level="DEBUG", prefix="Google TTS")
            tts = gTTS(text=text, lang='ja', slow=False)
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_file = fp.name
            
            tts.save(temp_file)
            log_message(f"Google TTSの一時ファイルを作成しました: {temp_file}", level="INFO", prefix="Google TTS")
            
            return temp_file
        except Exception as e:
            log_message(f"Google TTS音声ファイル生成エラー: {e}", level="ERROR", prefix="Google TTS")
            import traceback
            traceback.print_exc()
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    log_message(f"エラーにより一時ファイルを削除しました: {temp_file}", level="DEBUG", prefix="Google TTS")
                except:
                    pass
            return None
    
    def _generate_say_audio(self, text):
        """macOSのsayコマンドを使用してテキストから音声ファイルを生成する"""
        temp_file = None
        try:
            # 一時ファイルを作成
            with tempfile.NamedTemporaryFile(delete=False, suffix='.aiff') as fp:
                temp_file = fp.name
            
            log_message(f"macOS say音声合成を開始 (文字数: {len(text)}, 速度: {self.speech_rate}WPM)", 
                      level="DEBUG", prefix="macOS say")
            
            # sayコマンドで音声ファイルを生成
            result = subprocess.run(['say', '-r', str(self.speech_rate), '-o', temp_file, text], 
                                  check=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                log_message(f"sayコマンドの一時ファイルを作成しました: {temp_file}", level="INFO", prefix="macOS say")
            else:
                log_message(f"sayコマンドエラー: {result.stderr}", level="ERROR", prefix="macOS say")
                return None
            
            return temp_file
        except Exception as e:
            log_message(f"sayコマンド音声ファイル生成エラー: {e}", level="ERROR", prefix="macOS say")
            import traceback
            traceback.print_exc()
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    log_message(f"エラーにより一時ファイルを削除しました: {temp_file}", level="DEBUG", prefix="macOS say")
                except:
                    pass
            return None
    
    def _process_text_for_speech(self, text):
        """読み上げ用にテキストを処理する"""
        # 改行ごとに区切って配列に格納
        lines = []
        
        for line in text.split('\n'):
            # 空行や空白行をスキップ
            if not line.strip():
                continue
                
            # Markdown記法を除去して読みやすくする
            # 見出し記法を除去 (# ##, ###, etc.) - すべてのレベルの見出しに対応
            clean_line = re.sub(r'^#+\s*', '', line)  # #で始まる行の#をすべて削除
            
            # 強調記法を除去 (**bold**, *italic*)
            clean_line = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_line)  # **bold** -> bold
            clean_line = re.sub(r'\*(.+?)\*', r'\1', clean_line)        # *italic* -> italic
            
            # リスト記法を除去 (-, *, 1. etc.)
            clean_line = re.sub(r'^\s*[-*+]\s+', '', clean_line)      # - item -> item
            clean_line = re.sub(r'^\s*\d+\.\s+', '', clean_line)      # 1. item -> item
            
            # リンク記法を除去 [text](url)
            clean_line = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', clean_line)  # [text](url) -> text
            
            # コードブロック記法を除去 (`code`)
            clean_line = re.sub(r'`(.+?)`', r'\1', clean_line)          # `code` -> code
            
            # 水平線をスキップ (---)
            if re.match(r'^-{3,}$|^\*{3,}$|^_{3,}$', clean_line):
                continue
                
            # コメントを除去 <!-- comment -->
            clean_line = re.sub(r'<!--.*?-->', '', clean_line)
            
            if clean_line.strip():
                lines.append(clean_line.strip())
        
        return lines
    
    def check_voicevox_available(self):
        """VOICEVOXエンジンが利用可能かチェック"""
        if not REQUESTS_AVAILABLE:
            return False
            
        try:
            response = requests.get(f"{self.voicevox_url}/version", timeout=1)
            return response.status_code == 200
        except:
            return False
    
    def speak_with_voicevox(self, text):
        """VOICEVOXを使用してテキストを音声合成"""
        temp_file = None
        try:
            # 音声合成クエリ作成
            query_response = requests.post(
                f"{self.voicevox_url}/audio_query",
                params={'text': text, 'speaker': self.voicevox_speaker}
            )
            query = query_response.json()
            
            # 速度を設定（speech_rateから適切な比率に変換）
            # 標準速度（220WPM）との比率を計算
            speed_ratio = self.speech_rate / 220.0
            # 範囲を拡大（0.5～3.0）してより速い再生をサポート
            speed_scale = max(0.5, min(3.0, speed_ratio))
            query['speedScale'] = speed_scale
            print(f"VOICEVOX読み上げ速度: {self.speech_rate}WPM (speedScale: {speed_scale:.2f})")
            
            # 音声合成実行
            synthesis_response = requests.post(
                f"{self.voicevox_url}/synthesis",
                params={'speaker': self.voicevox_speaker},
                data=json.dumps(query)
            )
            
            # 音声合成が停止された場合は処理を中断
            if not self.is_speaking:
                return False
            
            # 一時ファイルに保存して再生
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as fp:
                temp_file = fp.name
                fp.write(synthesis_response.content)
                print(f"VOICEVOXの一時ファイルを作成しました: {temp_file}")
            
            # 再生プロセスを開始（wait()しない）
            self.speak_process = subprocess.Popen(['afplay', temp_file])
            
            # プロセスが終了するまで定期的にチェック（より短い間隔でチェック）
            while self.is_speaking and self.speak_process.poll() is None:
                time.sleep(0.01)  # 10ミリ秒ごとにチェック（より高速に応答）
            
            # 再生が正常に完了したらファイルを削除
            if temp_file and os.path.exists(temp_file) and self.is_speaking:
                try:
                    os.unlink(temp_file)
                    print(f"VOICEVOXの一時ファイルを削除しました: {temp_file}")
                except Exception as e:
                    print(f"一時ファイル削除エラー: {e}")
            
            return True
        except Exception as e:
            print(f"VOICEVOX連携エラー: {e}")
            # エラー時にも一時ファイルがあれば削除を試みる
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
            return False
    
    def change_engine(self, engine_type):
        """音声合成エンジンを切り替える"""
        # すべてのフラグをリセット
        self.use_gtts = False
        self.use_voicevox = False
        
        # 選択されたエンジンをアクティブに
        if engine_type == "gtts" and GTTS_AVAILABLE:
            self.use_gtts = True
            engine_name = "Google TTS"
        elif engine_type == "voicevox":
            # VOICEVOXが利用可能かチェック
            if self.check_voicevox_available():
                self.use_voicevox = True
                selected_speaker = self.speaker_var.get()
                engine_name = f"VOICEVOX ({selected_speaker})"
            else:
                # 自動起動が有効なら、起動を試みる
                if self.auto_start_voicevox.get() == 1:
                    if self.start_voicevox_if_needed():
                        self.use_voicevox = True
                        selected_speaker = self.speaker_var.get()
                        engine_name = f"VOICEVOX ({selected_speaker})"
                    else:
                        log_message("VOICEVOXエンジンに接続できません。起動しているか確認してください。", 
                                  level="WARN", prefix="エンジン変更")
                        engine_name = "macOS say (フォールバック)"
                else:
                    log_message("VOICEVOXエンジンに接続できません。起動しているか確認してください。", 
                              level="WARN", prefix="エンジン変更")
                    engine_name = "macOS say (フォールバック)"
        else:
            engine_name = "macOS say"
        
        # ボタンの色を更新
        self.say_btn.config(bg=self.accent_blue if not (self.use_gtts or self.use_voicevox) else self.btn_bg)
        self.gtts_btn.config(bg=self.accent_blue if self.use_gtts else self.btn_bg)
        self.voicevox_btn.config(bg=self.accent_blue if self.use_voicevox else self.btn_bg)
        
        self.status_label.config(text=f"音声エンジンを {engine_name} に切り替えました")
        log_message(f"音声エンジンを {engine_name} に切り替えました", level="INFO", prefix="エンジン変更")
        
        # エンジンを変更した場合、現在のスライドの音声キャッシュをクリア
        if self.current_slide in self.audio_cache:
            try:
                if os.path.exists(self.audio_cache[self.current_slide]):
                    os.unlink(self.audio_cache[self.current_slide])
                    log_message(f"エンジン変更により音声キャッシュを削除: {self.audio_cache[self.current_slide]}", 
                              level="INFO", prefix="キャッシュ")
            except Exception as e:
                log_message(f"キャッシュ削除エラー: {e}", level="ERROR", prefix="キャッシュ")
            
            # キャッシュ情報をリセット
            self.audio_cache.pop(self.current_slide, None)
            self.is_loaded.pop(self.current_slide, None)
            
            # 音声の読み込みが必要であることを表示
            self.status_label.config(text=f"音声エンジンを {engine_name} に切り替えました。音声の再読み込みが必要です")
            # 再生ボタンをグレーアウト
            self.speak_btn.config(bg="#cccccc", fg="black", text="音声未読込", state=tk.DISABLED)
        
    def _speak_text(self, text):
        """テキストを音声で読み上げるバックグラウンド処理"""
        try:
            # 読み上げ用にテキストを処理
            lines = self._process_text_for_speech(text)
            
            if self.use_voicevox:
                # VOICEVOXで読み上げ - 複数行をまとめて処理
                selected_speaker = self.speaker_var.get()
                print(f"VOICEVOXで音声再生を開始します（話者: {selected_speaker}）")
                
                # 複数行を結合（空行は除外）
                combined_text = " ".join([l for l in lines if l.strip()])
                
                if combined_text and self.is_speaking:
                    # まとめたテキストを一度に合成・再生
                    success = self.speak_with_voicevox(combined_text)
                    if not success:
                        print("VOICEVOX処理に失敗しました")
                
                print("音声再生が完了しました（VOICEVOX）")
            elif self.use_gtts and GTTS_AVAILABLE:
                # Google TTSで読み上げ
                print("Google TTSで音声再生を開始します")
                for i, line in enumerate(lines):
                    if not line:  # 空行はスキップ
                        continue
                        
                    # Google TTSで音声合成
                    tts = gTTS(text=line, lang='ja', slow=False)
                    
                    # 一時ファイルに保存
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                        temp_file = fp.name
                    
                    print(f"音声ファイルを生成中: {temp_file} (行 {i+1}/{len(lines)})")
                    tts.save(temp_file)
                    
                    # 再生が停止されたか確認
                    if not self.is_speaking:
                        os.unlink(temp_file)
                        break
                    
                    # macOSのafplayコマンドで再生（速度調整を適用）
                    # afplayは直接速度を調整できないため、比率を計算して調整
                    # 標準速度（220WPM）との比率を計算
                    speed_ratio = self.speech_rate / 220.0
                    if speed_ratio != 1.0:
                        # macOSの場合、afplayに-rオプションで速度調整できる（0.5〜2.0の範囲）
                        speed_arg = max(0.5, min(2.0, speed_ratio))  # 0.5〜2.0の範囲に制限
                        self.speak_process = subprocess.Popen(['afplay', '-r', str(speed_arg), temp_file])
                    else:
                        self.speak_process = subprocess.Popen(['afplay', temp_file])
                    self.speak_process.wait()
                    
                    # 一時ファイルを削除
                    os.unlink(temp_file)
                    
                    # 改行ごとに間を挟む
                    if i < len(lines) - 1 and self.is_speaking:
                        # 読み上げが速いほど短いポーズに調整
                        adjusted_pause = self.pause_time * (220 / self.speech_rate)
                        time.sleep(adjusted_pause)
            
                print("音声再生が完了しました（Google TTS）")
            else:
                # macOSのsayコマンドを使用
                print("macOSのsayコマンドで音声再生を開始します")
                for i, line in enumerate(lines):
                    if not line:  # 空行はスキップ
                        continue
                        
                    # 再生が停止されたか確認
                    if not self.is_speaking:
                        break
                    
                    # テキストを読み上げ、速度を設定値に合わせる
                    self.speak_process = subprocess.Popen(['say', '-r', str(self.speech_rate), line])
                    self.speak_process.wait()
                    
                    # 改行ごとに間を挟む
                    if i < len(lines) - 1 and self.is_speaking:
                        # 読み上げが速いほど短いポーズに調整
                        adjusted_pause = self.pause_time * (220 / self.speech_rate)
                        time.sleep(adjusted_pause)
        except Exception as e:
            print(f"音声再生エラー: {e}")
        finally:
            # UI更新はメインスレッドで行う
            self.root.after(0, self._reset_speak_button)
    
    def update_speech_rate(self, value):
        """スライダーの値から読み上げ速度を更新する"""
        self.speech_rate = int(float(value))
        self.speed_value_label.config(text=f"{self.speech_rate} WPM")
        
        # 読み上げ速度を変更した場合、現在のスライドの音声キャッシュをクリア
        if self.current_slide in self.audio_cache:
            try:
                if os.path.exists(self.audio_cache[self.current_slide]):
                    os.unlink(self.audio_cache[self.current_slide])
                    log_message(f"速度変更により音声キャッシュを削除: {self.audio_cache[self.current_slide]}", 
                              level="INFO", prefix="キャッシュ")
            except Exception as e:
                log_message(f"キャッシュ削除エラー: {e}", level="ERROR", prefix="キャッシュ")
            
            # キャッシュ情報をリセット
            self.audio_cache.pop(self.current_slide, None)
            self.is_loaded.pop(self.current_slide, None)
            
            # 音声の読み込みが必要であることを表示
            self.status_label.config(text=f"速度を {self.speech_rate} WPM に変更しました。音声の再読み込みが必要です")
            # 再生ボタンをグレーアウト
            self.speak_btn.config(bg="#cccccc", fg="black", text="音声未読込", state=tk.DISABLED)
    
    def increase_speed(self):
        """読み上げ速度を上げる（上矢印キー用）"""
        new_value = min(self.speech_rate + 10, self.max_rate)
        self.speed_slider.set(new_value)
        
    def decrease_speed(self):
        """読み上げ速度を下げる（下矢印キー用）"""
        new_value = max(self.speech_rate - 10, self.min_rate)
        self.speed_slider.set(new_value)
    
    def _reset_speak_button(self):
        """音声再生ボタンをリセット"""
        # 現在のスライドインデックス
        current_idx = self.current_slide
        
        # 音声が読み込み済みかどうかで表示を変える
        if current_idx in self.is_loaded and self.is_loaded[current_idx]:
            # 読み込み済みの場合は再生可能に
            self.speak_btn.config(text="▶ 音声再生", state=tk.NORMAL, bg=self.accent_green)
        else:
            # 未読み込みの場合はグレーアウト
            self.speak_btn.config(text="音声未読込", state=tk.DISABLED, bg="#cccccc")
    
    def stop_speaking(self):
        """音声再生を停止"""
        if self.is_speaking:
            try:
                # 先にフラグを停止に設定
                self.is_speaking = False
                
                # プロセスが存在する場合は強制終了
                if self.speak_process:
                    self.speak_process.terminate()
                    # プロセス参照をクリア
                    self.speak_process = None
                
                # UIを更新
                self.root.after(0, self._reset_speak_button)
                self.status_label.config(text="再生を停止しました")
                
                # 読み込み中のスレッドがあれば停止
                for idx in list(self.is_loading.keys()):
                    if self.is_loading[idx]:
                        self.is_loading[idx] = False
                
            except Exception as e:
                print(f"音声停止エラー: {e}")

    def open_file(self):
        """ファイル選択ダイアログを開く"""
        file_path = filedialog.askopenfilename(
            title="台本ファイルを選択",
            filetypes=[("Markdown", "*.md"), ("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
            initialdir=os.path.dirname(self.script_path) if self.script_path else None
        )
        
        if file_path:
            # 現在再生中なら停止
            self.stop_speaking()
            
            # キャッシュをクリア
            for cache_file in self.audio_cache.values():
                if os.path.exists(cache_file):
                    try:
                        os.unlink(cache_file)
                    except:
                        pass
            
            self.audio_cache = {}
            self.is_loaded = {}
            self.is_loading = {}
            
            # 新しいファイルを読み込み
            self.load_file(file_path)

    def get_voicevox_speakers(self):
        """VOICEVOXから利用可能な話者リストを取得する"""
        try:
            if self.check_voicevox_available():
                response = requests.get(f"{self.voicevox_url}/speakers")
                if response.status_code == 200:
                    return response.json()
            return []
        except:
            return []
    
    def on_closing(self):
        """アプリケーション終了時の処理"""
        # 音声再生を停止
        self.stop_speaking()
        
        # 音声キャッシュの削除
        for cache_file in self.audio_cache.values():
            if os.path.exists(cache_file):
                try:
                    os.unlink(cache_file)
                except Exception:
                    pass
        
        # VOICEVOXエンジンを終了（自動起動した場合のみ）
        if voicevox_process:
            stop_voicevox_engine()
        
        # アプリケーションを終了
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleScriptReader(root)
    root.mainloop()