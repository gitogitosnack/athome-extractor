# bukken_info_extractor

Athome の保存した HTML/TXT ファイルから、物件名・価格・所在地を抽出して CSV に出力する Python スクリプトです。

## 概要

`extract_athome_data_from_html.py` は、`./bukken_pool` 配下の `.html` / `.txt` ファイルを読み込み、以下の情報を抽出します。

- 物件名
- 価格
- 所在地
- ファイル名

抽出結果は、実行時のタイムスタンプ付き CSV ファイルとしてルートディレクトリに出力されます。

## 依存環境

- Python 3.8 以上
- Python 標準ライブラリ
  - `os`
  - `csv`
  - `shutil`
  - `glob`
  - `datetime`
- 外部ライブラリ
  - `beautifulsoup4`

### インストール例

```bash
python -m pip install beautifulsoup4
```

## 使い方
#### 注意：抽出元となるファイルは、AtHomeサイトがスクレイピングを禁止しているため、手動でそのデータを入手する必要があるため、以下の面倒な手作業が発生している。

1. ブラウザで Athome の物件一覧ページを開きます。
2. `F12` キー（または右クリック > 検証）でデベロッパーツールを開きます。
3. `Elements` タブを選択し、HTML ドキュメントの先頭にある `<html>` タグを右クリックします。
4. **Copy > Copy element** を選択して、HTML 全体をコピーします。
5. テキストエディタを開き、コピーした HTML を貼り付けて保存します。
6. 保存ファイルを `bukken_pool` フォルダに移動します。
   - 例: `bukken_pool/chiba.html`
   - 例: `bukken_pool/tochigi.txt`

7. リポジトリのルートディレクトリに移動します。

8. スクリプトを実行します。

```bash
python extract_athome_data_from_html.py
```

## 出力とバックアップ

- 出力ファイル: `bukken_list_YYYYMMDD_HHMMSS.csv`
- バックアップフォルダ: `backup_bukken_list/`

既存の `bukken_list_*.csv` は、実行前に `backup_bukken_list` にコピーされます。
また、ルートディレクトリには最新の CSV 1 ファイルだけが残り、古い `bukken_list_*.csv` は削除されます。

## ディレクトリ構成

```text
.
├── backup_bukken_list/             # 過去のCSVバックアップ保存先
├── bukken_list_YYYYMMDD_HHMMSS.csv # 最新の出力ファイル
├── bukken_pool/                    # 解析対象のHTML/TXTを配置
├── extract_athome_data_from_html.py # 抽出スクリプト本体
├── README.md
└── venv/                           # Python仮想環境（存在する場合）
```

## 注意事項

- HTML の構造が変わると抽出処理も修正が必要です。
- 現在は `div.card-box.open` 内の項目を対象にしています。
- `価格` と `所在地` の検出は現状のタグ構造に依存しています。

## 変更したい場合

- `target_dir` を変更したい場合は、`extract_athome_data_from_html.py` 内の `target_dir` を編集してください。
- 出力ファイル名のフォーマットを変えたい場合は、同ファイルの `output_file` 生成部分を修正してください。
