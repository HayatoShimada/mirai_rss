# Mirai RSS Bot

富山県南砺市井波でこれから創業を考えている、あるいは創業し始めたばかりの小規模な個人事業主（1〜2人での創業）向け（ミライ店主会Bot）に、空き家活用、DIY、田舎での集客、コミュニティづくり、地域ニュースなどの有益な情報を収集・厳選してDiscordに毎日定期配信するBotです。
RSSが提供されていないWebサイトの場合でも、直接URLを渡すことで、Google Gemini APIが自らインターネットを検索・内容を確認し、有益な情報を厳選・要約します。

## 主な機能
- **RSS & HTML自動解析**: RSSフィードからの高速な取得はもちろん、RSSがないサイトのHTMLページもGeminiモデルを用いて自律的に内容を読み取り、リンク先も探索します。
- **高精度な要約・フィルタリング**: 1日分のニュースから重複を排除し、「ニュース」「補助金・支援」「空き家・DIY」「集客・コミュニティ」のカテゴリ付きで、最大5件の重要な情報を要約して配信します。
- **代替ニュース機能**: 定義されたメイン情報源（南砺市周辺）から新しい情報が無かった場合は、自動的に代替ソース（全国のビジネス・空き家情報など）から情報をピックアップします。
- **配信履歴の記憶**: `posted_articles.json` に過去の投稿URLを記録してGitHub上に保存することで、昨日と同じニュースが重複して配信されることを防ぎます。
- **Discord Webhook連携**: スマートフォンからも見やすいEmbed（埋め込みメッセージ形式）でDiscordに自動投稿されます。
- **完全自動運用**: GitHub Actionsを利用するためサーバーは一切不要で、毎日定時に自動実行されます。

## 必要要件
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

| URL                               | Type | Selector      |
| --------------------------------- | ---- | ------------- |
| https://news.yahoo.co.jp/rss/...  | RSS  |               |
| https://www.city.nanto.toyama.jp/ | HTML | .info_list li |

- `Type` には `RSS` または `HTML` と記載します。
- `Selector` は `Type` が `HTML` の場合にのみ使用します。新着情報が含まれるHTML要素（liタグやarticleタグなど）をCSSセレクタ形式で指定してください。

## GitHub Actionsの運用と手動での実行方法
GitHub上で自動で毎日稼働させる手順は以下の通りです：

1. リポジトリの [Settings] タブを開きます。
2. 左メニューから [Secrets and variables] > [Actions] を選択します。
3. `New repository secret` ボタンから、以下の2つのシークレット値を登録してください。
   - `DISCORD_WEBHOOK_URL` (Discord WebhookのURL)
   - `GEMINI_API_KEY` (Gemini APIのキー)
4. あとは `.github/workflows/rss_bot.yml` の設定に従い、日本時間の毎日朝4:00に自動実行されます。

### 手動でBotを実行する方法 (Workflow Dispatch)
新しく追加した設定の動作確認や、今日すぐにニュースをまとめたい場合は、GitHubの画面から手動でBotを起動できます。

1. GitHubリポジトリの **[Actions]** タブを開きます。
2. 左側のワークフロー一覧から **[Mirai RSS Bot]** をクリックします。
3. 画面の右側にある **[Run workflow]** というドロップダウンボタンをクリックします。
4. 緑色の **[Run workflow]** ボタンを押すと、処理がスタートします。数分後にDiscordへ投稿されます。

## 🤝 開発への参加（Pull Request の歓迎）

このプロジェクトでは、より良質な情報を効率的に届けるために、皆様からの**Pull Request（プルリク）による改善提案を大募集**しています！
エンジニアではない方でも、文章の設定を変えるだけでBotをより賢くすることができます。

**特に歓迎するコントリビューション：**
- **🎯 `prompt.txt` の改善**: プロンプト（AIへの命令書）内のルールや言い回しを微調整することで、AIの要約品質や口調を良くする改善。
- **🌐 `sources.md` の追加・整理**: 新しい空き家バンク情報、地元メディア、有益な補助金サイトなどの情報源リストへの追加。
- **💻 プログラムの改善**: より優れたエラー検知、処理速度の向上、Discordの見た目のカスタマイズなど。

**PRを送る手順：**
1. リポジトリ右上にある **[Fork]** を押して自身のアカウントにコピーを作成します。
2. 修正したいファイル（例：`prompt.txt` や `sources.md`）を編集し、Commitします。
3. リポジトリの [Pull requests] タブから **[New pull request]** を作成し、提案の内容（なぜその変更が必要か）を記載して送信してください。
