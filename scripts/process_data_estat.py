import pandas as pd
import numpy as np
import csv
import os

# --- 設定エリア ---
INPUT_PATH = 'data/raw/estat_raw.csv'
OUTPUT_PATH = 'data/processed/estat_transformed.csv'

def clean_num(val):
    """数値データのクレンジング（カンマ除去、異常値の0埋め）"""
    if not val: return 0
    s = str(val).replace(',', '').strip()
    if s in ['', '-', '***']: return 0
    try: 
        return int(float(s))
    except: 
        return 0

def get_bureau_prefix(name):
    """地域名から「出入国管理局」名のみを抽出"""
    for target in ["出入国在留管理局", "出入国管理局"]:
        if target in name:
            return name.split(target)[0]
    return ""

def transform_estat_data(input_file, output_file):
    """e-StatのCSVをTableau/分析用の縦持ち形式に変換"""
    
    # 1. データ読み込み
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        all_rows = [row for row in reader]

    # ヘッダー情報の定義（e-Stat特有の行位置を指定）
    raw_names = all_rows[10][13:]
    attr_headers = [h.strip() if h.strip() != "" else f"col_{i}" for i, h in enumerate(all_rows[10][:12])]
    
    # 2. データフレーム構築
    df_raw = pd.DataFrame(all_rows[11:])
    attr_part = df_raw.iloc[:, :12]
    value_part = df_raw.iloc[:, 13:13+len(raw_names)]
    
    df_combined = pd.concat([attr_part, value_part], axis=1)
    df_combined.columns = attr_headers + raw_names

    # 3. Transform (縦持ち変換: Melt)
    df_long = df_combined.melt(
        id_vars=attr_headers,
        value_vars=raw_names,
        var_name='地域名',
        value_name='件数'
    )

    # 4. 前処理とカラム整理
    df_long['件数'] = df_long['件数'].apply(clean_num)
    df_long['出入国管理局'] = df_long['地域名'].apply(get_bureau_prefix)

    # 5. リネームと列選択
    df_long = df_long.rename(columns={
        attr_headers[8]: '在留資格審査',
        attr_headers[5]: '时间轴（月次）',
        attr_headers[11]: '在留資格審査の受理・処理'
    })

    final_cols = [
        '在留資格審査', '地域名', '出入国管理局', 
        '时间轴（月次）', '在留資格審査の受理・処理', '件数'
    ]
    
    # 6. 結果の保存
    df_final = df_long[final_cols]
    df_final.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ 変換完了: {output_file}")

if __name__ == "__main__":
    # 出力先ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    if os.path.exists(INPUT_PATH):
        transform_estat_data(INPUT_PATH, OUTPUT_PATH)
    else:
        print(f"❌ エラー: 入力ファイルが見つかりません ({INPUT_PATH})")