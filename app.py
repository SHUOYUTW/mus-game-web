import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="姆斯遊戲商城", layout="wide")

# CSS 美化：網格卡片與報價單樣式
st.markdown("""
    <style>
    .game-card { border: 1px solid #eee; border-radius: 15px; padding: 15px; text-align: center; background: white; transition: 0.3s; }
    .game-card:hover { border-color: #ee4d2d; box-shadow: 0 5px 15px rgba(0,0,0,0.1); transform: translateY(-3px); }
    .price-row { background: #262730; color: white; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 5px solid #ee4d2d; font-family: monospace; }
    </style>
""", unsafe_allow_html=True)

def get_conn():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"], database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"], password=st.secrets["DB_PASS"],
        port=st.secrets["DB_PORT"], sslmode="require", connect_timeout=10
    )

def main():
    if "selected_game" not in st.session_state:
        st.session_state.selected_game = None

    try:
        conn = get_conn()
    except Exception as e:
        st.error("⚠️ 資料庫連線中，請檢查 Secrets 設定...")
        return

    # --- 頁面 B：詳情報價單 ---
    if st.session_state.selected_game:
        game = st.session_state.selected_game
        if st.button("⬅️ 返回商城"):
            st.session_state.selected_game = None
            st.rerun()
        
        st.title(f"🔥 {game} - 報價單")
        df = pd.read_sql("SELECT item_name, price FROM GameData WHERE game_name = %s ORDER BY price ASC", conn, params=(game,))
        
        if df.empty:
            st.warning("此遊戲暫無資料。")
        else:
            for _, row in df.iterrows():
                st.markdown(f'<div class="price-row"><span style="font-size:18px;">▪️ {row["item_name"]}</span><span style="float:right; color:#ee4d2d; font-size:20px; font-weight:bold;">{int(row["price"]):,} NT</span></div>', unsafe_allow_html=True)

    # --- 頁面 A：商城首頁 (網格) ---
    else:
        st.title("🛍️ 姆斯遊戲服務商城")
        df_games = pd.read_sql("SELECT DISTINCT game_name, image_url FROM GameData", conn)
        
        if df_games.empty:
            st.info("🏪 歡迎光臨！請至後台匯入 Excel 資料庫。")
        else:
            cols = st.columns(4)
            for i, row in df_games.iterrows():
                with cols[i % 4]:
                    st.markdown('<div class="game-card">', unsafe_allow_html=True)
                    st.image(row['image_url'], use_container_width=True)
                    st.subheader(row['game_name'])
                    if st.button("查看報價", key=f"view_{i}", use_container_width=True):
                        st.session_state.selected_game = row['game_name']
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    conn.close()

if __name__ == "__main__":
    main()
