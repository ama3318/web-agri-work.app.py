import streamlit as st
import json
import os
from datetime import datetime

# --- ページ設定 ---
st.set_page_config(page_title="農作業メモ v4.0", layout="wide")

FILENAME = 'garden_records.json'

# --- 1. 共通関数 ---
def load_data():
    if os.path.exists(FILENAME):
        with open(FILENAME, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(FILENAME, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def parse_garden_date(date_input):
    try:
        clean_input = date_input.replace("月", "/").replace("日", "").strip()
        parts = clean_input.split("/")
        month, day = int(parts[0]), int(parts[1])
        now = datetime.now()
        year = now.year
        if now.month >= 10 and month <= 3: year += 1
        elif now.month <= 3 and month >= 10: year -= 1
        return datetime(year, month, day)
    except:
        return datetime.now()

# --- 2. パスワード認証機能 ---
def check_password():
    """正しいパスワードが入力されたら True を返す"""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # 既に認証済みならスルー
    if st.session_state["password_correct"]:
        return True

    # ログイン画面の表示
    st.title("🔒 認証が必要です")
    password = st.text_input("パスワードを入力してください", type="password")
    
    # 💡 サーバー公開時は st.secrets から、ローカルテスト時は直接設定
    correct_password = st.secrets.get("password", "admin123")  # デフォルトは admin123

    if st.button("ログイン"):
        if password == correct_password:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("パスワードが違います")
    return False

# --- 認証チェック ---
if check_password():
    # データを読み込み
    if "garden_records" not in st.session_state:
        st.session_state.garden_records = load_data()
    
    records = st.session_state.garden_records

    # --- 3. メイン画面の構築 ---
    st.title("🥬 農作業メモ v4.0 (Web版)")

    # 画面を2カラムに分割 (左: リストと選択、右: 詳細と入力)
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("登録済み野菜")
        n_list = sorted(list(records.keys()))
        
        # セレクトボックスで野菜を選択
        selected_name = st.selectbox("野菜を選ぶか、下に入力してください", ["(新規登録)"] + n_list)
        
        # 新規入力用のテキストボックス
        input_name = st.text_input("野菜名（新規・検索）")
        
        # 最終的な判定
        name = input_name.strip() if input_name.strip() else (selected_name if selected_name != "(新規登録)" else "")

    with col2:
        if name:
            st.subheader(f"【{name}】の作業履歴")
            
            # --- 履歴の表示・編集・削除 ---
            if name in records and records[name]:
                # テーブル表示用のデータ作成
                table_data = []
                for idx, r in enumerate(records[name]):
                    table_data.append({
                        "インデックス": idx,
                        "日付": r["日付"],
                        "内容": r["内容"],
                        "備考": r["備考"]
                    })
                
                # データフレームとして表示
                st.dataframe(table_data, use_container_width=True, hide_index=True)
                
                # 編集・削除用のアコーディオン
                with st.expander("選択して履歴を編集・削除"):
                    edit_idx = st.selectbox("編集・削除する行番号(インデックス)", [d["インデックス"] for d in table_data])
                    current_row = records[name][edit_idx]
                    
                    e_date = st.text_input("編集後の日付", value=current_row["日付"], key="e_date")
                    e_action = st.text_input("編集後の内容", value=current_row["内容"], key="e_action")
                    e_note = st.text_input("編集後の備考", value=current_row["備考"], key="e_note")
                    
                    b_col1, b_col2 = st.columns(2)
                    with b_col1:
                        if st.button("選択行を上書き保存", type="primary"):
                            records[name][edit_idx] = {"日付": e_date, "内容": e_action, "備考": e_note}
                            records[name].sort(key=lambda x: parse_garden_date(x['日付']))
                            save_data(records)
                            st.success("上書き保存しました！")
                            st.rerun()
                    with b_col2:
                        if st.button("選択行を削除", help="赤いボタン"):
                            records[name].pop(edit_idx)
                            if not records[name]:
                                del records[name]
                            save_data(records)
                            st.warning("削除しました")
                            st.rerun()
            else:
                st.info(f"{name} の記録は見つかりませんでした。新しく追加できます。")

            st.markdown("---")
            
            # --- 新しい記録の追加 ---
            st.subheader("✍️ 新しい記録の追加")
            
            # 日付の初期値に今日の日付を設定（手入力も可能）
            default_date = datetime.now().strftime("%m/%d")
            new_date = st.text_input("日付:", value=default_date)
            new_action = st.text_input("内容:")
            new_note = st.text_input("備考:")
            
            if st.button("記録を保存", type="primary"):
                if not name or not new_date:
                    st.error("野菜名と日付を入力してください")
                else:
                    if name not in records:
                        records[name] = []
                    records[name].append({
                        "日付": new_date,
                        "内容": new_action,
                        "備考": new_note
                    })
                    records[name].sort(key=lambda x: parse_garden_date(x['日付']))
                    save_data(records)
                    st.success(f"【{name}】の記録を保存しました！")
                    st.rerun()
        else:
            st.info("左側のリストから野菜を選ぶか、新しい野菜名を入力してください。")
