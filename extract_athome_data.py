import os
import csv
import glob
from bs4 import BeautifulSoup

def extract_bukken_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    bukken_list = []

    # 各物件のカードコンポーネントをすべて取得
    cards = soup.find_all('athome-csite-pc-part-bukken-card-ryutsu-sell-living')

    for card in cards:
        data = {}
        
        # 1. タイトル・物件名
        title_tag = card.find('div', class_='title-wrap__title-text')
        data['物件名'] = title_tag.get_text(strip=True) if title_tag else ""

        # 2. 価格
        price_tag = card.find('div', class_='property-price')
        data['価格'] = price_tag.get_text(strip=True) if price_tag else ""

        # 3. 詳細テーブルの解析（交通、所在地、間取り、築年月、土地面積、建物面積など）
        # 各ブロックをループして、項目名(strong)と値(span)をペアにする
        detail_blocks = card.find_all('div', class_='property-detail-table__block')
        for block in detail_blocks:
            label_tag = block.find('strong')
            value_tag = block.find('span')
            
            if label_tag and value_tag:
                label = label_tag.get_text(strip=True)
                value = value_tag.get_text(strip=True)
                data[label] = value

        if data:
            bukken_list.append(data)
            
    return bukken_list

def main():
    # 設定
    input_folder = './html_files'  # 解析対象のフォルダパス
    output_csv = 'bukken_export.csv'
    
    all_data = []
    
    # フォルダ内の全htmlファイルを取得 (100ファイル程度想定)
    html_files = glob.glob(os.path.join(input_folder, "*.html"))
    
    print(f"解析開始: {len(html_files)} ファイルが見つかりました。")

    for file_path in html_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                results = extract_bukken_data(content)
                all_data.extend(results)
                print(f"完了: {os.path.basename(file_path)} ({len(results)}件)")
        except Exception as e:
            print(f"エラー発生 ({os.path.basename(file_path)}): {e}")

    # CSV出力
    if all_data:
        # 最初のデータのキーをヘッダーにする
        keys = all_data[0].keys()
        with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_data)
        print(f"\n成功: {output_csv} に {len(all_data)} 件の物件データを出力しました。")
    else:
        print("\nデータが見つかりませんでした。")

if __name__ == "__main__":
    main()