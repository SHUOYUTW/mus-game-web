import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="姆斯遊戲商城", layout="wide", page_icon="🎮")

# 讀取 CSS
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except: pass

local_css("front_style.css")

def get_conn():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"], database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"], password=st.secrets["DB_PASS"],
        port=st.secrets["DB_PORT"], sslmode="require"
    )

if "viewing_game" not in st.session_state:
    st.session_state.viewing_game = None

conn = get_conn()

if st.session_state.viewing_game:
    # 詳情報價頁
    game = st.session_state.viewing_game
    if st.button("⬅️ 返回商城列表"):
        st.session_state.viewing_game = None
        st.rerun()
    
    st.title(f"🔥 {game} - 報價單")
    df = pd.read_sql("SELECT item_name, price FROM GameData WHERE game_name = %s ORDER BY price ASC", conn, params=(game,))
    for _, row in df.iterrows():
        st.markdown(f'<div class="price-item"><span class="price-label">▪️ {row["item_name"]}</span><span class="price-value">{int(row["price"]):,} NT</span></div>', unsafe_allow_html=True)
else:
    # 商城首頁
    st.title("🎮 姆斯遊戲服務商城")
    df_games = pd.read_sql("SELECT DISTINCT game_name, image_url FROM GameData", conn)
    if df_games.empty:
        st.warning("🏪 補貨中，請稍後...")
    else:
        cols = st.columns(4)
        for i, row in df_games.iterrows():
            with cols[i % 4]:
                st.markdown(f'<div class="game-card"><img src="{row["image_url"]}" class="game-img"><h3>{row["game_name"]}</h3></div>', unsafe_allow_html=True)
                if st.button(f"查看報價", key=f"btn_{i}", use_container_width=True):
                    st.session_state.viewing_game = row['game_name']
                    st.rerun()
conn.close()
