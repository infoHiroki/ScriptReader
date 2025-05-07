# スクリプトリーダーへのVOICEVOX統合設計書

## 1. 概要

マークダウン形式のスクリプト読み上げツール「スクリプトリーダー」に、高品質な日本語音声合成エンジン「VOICEVOX」を統合する設計書です。簡易的な実装を行い、必要に応じて機能拡張することを前提とします。

## 2. 前提条件

- ユーザーがVOICEVOXをローカルにインストール済みであること
- VOICEVOXエンジンが起動していること（デフォルトでは`http://localhost:50021`で起動）
- Python環境に`requests`ライブラリがインストールされていること

## 3. 実装方針

### 3.1 最小限の実装内容

- 既存の音声エンジン選択に「VOICEVOX」オプションを追加
- 最もシンプルなVOICEVOX連携機能の実装（話者IDは固定）
- エラー発生時は既存のmacOS sayコマンドにフォールバック

### 3.2 将来的な拡張オプション（初期実装では含まない）

- 話者選択機能（VOICEVOXの複数話者から選択）
- VOICEVOXの音声パラメータ調整（感情、速度、ピッチなど）
- VOICEVOXの自動起動機能
- 音声キャッシュ機能

## 4. コード修正概要

### 4.1 必要なライブラリ追加

```python
import requests
import json
```

### 4.2 クラス変数の追加

```python
# 音声合成エンジンの設定
self.use_gtts = False   # Google TTS
self.use_voicevox = False  # VOICEVOX
self.voicevox_speaker = 1  # デフォルト話者ID
self.voicevox_url = "http://localhost:50021"  # VOICEVOXエンジンのURL
```

### 4.3 UI修正

VOICEVOXエンジン選択ボタンの追加:

```python
# VOICEVOX選択ボタン
self.voicevox_btn = Button(engine_frame, text="VOICEVOX", 
                          command=lambda: self.change_engine("voicevox"),
                          font=("Helvetica", 12), 
                          bg=self.accent_blue if self.use_voicevox else self.btn_bg, 
                          fg="black")
self.voicevox_btn.pack(side=tk.LEFT, padx=5)
```

### 4.4 エンジン切り替え関数の修正

```python
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
            engine_name = "VOICEVOX"
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
```

### 4.5 VOICEVOX利用可能確認関数

```python
def check_voicevox_available(self):
    """VOICEVOXエンジンが利用可能かチェック"""
    try:
        response = requests.get(f"{self.voicevox_url}/version")
        return response.status_code == 200
    except:
        return False
```

### 4.6 VOICEVOX音声合成関数

```python
def speak_with_voicevox(self, text):
    """VOICEVOXを使用してテキストを音声合成"""
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
        
        # 一時ファイルに保存して再生
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as fp:
            temp_file = fp.name
            fp.write(synthesis_response.content)
        
        # 再生（既存のコードを流用）
        self.speak_process = subprocess.Popen(['afplay', temp_file])
        self.speak_process.wait()
        os.unlink(temp_file)
        
        return True
    except Exception as e:
        print(f"VOICEVOX連携エラー: {e}")
        return False
```

### 4.7 読み上げ処理部分の修正

```python
def _speak_text(self, text):
    """テキストを音声で読み上げるバックグラウンド処理"""
    try:
        # 読み上げ用にテキストを処理
        lines = self._process_text_for_speech(text)
        
        if self.use_voicevox:
            # VOICEVOXで読み上げ
            print("VOICEVOXで音声再生を開始します")
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
            # 既存のGoogle TTS処理
            # ...（既存コード）
        else:
            # 既存のmacOS say処理
            # ...（既存コード）
    except Exception as e:
        print(f"音声再生エラー: {e}")
    finally:
        # UI更新はメインスレッドで行う
        self.root.after(0, self._reset_speak_button)
```

## 5. 導入手順

1. VOICEVOXをインストール
   - 公式サイト（https://voicevox.hiroshiba.jp/）からダウンロード
   - インストール後、VOICEVOXエディタを起動（エンジンも同時に起動される）

2. Pythonライブラリのインストール
   ```
   pip install requests
   ```

3. スクリプトリーダーの起動
   - VOICEVOXを起動した状態でスクリプトリーダーを起動
   - 音声エンジン選択で「VOICEVOX」を選択

## 6. 今後の拡張案

- 話者選択機能の追加（UIにドロップダウンメニュー）
- 音声パラメータ調整（感情パラメータ、イントネーションなど）
- 音声キャッシュによるパフォーマンス向上
- VOICEVOXエンジンの自動起動機能

## 7. 注意点

- VOICEVOXエンジンが起動していない場合、自動的にmacOS sayにフォールバックする
- 初期実装では話者IDが固定されている（1番目の話者）
- エラー処理は最小限にしているため、例外的な状況では動作が不安定になる可能性がある