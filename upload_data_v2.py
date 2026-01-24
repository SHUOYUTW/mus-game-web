import pandas as pd
import psycopg2
import re
import glob
import sys

DB_HOST = "db.fsdrnmwvsngbaasiriou.supabase.co" 
DB_USER = "postgres"
DB_PASS = "Eason931229@@"
DB_NAME = "postgres"
DB_PORT = "5432"

def parse_quote(text):
    items = []
    if not isinstance(text, str): return items
    
    lines = text.split('\n')
    for line in lines:
        if '=' not in line: continue
        parts = line.split('=')
        if len(parts) >= 2:
            item_name = parts[0].strip()
            item_name = re.sub(r'^[💥▪️✻]\s*', '', item_name)
            
            price_str = parts[1].strip()
            # 抓取數字 (支援 1,000 或 $100)
            price_match = re.search(r'(\d{1,3}(,\d{3})*|\d+)', price_str)
            if price_match:
                price = int(price_match.group(0).replace(',', ''))
                items.append((item_name, price))
    return items

def upload_to_supabase():
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
        cur = conn.cursor()
        print("✅ 資料庫連線成功！")

        cur.execute("TRUNCATE TABLE GamePrices;")
        
        # 搜尋所有 xlsx 檔案
        excel_files = glob.glob('*.xlsx')
        if not excel_files:
            print("⚠️ 找不到任何 .xlsx 檔案！請確認檔案是否在同一個資料夾。")
            return

        total_count = 0

        for file in excel_files:
            category = 'PC' if '端遊' in file else 'Mobile'
            print(f"\n📂 正在讀取: {file} ({category})")
            
            try:
                df = pd.read_excel(file, engine='openpyxl')
                print(f"   -> 偵測到欄位: {df.columns.tolist()}")
            except Exception as e:
                print(f"   ❌ 無法讀取檔案: {e}")
                continue

            # --- 聰明對應欄位 (改進版) ---
            # 直接拿第 1 欄當遊戲名稱，第 2 欄當報價單 (不管標題叫什麼)
            if len(df.columns) < 2:
                print("   ❌ 跳過：欄位不足 (至少需要 2 欄)")
                continue
                
            col_game = df.columns[0] # 第 1 欄
            col_quote = df.columns[1] # 第 2 欄
            print(f"   -> 使用 '{col_game}' 當遊戲名稱, '{col_quote}' 當報價單")

            file_count = 0
            for _, row in df.iterrows():
                game = row[col_game]
                quote = row[col_quote]
                
                # 檢查資料是否為空
                if pd.isna(game) or pd.isna(quote): continue
                
                # 清理遊戲名稱
                if isinstance(game, str):
                    game = game.replace('【', '').replace('】', '').replace('《', '').replace('》', '').strip()

                items = parse_quote(str(quote))
                
                if not items:
                    # 如果解析失敗，印出來看看是不是格式怪怪的
                    # print(f"   (DEBUG) 解析失敗: {str(quote)[:30]}...") 
                    pass

                for item_name, price in items:
                    cur.execute(
                        "INSERT INTO GamePrices (category, game_name, item_name, price) VALUES (%s, %s, %s, %s)",
                        (category, game, item_name, price)
                    )
                    file_count += 1
                    total_count += 1
            
            print(f"   -> 成功從此檔案匯入 {file_count} 筆")

        conn.commit()
        print(f"\n🎉 全部完成！資料庫現在共有 {total_count} 筆資料。")
        cur.close()
        conn.close()

    except Exception as e:
        print(f"💀 發生錯誤: {e}")

if __name__ == "__main__":
    upload_to_supabase()