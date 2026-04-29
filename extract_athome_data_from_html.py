import os
import csv
import shutil
import glob
from datetime import datetime
from bs4 import BeautifulSoup

# 1. 処理したいファイルが入っているフォルダを指定.
# （ここでは現在のフォルダを対象にしています）
target_dir = './bukken_pool'
backup_dir = './backup_bukken_list'
base_output_file = 'bukken_list'

def extract_property_info(file_path):
    """ファイルから物件情報を抽出する関数"""
    properties = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 物件のブロックを特定（実際のHTML構造に合わせて調整）
    # アットホームの物件は <div class="card-box open"> 内にあります
    items = soup.find_all('div', class_='card-box open')
    
    for item in items:
        # 物件名の抽出
        name_tag = item.find('div', class_='title-wrap__title-text')
        name = name_tag.get_text(strip=True) if name_tag else 'N/A'
        
        # 価格の抽出
        price_tag = item.find('div', class_='property-price')
        if price_tag:
            price_text = price_tag.get_text(strip=True)
            # 数字部分のみ抽出（例: "148万円" → "148万円"）
            price = price_text
        else:
            price = 'N/A'
        
        # 所在地の抽出
        address_tag = item.find('span', string=lambda text: text and '所在地' in text)
        if address_tag:
            address = address_tag.find_next('span').get_text(strip=True) if address_tag.find_next('span') else 'N/A'
        else:
            # 別の方法で所在地を探す
            address_span = item.find('span', text=lambda t: t and ('北九州市' in t or '福岡市' in t))
            address = address_span.get_text(strip=True) if address_span else 'N/A'
        
        properties.append({
            '物件名': name,
            '価格': price,
            '所在地': address,
            'ファイル名': os.path.basename(file_path)
        })
    
    # ファイルごとの区切り行を先頭に追加
    separator_row = {
        '物件名': f'--- {os.path.basename(file_path)} ---',
        '価格': '',
        '所在地': '',
        'ファイル名': ''
    }
    properties.insert(0, separator_row)
    return properties

def main():
    all_properties = []
    
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