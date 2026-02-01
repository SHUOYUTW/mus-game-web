import streamlit as st
import psycopg2
import pandas as pd

# 1. 頁面基本設定
st.set_page_config(page_title="姆斯遊戲服務商城", layout="wide", page_icon="🎮")

# 2. 讀取外部 CSS 函式
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"無法載入樣式表: {e}")

local_css("front_style.css")

# 3. 資料庫連線 (請確保 Secrets 已設定)
def get_conn():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASS"],
        port=st.secrets["DB_PORT"],
        sslmode="require"
    )

# 4. 購物狀態管理
if "viewing_game" not in st.session_state:
    st.session_state.viewing_game = None

# --- [主要顯示邏輯] ---
def main():
    conn = get_conn()
    
    # A. 詳情頁面 (當使用者點擊了某個遊戲)
    if st.session_state.viewing_game:
        game_name = st.session_state.viewing_game
        if st.button("⬅️ 返回商城列表"):
            st.session_state.viewing_game = None
            st.rerun()
            
        st.title(f"🔥 {game_name} - 最新報價單")
        
        query = "SELECT item_name, price FROM GameData WHERE game_name = %s ORDER BY price ASC"
        df = pd.read_sql(query, conn, params=(game_name,))
        
        if not df.empty:
            for _, row in df.iterrows():
                # 套用 CSS 中的 .price-item 類別
                st.markdown(f"""
                    <div class="price-item">
                        <span class="price-label">▪️ {row['item_name']}</span>
                        <span class="price-value">{int(row['price']):,} NT</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("目前尚無報價，請聯絡管理員更新。")

    # B. 商城首頁 (遊戲清單)
    else:
        st.title("🎮 姆斯遊戲服務商城")
        st.markdown("#### 選擇遊戲查看即時報價")
        
        query_games = "SELECT DISTINCT game_name, image_url FROM GameData"
        df_games = pd.read_sql(query_games, conn)
        
        if df_games.empty:
            st.warning("🏪 店家正在補貨中，請稍後再試！")
        else:
            # 使用 4 欄位的網格排版
            cols = st.columns(4)
            for i, row in df_games.iterrows():
                with cols[i % 4]:
                    # 套用 CSS 中的 .game-card 類別
                    st.markdown(f"""
                        <div class="game-card">
                            <img src="{row['image_url']}" class="game-img">
                            <h3 style="margin: 10px 0;">{row['game_name']}</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # 使用按鈕來切換狀態
                    if st.button(f"查看 {row['game_name']} 報價", key=f"btn_{row['game_name']}", use_container_width=True):
                        st.session_state.viewing_game = row['game_name']
                        st.rerun()
    
    conn.close()

if __name__ == "__main__":
    main()
