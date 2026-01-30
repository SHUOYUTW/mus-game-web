import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="姆斯遊戲商城", layout="wide", page_icon="🎮")

@st.cache_resource
def get_connection():
    try:
        return psycopg2.connect(
            host=st.secrets["DB_HOST"],
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASS"],
            port=st.secrets["DB_PORT"],
            sslmode="require"
        )
    except:
        return None

# 蝦皮橘色風格 CSS
st.markdown("""
    <style>
    .game-card {
        background-color: #ffffff; border: 1px solid #ddd; border-radius: 8px;
        text-align: center; transition: 0.3s; cursor: pointer; color: #333;
    }
    .game-card:hover { border-color: #ee4d2d; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .price-card {
        background-color: #262730; border-radius: 10px; padding: 20px;
        margin-bottom: 12px; border-left: 5px solid #ee4d2d;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    if "selected_game" not in st.session_state:
        st.session_state.selected_game = None

    conn = get_connection()
    if not conn:
        st.error("資料庫連線中...")
        return

    # --- 詳情頁 ---
    if st.session_state.selected_game:
        game = st.session_state.selected_game
        if st.button("⬅️ 返回首頁"):
            st.session_state.selected_game = None
            st.rerun()
        
        st.title(f"🔥 {game} 價目表")
        df_items = pd.read_sql("SELECT item_name, price FROM GamePrices WHERE game_name = %s ORDER BY price ASC", conn, params=(game,))
        
        for i, row in df_items.iterrows():
            st.markdown(f"""
                <div class="price-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-size: 18px; color: white;">▪️ {row['item_name']}</div>
                        <div style="color: #ee4d2d; font-size: 24px; font-weight: bold;">{int(row['price']):,} NT</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.button(f"📋 複製報價", key=f"cp_{i}")

    # --- 首頁 (網格展示) ---
    else:
        st.title("🛍️ 姆斯遊戲商城")
        df_games = pd.read_sql("SELECT DISTINCT ON (game_name) game_name, image_url FROM GamePrices", conn)
        
        if df_games.empty:
            st.info("目前還沒有資料，請先去管理端新增喔！")
        else:
            cols = st.columns(4)
            for i, row in df_games.reset_index().iterrows():
                with cols[i % 4]:
                    st.markdown('<div class="game-card">', unsafe_allow_html=True)
                    st.image(row['image_url'], use_container_width=True)
                    st.markdown(f"<div style='padding:10px;'><b>{row['game_name']}</b></div>", unsafe_allow_html=True)
                    if st.button("查看價目", key=f"go_{row['game_name']}", use_container_width=True):
                        st.session_state.selected_game = row['game_name']
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
