import streamlit as st
import psycopg2
import pandas as pd
import re
import io
import urllib.parse

st.set_page_config(page_title="姆斯電商-管理後台", layout="wide", page_icon="⚙️")

def get_connection():
    try:
        return psycopg2.connect(
            host=st.secrets["DB_HOST"],
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASS"],
            port=st.secrets["DB_PORT"],
            sslmode="require",
            connect_timeout=10
        )
    except Exception as e:
        st.error(f"❌ 連線失敗: {e}")
        return None

st.title("🛡️ 姆斯遊戲商城 - 管理後台")

# --- 分頁設定 ---
tab1, tab2, tab3, tab4 = st.tabs(["📁 檔案匯入", "🚀 文字解析", "📊 資料管理 & 單筆刪除", "⚠️ 危險區域"])

# ... (Tab 1 & 2 保持不變，略過以縮短回應長度) ...

# --- Tab 3: 資料管理 & 單筆刪除 (全新優化版) ---
with tab3:
    conn = get_connection()
    if conn:
        try:
            # 讀取全部資料備用
            df_all = pd.read_sql("SELECT * FROM GameData ORDER BY game_name ASC, price ASC", conn)
            
            if df_all.empty:
                st.info("目前資料庫沒有資料，請先前往匯入。")
            else:
                # --- 區塊 A：更換封面照片 (維持原功能) ---
                st.subheader("🖼️ 更改遊戲封面圖")
                game_list = df_all['game_name'].unique()
                c_pic1, c_pic2 = st.columns([1, 2])
                with c_pic1:
                    target_game = st.selectbox("選擇遊戲", game_list, key="sel_pic")
                with c_pic2:
                    new_url = st.text_input("輸入新圖片連結", placeholder="https://...")
                if st.button("🎨 更新照片"):
                    cur = conn.cursor()
                    cur.execute("UPDATE GameData SET image_url = %s WHERE game_name = %s", (new_url, target_game))
                    conn.commit()
                    st.success("更新成功")
                    st.rerun()

                st.divider()

                # --- 區塊 B：單筆面額刪除 (新功能！) ---
                st.subheader("🗑️ 單筆面額管理")
                st.write("先選擇遊戲，再選擇要刪除的具體品項：")
                
                col_del1, col_del2 = st.columns(2)
                with col_del1:
                    sel_game_for_item = st.selectbox("1. 選擇要管理的遊戲", game_list, key="sel_del_game")
                
                # 根據選中的遊戲，篩選出該遊戲的所有面額
                items_df = df_all[df_all['game_name'] == sel_game_for_item]
                
                with col_del2:
                    # 建立一個選項字串，方便管理員辨識
                    item_options = items_df.apply(lambda x: f"ID:{x['id']} | {x['item_name']} = {int(x['price'])}元", axis=1).tolist()
                    sel_item_str = st.selectbox("2. 選擇要刪除的面額品項", item_options, key="sel_del_item")
                
                if st.button("❌ 確認刪除該筆品項", type="primary"):
                    # 從字串中提取 ID
                    target_id = int(sel_item_str.split('|')[0].replace('ID:', '').strip())
                    cur = conn.cursor()
                    cur.execute("DELETE FROM GameData WHERE id = %s", (target_id,))
                    conn.commit()
                    st.success(f"已成功刪除該面額資料！")
                    st.rerun()

                st.divider()

                # --- 區塊 C：資料瀏覽 ---
                st.subheader("🔍 資料庫全覽")
                search = st.text_input("搜尋關鍵字...")
                df_view = df_all[df_all['game_name'].str.contains(search) | df_all['item_name'].str.contains(search)] if search else df_all
                st.dataframe(df_view, use_container_width=True)

        finally:
            conn.close()

# --- Tab 4: 危險區域 (維持原樣) ---
# ... (略)
