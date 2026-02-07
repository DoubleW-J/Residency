import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def setup_driver():
    """
    Selenium WebDriverの設定と初期化
    """
    chrome_options = Options()
    # 自動実行（GitHub Actionsなど）の場合は以下のコメントを外してヘッドレスモードにする
    # chrome_options.add_argument("--headless")
    
    # 自動操作防止機能の回避設定
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # ブラウザの起動
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def scrape_red_search(keyword, pages=3):
    """
    小紅書の検索結果からデータを取得する
    """
    driver = setup_driver()
    search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
    driver.get(search_url)
    
    # 初回読み込み待ち（手動でログインが必要な場合はここで時間を稼ぐ）
    print("ページ読み込み中... ログインが必要な場合は操作してください。")
    time.sleep(10) 

    data_list = []
    
    for page in range(pages):
        print(f"{page + 1}ページ目を処理中...")
        
        
        items = driver.find_elements(By.CSS_SELECTOR, ".note-item")
        for item in items:
            try:
                
                title = item.find_element(By.CSS_SELECTOR, ".title").text
                
                
                data_list.append({
                    "raw_text": title,
                    "source": "RED",
                    "collected_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as e:
                
                continue
        
        # ページ下部へスクロールして次のコンテンツを読み込む
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3) # 読み込み待ち

    driver.quit()
    return pd.DataFrame(data_list)

if __name__ == "__main__":
    # 検索キーワード設定
    search_term = "日本永住 申請"
    
    result_df = scrape_red_search(search_term, pages=2)

    output_file = "red_raw_data.csv"
    result_df.to_csv(output_file, index=False, encoding="utf-8-sig")
    
    print(f"処理完了: {len(result_df)}件のデータを {output_file} に保存しました。")