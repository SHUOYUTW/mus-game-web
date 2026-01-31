import streamlit as st
import psycopg2
import pandas as pd
import io, re

st.set_page_config(page_title="姆斯後台-終極版", layout="wide")

def get_conn():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"], database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"], password=st.secrets["DB_PASS"],
        port=st.secrets["DB_PORT"], sslmode="require"
    )

def upload_to_db(df):
    try:
        conn = get_conn()
        cur = conn.cursor()
        df.columns = [c.lower().strip() for c in df.columns]
        for _, row in df.iterrows():
            cur.execute(
                "INSERT INTO GameData (category, game_name, item_name, price, image_url) VALUES (%s, %s, %s, %s, %s)",
                (row['category'], row['game_name'], row['item_name'], row['price'], row['image_url'])
            )
        conn.commit()
        conn.close()
        st.success(f"✅ 成功匯入 {len(df)} 筆資料！")
    except Exception as e:
        st.error(f"❌ 寫入失敗: {e}")

st.title("🛠️ 姆斯商城 - 終極後台管理")
tab1, tab2, tab3 = st.tabs(["📁 批量匯入", "🚀 智慧文字解析", "📊 資料管理"])

# --- Tab 1: Excel/CSV 上傳 ---
with tab1:
    uploaded_file = st.file_uploader("選擇價目表檔案", type=["xlsx", "csv"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                content = uploaded_file.read()
                # 解決 0x94 編碼報錯：遍歷嘗試編碼
                for enc in ['utf-8-sig', 'cp950', 'big5', 'latin1']:
                    try:
                        df = pd.read_csv(io.BytesIO(content), encoding=enc)
                        st.info(f"💡 已識別編碼: {enc}")
                        break
                    except: continue
            else:
                df = pd.read_excel(uploaded_file)
            
            st.dataframe(df.head())
            if st.button("🚀 確認批量匯入"):
                upload_to_db(df)
        except Exception as e:
            st.error(f"🚨 讀取失敗: {e}")

# --- Tab 2: 智慧文字解析 ---
with tab2:
    col_l, col_r = st.columns(2)
    with col_l:
        in_cat = st.selectbox("分類", ["手遊", "端遊", "點數卡", "其他"])
        in_img = st.text_input("🖼️ 封面網址")
    with col_r:
        bulk_text = st.text_area("直接貼上報價單 (範例：【遊戲】▪️品項=100NT)", height=200)
    
    if st.button("✨ 執行解析並上傳"):
        if bulk_text:
            gn = (re.search(r'【(.*?)】', bulk_text).group(1)) if '【' in bulk_text else "未命名"
            lines = bulk_text.strip().split('\n')
            data = []
            for line in lines:
                if '=' in line:
                    p = line.split('=')
                    it = p[0].replace('▪️', '').strip()
                    pr = float(re.sub(r'[^\d.]', '', p[1]))
                    data.append([in_cat, gn, it, pr, in_img if in_img else "https://via.placeholder.com/400x300.png"])
            upload_to_db(pd.DataFrame(data, columns=['category', 'game_name', 'item_name', 'price', 'image_url']))

# --- Tab 3: 資料管理 (刪除功能) ---
with tab3:
    conn = get_conn()
    df_all = pd.read_sql("SELECT DISTINCT game_name FROM GameData", conn)
    target = st.selectbox("🗑️ 選擇要批量刪除的遊戲", df_all['game_name'].tolist() if not df_all.empty else [])
    if st.button(f"確認刪除 {target} 及其所有價目", type="primary"):
        cur = conn.cursor()
        cur.execute("DELETE FROM GameData WHERE game_name = %s", (target,))
        conn.commit()
        conn.close()
        st.success(f"已清空 {target}")
        st.rerun()
