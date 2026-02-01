import streamlit as st
import psycopg2, pandas as pd, re, io, urllib.parse

st.set_page_config(page_title="姆斯後台", layout="wide", page_icon="⚙️")

def get_connection():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"], database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"], password=st.secrets["DB_PASS"],
        port=st.secrets["DB_PORT"], sslmode="require"
    )

st.title("🛡️ 姆斯商城 - 管理後台")
tab1, tab2, tab3, tab4 = st.tabs(["📁 高速檔案匯入", "🚀 文字解析", "📊 管理與勾選刪除", "⚠️ 重置"])

# --- Tab 1: 批量匯入 (高速版) ---
with tab1:
    in_cat = st.radio("選擇分類", ["手遊", "端遊", "點數卡"], horizontal=True)
    uploaded_file = st.file_uploader("上傳 CSV/Excel", type=["csv", "xlsx"])
    if uploaded_file:
        df_u = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        if st.button("🚀 開始高速批量匯入"):
            conn = get_connection()
            cur, data_to_insert = conn.cursor(), []
            for _, row in df_u.iterrows():
                gn, txt = str(row.iloc[0]).strip(), str(row.iloc[1])
                if not txt or "報價單" in gn: continue
                img = f"https://api.dicebear.com/7.x/initials/svg?seed={urllib.parse.quote(gn)}&backgroundColor=F14668"
                for line in txt.split('\n'):
                    if '=' in line:
                        p = line.split('=')
                        it, pr = p[0].replace('▪️', '').strip(), float(re.sub(r'[^\d.]', '', p[1]))
                        data_to_insert.append((in_cat, gn, it, pr, img))
            cur.executemany("INSERT INTO GameData (category, game_name, item_name, price, image_url) VALUES (%s,%s,%s,%s,%s)", data_to_insert)
            conn.commit()
            conn.close()
            st.success(f"匯入成功 {len(data_to_insert)} 筆！")

# --- Tab 3: 管理與勾選刪除 ---
with tab3:
    conn = get_connection()
    df_all = pd.read_sql("SELECT id, game_name, item_name, price FROM GameData ORDER BY game_name ASC", conn)
    if not df_all.empty:
        st.subheader("🗑️ 勾選式單項刪除")
        df_all.insert(0, "選取", False)
        edited_df = st.data_editor(df_all, hide_index=True, column_config={"選取": st.column_config.CheckboxColumn(required=True)}, disabled=["id", "game_name", "item_name", "price"], use_container_width=True)
        selected_ids = edited_df[edited_df["選取"] == True]["id"].tolist()
        if selected_ids and st.button(f"🔥 刪除選中的 {len(selected_ids)} 筆"):
            cur = conn.cursor()
            cur.execute("DELETE FROM GameData WHERE id IN %s", (tuple(selected_ids),))
            conn.commit()
            st.rerun()
        
        st.divider()
        st.subheader("🖼️ 更換封面圖")
        target_g = st.selectbox("選擇遊戲", df_all['game_name'].unique())
        new_url = st.text_input("圖片網址")
        if st.button("🎨 更新照片") and new_url:
            cur = conn.cursor()
            cur.execute("UPDATE GameData SET image_url = %s WHERE game_name = %s", (new_url, target_g))
            conn.commit()
            st.success("更新成功")
    conn.close()
