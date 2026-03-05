# Mirai RSS Bot

富山県南砺市で新しく小規模事業を始める人々（ミライ店主会）向けに、地域ニュースや補助金情報、イベント情報を収集・要約してDiscordに毎日定期配信するBotです。
RSSが提供されていないWebサイトからでも、情報取得（HTMLスクレイピング）を行い、Google Gemini APIを活用して有益な情報を厳選・要約します。

## 機能
- **RSS & HTMLスクレイピング対応**: RSSフィードはもちろん、フィードがないサイトからもCSSセレクタを用いて新着情報を取得できます。
- **Gemini APIによる自動生成**: 1日分のニュースから重複を排除し、「ニュース」「補助金・法律」「イベント」のカテゴリ付きで、最大3件の重要な情報を要約して配信します。
- **代替ニュース機能**: 定義されたメイン情報源（南砺市周辺）から新しい情報が無かった場合は、自動的に代替ソース（全国のビジネス・補助金情報など）から情報をピックアップします。
- **Discord Webhook連携**: 見やすいEmbed（埋め込みメッセージ形式）でDiscordに自動投稿されます。
- **GitHub Actionsによる完全自動運用**: サーバー不要で、毎日定時にスクリプトが自動実行されます。

## 必要条件
- Python 3.10 以上
- 対象のDiscordサーバーで発行した **Webhook URL**
- Google AI Studioで取得した **Gemini API Key** (Gemini 2.5 Flash などに対応)

## ローカルでの実行・テスト方法

1. リポジトリをクローンまたはダウンロードし、ディレクトリへ移動します。
2. 依存パッケージをインストールします。
   ```bash
   pip install -r requirements.txt
   ```
3. プロジェクトのルートに `.env` ファイルを作成し、以下のようにキーを設定します（※`.env`はGitで管理しないよう注意してください）。
   ```env
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxx/yyyy
   GEMINI_API_KEY=AIzaSy_YOUR_API_KEY_HERE
   ```
4. 手動でツールを実行してテストします。Discordへの投稿をスキップしてコンソールに出力だけ行いたい場合は、`--dry-run` オプションを指定します。
   ```bash
   PYTHONPATH=. python src/main.py --dry-run
   ```

## 情報源リスト (`sources.md`) の編集について

Botの取得対象サイト（RSSまたはHTML）は、コードを変更することなく `sources.md` ファイルを編集することで管理可能です。

- `## メイン用`、`## 代替用` の見出しに分けて記載してください。
- データの記載方法は以下の **Markdownテーブル形式** である必要があります。

| URL | Type | Selector |
|---|---|---|
| https://news.yahoo.co.jp/rss/... | RSS | |
| https://www.city.nanto.toyama.jp/ | HTML | .info_list li |

- `Type` には `RSS` または `HTML` と記載します。
- `Selector` は `Type` が `HTML` の場合にのみ使用します。新着情報が含まれるHTML要素（liタグやarticleタグなど）をCSSセレクタ形式で指定してください。

## GitHub Actionsでの運用設定
GitHub上で自動で毎日稼働させる手順は以下の通りです：

1. リポジトリの [Settings] タブを開きます。
2. 左メニューから [Secrets and variables] > [Actions] を選択します。
3. `New repository secret` ボタンから、以下の2つのシークレット値を登録してください。
   - `DISCORD_WEBHOOK_URL` (Discord WebhookのURL)
   - `GEMINI_API_KEY` (Gemini APIのキー)
4. あとは `.github/workflows/rss_bot.yml` の設定に従い、日本時間の毎日朝4:00に自動実行されます（Actionsタブから手動でのトリガー起動も可能です）。
