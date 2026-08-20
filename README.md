# Treasure AI 導入事例検索

GitHub Pagesで公開する、Treasure AIの導入事例検索サイトです。

## 自動更新

`.github/workflows/sync.yml` が6時間ごとに次を実行します。

1. `treasure.ai/sitemap.xml`から日本語の`/ja/customers/`ページを発見
2. 各ページの本文・見出し・成果数値を取得
3. `data/overrides.json`の手動分類・営業向けバッジをマージ
4. `data/cases.json`を更新
5. `index.html`を再生成してGitHub Pagesへ反映

公式ページが一時的に取得できない場合は、既存のデータを保持します。

## 手動補正

業界、製品、背景、成果、バッジなど、公式ページだけでは判断しにくい情報は`data/overrides.json`で管理します。自動取得データで上書きされません。

## GitHub Pages設定

- PagesのSourceは`Deploy from a branch`
- Branchは`main`
- Folderは`/ (root)`

Actionsを手動で試す場合は、GitHubの`Actions`タブから`Sync Treasure AI cases`を選び、`Run workflow`を押します。
