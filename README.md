# splitbills - レシート割り勘 LINE ボット

どの国のレシートでも対応可能な、シンプルで使いやすい割り勘計算 LINE ボットです。

## 機能

- 📷 レシート画像をOCRで自動読み取り
- 💰 金額を自動抽出（通貨記号は無視、数値のみ認識）
- 👥 人数を入力するだけで一人当たりの金額を計算
- 🎨 モダンなFlex UIデザイン
- 🆓 無料枠管理機能（月1000回のOCR制限）
- 🔒 セキュアな実装（HMAC署名検証）

## 動作フロー

1. レシート画像をLINEで送信
2. OCRが金額候補を自動抽出
3. Flexメッセージで金額を選択
4. 人数を入力
5. 一人当たりの金額を表示

## セットアップ手順

### 0) 事前準備

必要なツールをインストール：

```bash
# Google Cloud SDK
# macOS
brew install google-cloud-sdk

# Linux/WSL
curl https://sdk.cloud.google.com | bash

# Python 3.11
python3 --version  # 3.11.x であることを確認
```

### 1) GCP初期セットアップ & プロジェクト作成

```bash
# ログイン & ADC設定
gcloud auth login
gcloud auth application-default login

# プロジェクト作成（ID固定：splitbills）
gcloud projects create splitbills
gcloud config set project splitbills

# 必要API有効化
gcloud services enable vision.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

**注意**: `splitbills` というプロジェクトIDが既に使用されている場合は、下記の「代替ID手順」を参照してください。

### 2) サービスアカウント作成とIAM設定

```bash
# サービスアカウント作成
gcloud iam service-accounts create splitbills-sa \
    --display-name="splitbills Service Account"

# Cloud Vision API権限を付与
gcloud projects add-iam-policy-binding splitbills \
    --member="serviceAccount:splitbills-sa@splitbills.iam.gserviceaccount.com" \
    --role="roles/cloudvision.user"
```

### 3) 環境変数設定

```bash
# .env ファイルを作成
cp .env.example .env

# .env を編集して LINE の認証情報を設定
# LINE_CHANNEL_SECRET=your_channel_secret_here
# LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
```

### 4) LINE チャンネル設定（ユーザー作業）

**これはユーザーが手動で実施する必要があります：**

1. [LINE Developers Console](https://developers.line.biz/console/) にアクセス
2. 新規プロバイダーを作成（または既存のものを選択）
3. 「Messaging API」チャンネルを作成
4. チャンネル基本設定から以下を取得：
   - チャネルシークレット
   - チャネルアクセストークン（長期）
5. 取得した値を `.env` ファイルに設定

### 5) Cloud Run へのデプロイ

#### 自動デプロイ（推奨）

```bash
# スクリプトを実行可能にする
chmod +x scripts/init_gcp.sh

# デプロイスクリプトを実行
./scripts/init_gcp.sh
```

#### 手動デプロイ

```bash
# Cloud Run にデプロイ
gcloud run deploy splitbills \
    --source . \
    --region asia-northeast1 \
    --platform managed \
    --allow-unauthenticated \
    --service-account splitbills-sa@splitbills.iam.gserviceaccount.com \
    --set-env-vars "$(grep -v '^#' .env | xargs | tr ' ' ',')" \
    --memory 512Mi \
    --max-instances 10 \
    --timeout 60

# デプロイ後、表示されたURLを確認
# 例: https://splitbills-xxxxxxxxxx-an.a.run.app
```

### 6) LINE Webhook 設定（ユーザー作業）

1. LINE Developers Console でチャンネル設定を開く
2. Messaging API設定 > Webhook設定
3. Webhook URL に `https://your-cloud-run-url/callback` を設定
4. Webhook利用を「オン」に設定
5. 応答メッセージを「オフ」に設定
6. Botを友だち追加して動作確認

## ローカル開発

```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# ローカル実行
uvicorn app.main:app --reload --port 8000

# ngrok でトンネリング（別ターミナル）
ngrok http 8000
```

## GitHub リポジトリ作成

### 自動作成（gh CLI使用）

```bash
# スクリプトを実行可能にする
chmod +x scripts/init_github.sh

# リポジトリ作成スクリプトを実行
./scripts/init_github.sh
```

### 手動作成

```bash
# Git初期化
git init
git add .
git commit -m "Initial commit: splitbills LINE bot"

# GitHubでリポジトリ作成後
git remote add origin https://github.com/YOUR_USERNAME/splitbills.git
git push -u origin main
```

## 無料枠・安全策

- 本実装はメモリ内カウンタで月1000回のOCR利用を制限
- Cloud Run再起動でカウンタはリセットされます
- 本番環境では以下を推奨：
  - Firestore でカウンタを永続化
  - GCP Budget Alerts の設定
  - Cloud Monitoring でのアラート設定

## 代替ID手順（splitbills が使用済みの場合）

```bash
# ランダムな suffix を追加
ALT_ID=splitbills-$(openssl rand -hex 4)
echo "Using project ID: $ALT_ID"

# プロジェクト作成
gcloud projects create $ALT_ID
gcloud config set project $ALT_ID

# 以降のコマンドで splitbills を $ALT_ID に置換
# サービスアカウントのメールアドレスも変更
# splitbills-sa@$ALT_ID.iam.gserviceaccount.com
```

## トラブルシューティング

### 署名検証エラー

- LINE チャネルシークレットが正しく設定されているか確認
- `.env` ファイルが正しく読み込まれているか確認

### OCRが動作しない（403/401エラー）

```bash
# サービスアカウントの権限を確認
gcloud projects get-iam-policy splitbills

# Vision API が有効か確認
gcloud services list --enabled | grep vision

# Cloud Run のサービスアカウントを確認
gcloud run services describe splitbills --region asia-northeast1
```

### Vision API 429エラー（レート制限）

- `MONTHLY_OCR_CAP` の値を調整
- `FREE_MODE=false` に設定して制限を解除（課金注意）

### OCR精度が低い

レシート撮影のコツ：
- 明るい場所で撮影
- レシートを平らに置く
- カメラを真上から撮影
- 影やピンボケを避ける
- 高解像度で撮影

### Cloud Run デプロイエラー

```bash
# ビルドログを確認
gcloud builds list --limit 5

# Cloud Run のログを確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=splitbills" --limit 50
```

## アーキテクチャ

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│    LINE     │────▶│  Cloud Run  │────▶│ Vision API   │
│    User     │◀────│  (FastAPI)  │◀────│    (OCR)     │
└─────────────┘     └─────────────┘     └──────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Memory    │
                    │  (Session/  │
                    │   Usage)    │
                    └─────────────┘
```

## ライセンス

MIT License

## サポート

問題が発生した場合は、以下を確認してください：

1. Cloud Run のログ：
   ```bash
   gcloud run logs read --service splitbills --limit 50
   ```

2. GCP コンソール：
   https://console.cloud.google.com/run

3. LINE Developers Console：
   https://developers.line.biz/console/

## 今後の拡張案

- [ ] レシート保存機能（Cloud Storage）
- [ ] 履歴管理（Firestore）
- [ ] グループチャット対応
- [ ] 通貨自動判定
- [ ] チップ計算機能
- [ ] 税金分離機能