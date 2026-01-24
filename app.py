import streamlit as st
import psycopg2
import pandas as pd

# --- 1. 網頁基本設定 ---
st.set_page_config(
    page_title="姆斯遊戲價格查詢系統",
    page_icon="🎮",
    layout="centered"
)

# --- 2. 安全連線函式 ---
# 使用 st.cache_resource 避免每次搜尋都重新連線資料庫，提高效能
@st.cache_resource
def get_connection():
    try:
        return psycopg2.connect(
            host=st.secrets["DB_HOST"],
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASS"],
            port=st.secrets["DB_PORT"]
        )
    except Exception as e:
        st.error(f"❌ 資料庫連線失敗，請檢查 Secrets 設定：{e}")
        return None

# --- 3. 資料查詢邏輯 ---
def search_prices(keyword):
    conn = get_connection()
    if conn:
        try:
            # 使用 ILIKE 進行不分大小寫的模糊搜尋
            query = """
            SELECT 
                category AS "類別", 
                game_name AS "遊戲名稱", 
                item_name AS "商品內容", 
                price AS "價格 (NT)"
            FROM GamePrices
            WHERE game_name ILIKE %s OR item_name ILIKE %s
            ORDER BY game_name, price ASC;
            """
            # 使用 pandas 處理查詢結果
            df = pd.read_sql(query, conn, params=(f'%{keyword}%', f'%{keyword}%'))
            return df
        except Exception as e:
            st.error(f"🔍 查詢時發生錯誤：{e}")
            return None
    return None

# --- 4. 網頁介面設計 ---
def main():
    st.title("🎮 姆斯遊戲價格查詢系統")
    st.markdown("---")
    
    # 搜尋框與說明
    st.write("請輸入您想查詢的**遊戲名稱**或**商品內容**（如：點券、硬幣）")
    keyword = st.text_input("🔍 搜尋框", placeholder="例如：傳說對決、特戰、Apex...")

    if keyword:
        with st.spinner('正在從雲端資料庫抓取最新價格...'):
            df_result = search_prices(keyword)
            
            if df_result is not None:
                if not df_result.empty:
                    st.success(f"✅ 找到 {len(df_result)} 筆相關結果")
                    
                    # 顯示資料表格
                    # hide_index=True 隱藏左側無意義的序號
                    st.dataframe(
                        df_result, 
                        use_container_width=True, 
                        hide_index=True
                    )
                    
                    st.info("💡 小撇步：點擊表格標題（如：價格）可以進行即時排序喔！")
                else:
                    st.warning(f"查無資料：找不到關於 '{keyword}' 的內容，請嘗試縮短關鍵字。")
    else:
        # 未搜尋時顯示的歡迎畫面
        st.info("請在上方輸入關鍵字開始查詢。")
        
    # 頁尾
    st.markdown("---")
    st.caption("© 2026 姆斯遊戲服務 | 雲端資料庫即時連線中")

if __name__ == "__main__":
    main()