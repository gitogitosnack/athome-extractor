import os
import csv
import shutil
import glob
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup

# 1. 処理したいファイルが入っているフォルダを指定.
# （ここでは現在のフォルダを対象にしています）
target_dir = './bukken_pool'  # HTMLファイルが格納されるディレクトリ
backup_dir = './backup_bukken_list'  # バックアップファイルを保存するディレクトリ
base_output_file = 'bukken_list'  # 出力CSVファイルのベース名（タイムスタンプが追加される）

def extract_detail_value(item, label):
    """property-detail-table__block内からラベル付きの値を抽出"""
    # すべての詳細情報ブロック（property-detail-table__block）を検索
    detail_blocks = item.find_all('div', class_='property-detail-table__block')
    # 各ブロックをループして指定のラベルを含むものを探す
    for block in detail_blocks:
        # ラベルテキストを格納する<strong>タグを検索
        strong_tag = block.find('strong')
        # strong_tagが存在し、且つラベル文字列を含むか判定
        if strong_tag and label in strong_tag.get_text(strip=True):
            # 値を格納する<span>タグを同じブロック内で検索
            span_tag = block.find('span')
            # span_tagが存在すれば値を抽出して返す
            if span_tag:
                return span_tag.get_text(strip=True)
    # ラベルが見つからない場合は'N/A'を返す
    return 'N/A'

def extract_numeric_value(text):
    """テキストから数値を抽出"""
    # 入力が'N/A'の場合はそのまま返す（計算スキップ）
    if text == 'N/A':
        return 'N/A'
    # 正規表現で最初の数値（整数または小数）を検索
    # r'(\d+(?:\.\d+)?)' : 1文字以上の数字、オプションで小数点と小数部分
    match = re.search(r'(\d+(?:\.\d+)?)', text)
    # マッチした場合はgroup(1)で第1グループ（数値）を返す、なければ'N/A'
    return match.group(1) if match else 'N/A'

def extract_price_value(price_str):
    """価格文字列から万円単位の数値を抽出"""
    # 入力が'N/A'の場合はそのまま返す
    if price_str == 'N/A':
        return 'N/A'
    # 例："398万円"から"398"を抽出する正規表現
    # r'(\d+(?:\.\d+)?)' で最初の数値を検索
    match = re.search(r'(\d+(?:\.\d+)?)', price_str)
    # マッチした場合は数値部分を返す、なければ'N/A'
    return match.group(1) if match else 'N/A'

def extract_floor_plan_rooms(floor_plan_str):
    """間取りから部屋数を抽出（例：８ＤＫ → 8）"""
    # 入力が'N/A'の場合はそのまま返す
    if floor_plan_str == 'N/A':
        return 'N/A'
    # 全角数字（０-９）を半角数字（0-9）に変換
    # str.maketrans()で文字変換テーブルを作成し、translate()で置換
    floor_plan_str = floor_plan_str.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    # 変換後のテキストから最初の数字を正規表現で抽出
    # r'(\d+)' : 1文字以上の連続した数字
    match = re.search(r'(\d+)', floor_plan_str)
    # マッチした場合は数字を返す、なければ'N/A'
    return match.group(1) if match else 'N/A'

def format_build_date(date_str):
    """築年月日をISO形式（YYYY-MM-DD）に変換"""
    # 入力が'N/A'の場合はそのまま返す
    if date_str == 'N/A':
        return 'N/A'
    # 正規表現で年と月を抽出
    # r'(\d{4})年(\d{1,2})月' : "1964年1月" のようなフォーマットに対応
    # (\d{4}): 4桁の数字（年）
    # (\d{1,2}): 1-2桁の数字（月）
    match = re.search(r'(\d{4})年(\d{1,2})月', date_str)
    # マッチした場合は日付形式に変換
    if match:
        # マッチした第1グループ（年）を取得
        year = match.group(1)
        # マッチした第2グループ（月）を取得し、ゼロパディング（例：1 → 01）
        month = match.group(2).zfill(2)
        # ISO形式（YYYY-MM-01）で日付を返す（日は固定で1日）
        return f'{year}-{month}-01'
    # マッチしなかった場合は'N/A'を返す
    return 'N/A'

