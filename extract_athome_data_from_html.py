import os
import csv
from bs4 import BeautifulSoup

# 1. 処理したいファイルが入っているフォルダを指定.
# （ここでは現在のフォルダを対象にしています）
target_dir = './bukken_pool'
output_file = 'bukken_list.csv'

def extract_property_info(file_path):
    """ファイルから物件情報を抽出する関数"""
    properties = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 2. 物件情報のブロックを特定（サイトの構造に合わせて調整が必要）
    # アットホームの例：物件ごとに <div class="item"> などのブロックがある場合
    items = soup.find_all('div', class_='item') # ←ここは実際のHTML構造に合わせます
    
    for item in items:
        # 物件名の抽出
        name_tag = item.find('h2') # 物件名がh2タグにあると想定
        name = name_tag.get_text(strip=True) if name_tag else 'N/A'
        
        # 価格の抽出
        price_tag = item.find('p', class_='price') # 価格が特定のクラスにあると想定
        price = price_tag.get_text(strip=True) if price_tag else 'N/A'
        
        # 所在地の抽出
        address_tag = item.find('p', class_='address')
        address = address_tag.get_text(strip=True) if address_tag else 'N/A'
        
        properties.append({
            '物件名': name,
            '価格': price,
            '所在地': address,
            'ファイル名': os.path.basename(file_path)
        })
    
    return properties

def main():
    all_properties = []

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

    # 4. 結果をCSVに保存
    if all_properties:
        keys = all_properties[0].keys()
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_properties)
        print(f"\n完了! {len(all_properties)} 件の物件情報を {output_file} に保存しました。")
    else:
        print("\n物件情報が見つかりませんでした。タグの設定を確認してください。")

if __name__ == "__main__":
    main()