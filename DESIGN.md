## DiscordサーバーにWebHookでRSSを投稿する

富山県南砺市関連のRSSをDiscordサーバーに投稿する
ミライ店主会（南砺市井波で新しく小規模事業を始める人々）のDiscordサーバー向けに最適化していきたい。

### 1. 必要なもの
- DiscordサーバーのWebHook URL
- RSSのURL

### 2. 実装
- RSSを定期的に取得する
- 新しい記事があればWebHookで投稿する

### 3. 技術選定
- Python
- requests
- feedparser
- Gemini API

### 4. 実行方法
- GitHub Actions
- 1日1回朝4:00に実行

### 5. RSS URL一覧

RSSは都度募集中
Gemini APIで取得した内容を要約する
小規模事業者向けの補助金情報や、近隣のイベント情報をスクレイピングしてもよいかも

- 補助金情報
- 法律情報
- 物件情報
- 富山県地域のイベント情報
- 富山県南砺市地域のニュース


## 候補RSS
- https://webun.jp/subcategory/%E5%8D%97%E7%A0%BA%E5%B8%82