def extract_years_value(years_months_str):
    """築年数から年数を抽出（例：築62年4ヶ月 → 62）"""
    # 入力が'N/A'の場合はそのまま返す
    if years_months_str == 'N/A':
        return 'N/A'
    # 正規表現で"築"と"年"に囲まれた数字を抽出
    # r'築(\d+)年' : "築62年" のような文字列から"62"を抽出
    # (\d+): 1文字以上の連続した数字（キャプチャグループ）
    match = re.search(r'築(\d+)年', years_months_str)
    # マッチした場合はgroup(1)で年数を返す、なければ'N/A'
    return match.group(1) if match else 'N/A'

def calculate_years_months(date_str):
    """築年月日から築年数を計算"""
    try:
        # "1964年1月"形式のテキストをパース
        match = re.search(r'(\d{4})年(\d{1,2})月', date_str)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            build_date = datetime(year, month, 1)
            today = datetime.now()
            delta = relativedelta(today, build_date)
            return f'築{delta.years}年{delta.months}ヶ月'
    except Exception:
        pass
    return 'N/A'

def extract_property_info(file_path):
    """ファイルから物件情報を抽出する関数"""
    properties = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 物件のブロックを特定
    items = soup.find_all('div', class_='card-box open')
    
    for item in items:
        # 物件ID の抽出
        property_id = 'N/A'
        checkbox = item.find('input', type='checkbox')
        if checkbox and checkbox.get('id'):
            property_id = checkbox.get('id')
        
        # 物件名の抽出
        name_tag = item.find('div', class_='title-wrap__title-text')
        name = name_tag.get_text(strip=True) if name_tag else 'N/A'
        
        # 物件種別の抽出
        property_type = 'N/A'
        square_icon = item.find('li', class_='square-icon')
        if square_icon:
            property_type = square_icon.get_text(strip=True)
        
        # 価格の抽出と数値化
        price_tag = item.find('div', class_='property-price')
        price = price_tag.get_text(strip=True) if price_tag else 'N/A'
        price_numeric = extract_price_value(price)
        
        # 間取り の抽出と数値化
        floor_plan = extract_detail_value(item, '間取り')
        floor_plan_numeric = extract_floor_plan_rooms(floor_plan)
        
        # 建物面積 の抽出と数値化
        building_area = extract_detail_value(item, '建物面積')
        building_area_numeric = extract_numeric_value(building_area)
        
        # 土地面積 の抽出と数値化
        land_area = extract_detail_value(item, '土地面積')
        land_area_numeric = extract_numeric_value(land_area)
        
        # 築年月日 の抽出と日付化
        build_date = extract_detail_value(item, '築年月')
        build_date_formatted = format_build_date(build_date)
        
        # 築年数 の計算と数値化
        years_months = calculate_years_months(build_date)
        years_numeric = extract_years_value(years_months)
        
        # 駅情報・駅徒歩 の抽出
        transit = extract_detail_value(item, '交通')
        
        # 所在地の抽出
        address_tag = item.find('span', string=lambda text: text and '所在地' in text)
        if address_tag:
            address = address_tag.find_next('span').get_text(strip=True) if address_tag.find_next('span') else 'N/A'
        else:
            # 別の方法で所在地を探す
            address_span = item.find('span', text=lambda t: t and ('北九州市' in t or '福岡市' in t or '県' in t))
            address = address_span.get_text(strip=True) if address_span else 'N/A'
        
        # 不動産会社 の抽出
        company = 'N/A'
        estate_block = item.find('div', class_='card-box-inner__estate')
        if estate_block:
            company = estate_block.get_text(strip=True)
        
        # お気に入り登録数 の抽出
        favorites = 'N/A'
        round_icon = item.find('li', class_='round-icon')
        if round_icon:
            # round-iconの次のテキストノードを探す
            next_text = round_icon.find_next()
            if next_text:
                favorites_text = next_text.get_text(strip=True)
                match = re.search(r'(\d+)人', favorites_text)
                if match:
                    favorites = match.group(1) + '人'
        
        properties.append({
            '物件ID': property_id,
            '物件名': name,
            '物件種別': property_type,
            '価格': price,
            '価格（万円）': price_numeric,
            '間取り': floor_plan,
            '間取り（部屋数）': floor_plan_numeric,
            '建物面積': building_area,
            '建物面積（㎡）': building_area_numeric,
            '土地面積': land_area,
            '土地面積（㎡）': land_area_numeric,
            '築年月日': build_date,
            '築年月日（日付）': build_date_formatted,
            '築年数': years_months,
            '築年数（年）': years_numeric,
            '駅情報・駅徒歩': transit,
            '所在地': address,
            '不動産会社': company,
            'お気に入り登録数': favorites,
            'ファイル名': os.path.basename(file_path)
        })
    
    # ファイルごとの区切り行を先頭に追加
    separator_row = {
        '物件ID': '',
        '物件名': f'--- {os.path.basename(file_path)} ---',
        '物件種別': '',
        '価格': '',
        '価格（万円）': '',
        '間取り': '',
        '間取り（部屋数）': '',
        '建物面積': '',
        '建物面積（㎡）': '',
        '土地面積': '',
        '土地面積（㎡）': '',
        '築年月日': '',
        '築年月日（日付）': '',
        '築年数': '',
        '築年数（年）': '',
        '駅情報・駅徒歩': '',
        '所在地': '',
        '不動産会社': '',
        'お気に入り登録数': '',
        'ファイル名': ''
    }
    properties.insert(0, separator_row)
    return properties

