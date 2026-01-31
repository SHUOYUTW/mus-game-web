import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="姆斯遊戲商城", layout="wide")

# CSS 美化卡片
st.markdown("""
    <style>
    .game-card { border: 1px solid #ddd; border-radius: 12px; padding: 10px; text-align: center; transition: 0.3s; background: white; }
    .game-card:hover { border-color: #ee4d2d; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .price-row { background: #262730; color: white; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 5px solid #ee4d2d; }
    </style>
""", unsafe_allow_html=True)

def main():
    if "selected_game" not in st.session_state:
        st.session_state.selected_game = None

    conn = psycopg2.connect(host=st.secrets["DB_HOST"], database=st.secrets["DB_NAME"], 
                            user=st.secrets["DB_USER"], password=st.secrets["DB_PASS"], 
                            port=st.secrets["DB_PORT"], sslmode="require")

    # --- 詳情頁 ---
    if st.session_state.selected_game:
        game = st.session_state.selected_game
        if st.button("⬅️ 返回首頁"):
            st.session_state.selected_game = None
            st.rerun()
        st.title(f"🔥 {game} - 報價單")
        df = pd.read_sql("SELECT item_name, price FROM GameData WHERE game_name = %s ORDER BY price ASC", conn, params=(game,))
        for _, row in df.iterrows():
            st.markdown(f'<div class="price-row"><span>▪️ {row["item_name"]}</span><span style="float:right; color:#ee4d2d; font-size:20px;">{int(row["price"]):,} NT</span></div>', unsafe_allow_html=True)

    # --- 首頁 (網格) ---
    else:
        st.title("🛍️ 姆斯遊戲服務商城")
        df_games = pd.read_sql("SELECT DISTINCT game_name, image_url FROM GameData", conn)
        cols = st.columns(4)
        for i, row in df_games.iterrows():
            with cols[i % 4]:
                st.markdown(f'<div class="game-card">', unsafe_allow_html=True)
                st.image(row['image_url'], use_container_width=True)
                st.write(f"**{row['game_name']}**")
                if st.button("查看報價", key=f"btn_{i}", use_container_width=True):
                    st.session_state.selected_game = row['game_name']
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    conn.close()

if __name__ == "__main__":
    main()
