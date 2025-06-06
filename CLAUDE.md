# Claude 指示書

## プロジェクト概要
このプロジェクトは、マークダウン形式のスクリプト読み上げツール「スクリプトリーダー」に、VOICEVOXを統合するためのものです。

## 実行前の確認事項
- script_reader.pyを実行する前に、VOICEVOXエンジンが起動していることを確認する
- リクエストするためのrequestsライブラリがインストールされていることを確認する

## Claudeへの指示
1. コード修正時には、設計書の実装方針に従うこと
2. VOICEVOXエンジンとの連携に関するエラー処理を丁寧に行うこと
3. コードの可読性を保ちながら、機能拡張しやすい設計にすること
4. パフォーマンス面も考慮し、必要に応じて音声キャッシュ機能なども検討すること

## テスト手順
1. VOICEVOXエンジンを起動した状態でスクリプトリーダーを起動する
2. VOICEVOXエンジンが正常に接続できることを確認する
3. 文章を入力して読み上げが正常に行われることを確認する
4. 意図的にVOICEVOXエンジンを停止し、フォールバック機能が動作することを確認する

## 将来的な拡張方針
- 話者選択機能の追加
- 音声パラメータの調整機能
- VOICEVOXエンジンの自動起動機能
- 音声キャッシュ機能の実装