def main():
    """メイン処理関数
    
    処理フロー:
    1. バックアップディレクトリの作成
    2. 既存の日付付きCSVファイルをバックアップフォルダへコピー
    3. target_dir 内のHTMLファイルを全て処理
    4. 抽出結果をCSVファイルに出力
    5. 古い日付付きCSVを削除（最新ファイルのみ保持）
    """
    all_properties = []  # すべての物件情報を格納するリスト
    
    # バックアップディレクトリを作成
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 既存のbukken_list_日付.csvをバックアップ
    old_csv_files = glob.glob(f'{base_output_file}_*.csv')
    for old_file in old_csv_files:
        backup_file = os.path.join(backup_dir, os.path.basename(old_file))
        if not os.path.exists(backup_file):
            shutil.copy2(old_file, backup_file)
            print(f"バックアップ作成: {backup_file}")

    # 3. フォルダ内のファイルをループ処理
    for filename in os.listdir(target_dir):
        if filename.endswith('.html') or filename.endswith('.txt'):
            file_path = os.path.join(target_dir, filename)
            print(f"処理中: {filename}")
            
            try:
                data = extract_property_info(file_path)
                all_properties.extend(data)
            except Exception as e:
                print(f"エラー（{filename}): {e}")

    # 4. 結果をCSVに保存（日付付きファイル名）
    if all_properties:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'{base_output_file}_{timestamp}.csv'
        keys = all_properties[0].keys()
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_properties)
        print(f"\n完了! {len(all_properties)} 件の物件情報を {output_file} に保存しました。")
        
        # 古いCSVファイルを削除（最新ファイル以外）
        old_csv_files = glob.glob(f'{base_output_file}_*.csv')
        if len(old_csv_files) > 1:
            old_csv_files.sort()  # ファイル名でソート（日付順）
            for old_file in old_csv_files[:-1]:  # 最新ファイル以外を削除
                try:
                    os.remove(old_file)
                    print(f"削除: {old_file}")
                except Exception as e:
                    print(f"削除失敗（{old_file}): {e}")
    else:
        print("\n物件情報が見つかりませんでした。タグの設定を確認してください。")

if __name__ == "__main__":
    main()