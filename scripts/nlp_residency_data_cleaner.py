import os
import json
import pandas as pd
from dotenv import load_dotenv
from google.genai import types
from google.genai import Client

# --- 設定エリア ---
# .envから環境変数を読み込み
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
INPUT_FILE = 'data/raw/xhs_summary.txt'
OUTPUT_FILE = 'data/processed/xhs_cohort_progress.csv'

# Geminiクライアント初期化
client = Client(api_key=GEMINI_API_KEY)

def run_cohort_analysis():
    """Gemini APIを使用してテキストデータからコホートデータを抽出・構造化する"""
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ エラー: 入力ファイルが見つかりません ({INPUT_FILE})")
        return

    # 1. テキストの読み込み
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    print("🤖 Gemini AI がデータを構造化しています...")

    # 2. プロンプト定義
    prompt = f"""
    Act as a Senior Data Engineer. Extract monthly cohort data from the provided report.

    [EXTRACTION LOGIC]
    1. "Month": Convert "24年X月" format to "2024-X" (e.g., 2024-01).
    2. "Total_Applied": Find the number in "⭐各月提交人数" section for that month.
    3. "Approved_Main": The number BEFORE '+' in the "下签" line.
    4. "Approved_Family": The number AFTER '+' in the "下签" line.
    5. "RFE_Count": The number of "补材料" (Request for Evidence).
    6. "Notes": Briefly summarize month-specific trends in Japanese.

    [OUTPUT RULES]
    - Return ONLY a raw JSON array.
    - No markdown formatting, no conversational text.

    [TARGET TEXT]
    {raw_text}
    """

    try:
        # 3. Gemini API リクエスト
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type='application/json'
            )
        )

        # 4. JSONパースとDataFrame化
        structured_data = json.loads(response.text)
        df = pd.DataFrame(structured_data)

        # 5. データ型変換と計算列の追加
        cols_to_fix = ['Total_Applied', 'Approved_Main', 'Approved_Family', 'RFE_Count']
        for col in cols_to_fix:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df['Total_Approved'] = df['Approved_Main'] + df['Approved_Family']
        df['Movement_Total'] = df['Total_Approved'] + df['RFE_Count']
        df['Activity_Rate'] = (df['Movement_Total'] / df['Total_Applied']).round(4)
        df['Last_Updated'] = pd.Timestamp.now().strftime('%Y-%m-%d')

        # 6. CSV保存
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

        print(f"✅ 解析完了: {OUTPUT_FILE}")
        print(df[['Month', 'Total_Applied', 'Total_Approved', 'Activity_Rate']].head())

    except Exception as e:
        print(f"❌ 解析中にエラーが発生しました: {e}")

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("❌ エラー: GEMINI_API_KEY が設定されていません。")
    else:
        run_cohort_analysis()