# スクリプトリーダー with VOICEVOX

マークダウン形式のスクリプト読み上げツール「スクリプトリーダー」にVOICEVOXを統合したアプリケーションです。
スライド形式の台本を表示し、高品質な日本語音声で読み上げることができます。

## 機能

- マークダウン形式のファイルをスライド単位で表示
- 3種類の音声エンジンによる読み上げ
  - macOS内蔵の「say」コマンド
  - Google Text-to-Speech (GTTSライブラリ使用)
  - VOICEVOX（高品質日本語音声合成エンジン）
- VOICEVOXの話者選択機能（四国めたん、ずんだもん、春日部つむぎなど）
- 読み上げ速度の調整（100〜660WPM）
- キーボードショートカット対応

## ディレクトリ構造

```
script_reader/
├── script_reader.py     # メインアプリケーション
├── README.md            # ドキュメント
├── CLAUDE.md            # Claude用指示書
└── Archive/             # アーカイブ資料
    ├── VOICEVOX統合設計書.md
    └── list_speakers.py
```

## 必要条件

- macOS（sayコマンドを使用するため）
- Python 3.6以上
- tkinter（GUIライブラリ）
- requests（VOICEVOXとの通信に使用）
- gTTS（オプション：Google TTSを使用する場合）
- VOICEVOX（オプション：VOICEVOXを使用する場合）

## セットアップ

1. リポジトリをクローンします：

```bash
git clone https://github.com/yourusername/script_reader.git
cd script_reader
```

2. 必要なPythonライブラリをインストールします：

```bash
pip install requests
pip install gTTS  # オプション：Google TTSを使用する場合
```

3. VOICEVOXをインストールします（オプション）：
   - [VOICEVOX公式サイト](https://voicevox.hiroshiba.jp/)からダウンロードしてインストールします
   - インストール後、VOICEVOXエディタを起動します（エンジンも同時に起動されます）

## 使い方

1. VOICEVOXを使用する場合は、先にVOICEVOXエディタを起動しておきます
2. スクリプトリーダーを起動します：

```bash
python script_reader.py
```

3. 「ファイルを開く」ボタンをクリックして、マークダウン形式の台本ファイルを選択します
4. 音声エンジンを選択します：
   - macOS say：macOSの標準音声合成を使用
   - Google TTS：Google Text-to-Speechを使用（インターネット接続が必要）
   - VOICEVOX：VOICEVOXを使用（事前にVOICEVOXエンジンを起動しておく必要があります）
5. VOICEVOXを使用する場合は、ドロップダウンメニューから話者を選択できます：
   - 四国めたん（ノーマル、あまあま、ツンツン、セクシー）
   - ずんだもん（ノーマル、あまあま、ツンツン）
   - 春日部つむぎ
   - 雨晴はう
   - 波音リツ
   - もち子さん
   - その他の話者
6. 「音声再生」ボタンをクリックして、現在のスライドを読み上げます

## キーボードショートカット

- スペースキー：音声再生/停止
- 左矢印キー：前のスライド
- 右矢印キー：次のスライド
- Escキー：音声停止
- Ctrl+O：ファイルを開く
- 上矢印キー：読み上げ速度を上げる
- 下矢印キー：読み上げ速度を下げる

## VOICEVOXについて

VOICEVOXは無料で使える高品質な日本語音声合成ソフトウェアです。
複数の話者（キャラクター）から選んで読み上げることができます。

VOICEVOXの詳細については[公式サイト](https://voicevox.hiroshiba.jp/)をご覧ください。

## 注意点

- VOICEVOXエンジンが起動していない場合、自動的にmacOS sayにフォールバックします
- VOICEVOXの利用には、requestsライブラリが必要です
- インターネット接続がない環境では、Google TTSは利用できません

## 最近の更新

- 音声再生プロセスのチェック間隔を短縮し、VOICEVOXでの複数行処理を改善
- 改行間のポーズ時間を短縮し、音声読み上げの応答性を向上
- VOICEVOXの最大読み上げ速度を660に変更し、速度設定を追加
- VOICEVOXの音声再生処理を改善し、一時ファイルの管理を強化
- VOICEVOX話者リストの更新と話者情報取得機能の追加