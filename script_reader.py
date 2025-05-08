import tkinter as tk
from tkinter import scrolledtext, Button, Label, Frame, filedialog, Scale, OptionMenu, StringVar
import os.path
import subprocess
import threading
import tempfile
import time
import re
import json

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

class SimpleScriptReader:
    def __init__(self, root):
        self.root = root
        self.root.title("シンプル台本リーダー")
        self.root.geometry("800x650")  # 高さを少し大きくして話者選択用のスペースを確保
        
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
        self.pause_time = 0.15  # 改行間のポーズ時間を短く
        self.min_rate = 100     # 最小読み上げ速度
        self.max_rate = 300     # 最大読み上げ速度
        
        # 音声合成エンジンの設定
        self.use_gtts = False   # Google TTS
        self.use_voicevox = False  # VOICEVOX
        self.voicevox_speaker = 1  # デフォルト話者ID
        self.voicevox_url = "http://localhost:50021"  # VOICEVOXエンジンのURL
        
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
        self.speak_btn = Button(control_frame, text="音声再生", command=self.speak_slide, 
                               font=("Helvetica", 12), bg=self.accent_green, fg="black")
        self.speak_btn.pack(side=tk.LEFT, padx=5)
        
        # 音声停止ボタン
        self.stop_btn = Button(control_frame, text="停止", command=self.stop_speaking, 
                              font=("Helvetica", 12), bg=self.accent_red, fg="black")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
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
        
        # VOICEVOX話者選択フレーム（新規追加）
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
    
    def change_speaker(self, *args):
        """VOICEVOXの話者を変更する"""
        selected_speaker = self.speaker_var.get()
        self.voicevox_speaker = VOICEVOX_SPEAKERS[selected_speaker]
        self.speaker_info_label.config(text=f"ID: {self.voicevox_speaker}")
        print(f"VOICEVOX話者を {selected_speaker} (ID: {self.voicevox_speaker}) に変更しました")
    
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
        
    def next_slide(self):
        """次のスライドへ移動"""
        if self.current_slide < len(self.slides) - 1:
            self.stop_speaking()
            self.current_slide += 1
            self.show_slide()
            
    def prev_slide(self):
        """前のスライドへ移動"""
        if self.current_slide > 0:
            self.stop_speaking()
            self.current_slide -= 1
            self.show_slide()
            
    def speak_slide(self):
        """現在のスライドを音声で読み上げる"""
        if self.is_speaking:
            self.stop_speaking()
            return
            
        if not self.slides:
            return
            
        self.is_speaking = True
        self.speak_btn.config(text="再生中...", state=tk.DISABLED)
        
        # スライドのテキストを取得
        text = self.slides[self.current_slide]
        print(f"音声再生開始: {len(text)}文字")
        
        # スレッドで音声再生を実行
        self.speak_thread = threading.Thread(target=self._speak_text, args=(text,))
        self.speak_thread.daemon = True
        self.speak_thread.start()
    
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
            response = requests.get(f"{self.voicevox_url}/version")
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
            
            # プロセスが終了するまで定期的にチェック
            while self.is_speaking and self.speak_process.poll() is None:
                time.sleep(0.1)  # 100ミリ秒ごとにチェック
            
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
                print("VOICEVOXエンジンに接続できません。起動しているか確認してください。")
                engine_name = "macOS say (フォールバック)"
        else:
            engine_name = "macOS say"
        
        # ボタンの色を更新
        self.say_btn.config(bg=self.accent_blue if not (self.use_gtts or self.use_voicevox) else self.btn_bg)
        self.gtts_btn.config(bg=self.accent_blue if self.use_gtts else self.btn_bg)
        self.voicevox_btn.config(bg=self.accent_blue if self.use_voicevox else self.btn_bg)
        
        print(f"音声エンジンを {engine_name} に切り替えました")
        
    def _speak_text(self, text):
        """テキストを音声で読み上げるバックグラウンド処理"""
        try:
            # 読み上げ用にテキストを処理
            lines = self._process_text_for_speech(text)
            
            if self.use_voicevox:
                # VOICEVOXで読み上げ
                selected_speaker = self.speaker_var.get()
                print(f"VOICEVOXで音声再生を開始します（話者: {selected_speaker}）")
                for i, line in enumerate(lines):
                    if not line:  # 空行はスキップ
                        continue
                        
                    # 再生が停止されたか確認
                    if not self.is_speaking:
                        break
                    
                    # VOICEVOXで音声合成・再生
                    success = self.speak_with_voicevox(line)
                    if not success:
                        # 失敗した場合はsayコマンドでフォールバック
                        self.speak_process = subprocess.Popen(['say', '-r', str(self.speech_rate), line])
                        self.speak_process.wait()
                    
                    # 改行ごとに間を挟む
                    if i < len(lines) - 1 and self.is_speaking:
                        adjusted_pause = self.pause_time * (220 / self.speech_rate)
                        time.sleep(adjusted_pause)
                
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
        # UI要素だけを更新（is_speakingフラグやspeak_processはstop_speaking内で処理）
        self.speak_btn.config(text="音声再生", state=tk.NORMAL)
    
    def stop_speaking(self):
        """音声再生を停止"""
        if self.is_speaking:
            try:
                # 先にフラグを停止に設定（これにより実行中のスレッドがループを抜ける）
                self.is_speaking = False
                
                # プロセスが存在する場合は強制終了
                if self.speak_process:
                    self.speak_process.terminate()
                    # プロセスが確実に終了するまで少し待機
                    self.speak_process.poll()
                    # プロセス参照をクリア
                    self.speak_process = None
                    
                # UIを更新
                self.root.after(0, self._reset_speak_button)
                print("音声再生を停止しました")
                
                # 一時ファイルが残っている可能性があるので確認
                temp_dir = tempfile.gettempdir()
                for file in os.listdir(temp_dir):
                    if file.endswith(('.mp3', '.wav')) and os.path.isfile(os.path.join(temp_dir, file)):
                        try:
                            # VOICEVOXとgTTSの両方の一時ファイルを検出するため、より広い条件で検索
                            if 'tmp' in file.lower() or (file.startswith('tmp') and (file.endswith('.wav') or file.endswith('.mp3'))):
                                full_path = os.path.join(temp_dir, file)
                                # ファイルが存在し、アクセス可能であれば削除
                                if os.path.exists(full_path) and os.access(full_path, os.W_OK):
                                    os.unlink(full_path)
                                    print(f"一時ファイルを削除しました: {full_path}")
                        except Exception as e:
                            print(f"一時ファイル削除エラー: {e}")
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
            self.load_file(file_path)

    def get_voicevox_speakers(self):
        """VOICEVOXから利用可能な話者リストを取得する（将来的な機能）"""
        try:
            if self.check_voicevox_available():
                response = requests.get(f"{self.voicevox_url}/speakers")
                if response.status_code == 200:
                    return response.json()
            return []
        except:
            return []

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleScriptReader(root)
    root.mainloop()