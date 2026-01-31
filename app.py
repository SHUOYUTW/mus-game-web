import streamlit as st
import psycopg2
import pandas as pd
import io
import re

st.set_page_config(page_title="姆斯遊戲商城", layout="wide")

# --- 資料庫連線函式 ---
def get_conn():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"], database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"], password=st.secrets["DB_PASS"],
        port=st.secrets["DB_PORT"], sslmode="require", connect_timeout=10
    )

# --- 導覽列 ---
menu = st.sidebar.selectbox("選單", ["🛒 遊戲商城首頁", "⚙️ 管理員後台"])

# ================= 頁面 1：遊戲商城首頁 =================
if menu == "🛒 遊戲商城首頁":
    st.title("🛍️ 姆斯遊戲服務商城")
    
    if "selected_game" not in st.session_state:
        st.session_state.selected_game = None

    try:
        conn = get_conn()
        if st.session_state.selected_game:
            # 詳情頁
            game = st.session_state.selected_game
            if st.button("⬅️ 返回首頁"):
                st.session_state.selected_game = None
                st.rerun()
            st.header(f"🔥 {game} - 報價單")
            df = pd.read_sql("SELECT item_name, price FROM GameData WHERE game_name = %s ORDER BY price ASC", conn, params=(game,))
            for _, row in df.iterrows():
                st.info(f"🔹 {row['item_name']} ——— 💰 {int(row['price'])} NT")
        else:
            # 首頁網格
            df_games = pd.read_sql("SELECT DISTINCT game_name, image_url FROM GameData", conn)
            if df_games.empty:
                st.warning("目前資料庫空空如也，請先去「管理員後台」上傳 CSV。")
            else:
                cols = st.columns(4)
                for i, row in df_games.iterrows():
                    with cols[i % 4]:
                        st.image(row['image_url'], use_container_width=True)
                        st.write(f"**{row['game_name']}**")
                        if st.button("查看價格", key=f"btn_{i}"):
                            st.session_state.selected_game = row['game_name']
                            st.rerun()
        conn.close()
    except Exception as e:
        st.error(f"連線錯誤: {e}")

# ================= 頁面 2：管理員後台 (上傳功能) =================
else:
    st.title("⚙️ 管理員後台 - 智慧解析匯入")
    
    cat = st.radio("🏷️ 步驟 1：選擇此檔案的分類", ["手遊", "端遊", "點數卡"])
    uploaded_file = st.file_uploader("📂 步驟 2：上傳原始 CSV 報價單", type=["csv"])

    if uploaded_file:
        content = uploaded_file.read()
        df = None
        for enc in ['utf-8-sig', 'cp950', 'big5']:
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=enc)
                break
            except: continue
        
        if df is not None:
            st.write("📊 偵測到的檔案內容預覽：")
            st.dataframe(df.head(10))
            
            if st.button("🚀 步驟 3：開始解析並寫入資料庫"):
                conn = get_conn()
                cur = conn.cursor()
                count = 0
                for _, row in df.iterrows():
                    game_name = str(row.iloc[0]).strip()
                    bulk_text = str(row.iloc[1])
                    if not bulk_text or bulk_text == 'nan' or "遊戲名稱" in game_name: continue
                    lines = bulk_text.split('\n')
                    for line in lines:
                        if '=' in line:
                            try:
                                parts = line.split('=')
                                item = parts[0].replace('💥', '').replace('▪️', '').strip()
                                price_str = re.sub(r'[^\d.]', '', parts[1])
                                if price_str:
                                    cur.execute("INSERT INTO GameData (category, game_name, item_name, price, image_url) VALUES (%s, %s, %s, %s, %s)",
                                                (cat, game_name, item, float(price_str), "https://via.placeholder.com/400x300.png"))
                                    count += 1
                            except: continue
                conn.commit()
                conn.close()
                st.success(f"✨ 成功匯入 {count} 筆面額！")
