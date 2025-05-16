import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

st.set_page_config(page_title="GreenClass - Thi đua giảm rác nhựa", layout="wide")

# ==== Cấu hình màu sắc và tiêu đề ====
st.markdown("""
    <style>
    .title {
        font-size:50px !important;
        color: #2E8B57;
        text-align: center;
        font-weight: bold;
    }
    .subtitle {
        font-size:24px !important;
        color: #4682B4;
        font-weight: bold;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>GreenClass - Thi đua giảm rác nhựa</div>", unsafe_allow_html=True)

# ==== Danh sách lớp và mật khẩu ====
lop_pass = {f"{khoi}A{i}": "123" for khoi in ['10', '11', '12'] for i in range(1, 9)}
lop_pass["GIAOVIEN"] = "123"

# ==== Khởi tạo session_state ====
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = ""
if 'lop' not in st.session_state:
    st.session_state.lop = ""

# ==== Giao diện đăng nhập ====
if not st.session_state.logged_in:
    role = st.selectbox("Bạn là:", ["Học sinh", "Giáo viên"])
    if role == "Học sinh":
        lop = st.selectbox("Chọn lớp của bạn", [lop for lop in lop_pass if lop != "GIAOVIEN"])
    else:
        lop = "GIAOVIEN"

    matkhau = st.text_input("Nhập mật khẩu", type="password")
    if st.button("Đăng nhập"):
        if lop in lop_pass and lop_pass[lop] == matkhau:
            st.session_state.logged_in = True
            st.session_state.user_role = role
            st.session_state.lop = lop
            st.success("Đăng nhập thành công!")
        else:
            st.error("Sai mật khẩu!")
    st.stop()

# ==== Giao diện Học sinh ====
if st.session_state.user_role == "Học sinh":
    st.markdown("<div class='subtitle'>📥 Nhập dữ liệu sử dụng sản phẩm nhựa</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        so_chai = st.number_input("Số chai nhựa đã dùng", min_value=0, step=1)
        so_ly = st.number_input("Số ly nhựa đã dùng", min_value=0, step=1)
    with col2:
        so_tui = st.number_input("Số túi nylon đã dùng", min_value=0, step=1)
        so_khac = st.number_input("Sản phẩm nhựa khác", min_value=0, step=1)

    if st.button("📌 Gửi dữ liệu"):
        data = {
            "Thời gian": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "Lớp": [st.session_state.lop],
            "Chai": [so_chai],
            "Ly": [so_ly],
            "Túi nylon": [so_tui],
            "Khác": [so_khac]
        }
        df_new = pd.DataFrame(data)
        try:
            old_df = pd.read_csv("data.csv")
            df = pd.concat([old_df, df_new], ignore_index=True)
        except FileNotFoundError:
            df = df_new
        df.to_csv("data.csv", index=False)
        st.success("Đã gửi dữ liệu thành công!")

# ==== Giao diện Giáo viên ====
if st.session_state.user_role == "Giáo viên":
    st.markdown("<div class='subtitle'>📊 Thống kê thi đua giảm rác nhựa theo tuần</div>", unsafe_allow_html=True)

    try:
        df = pd.read_csv("data.csv")
        df["Thời gian"] = pd.to_datetime(df["Thời gian"])
    except FileNotFoundError:
        st.warning("Chưa có dữ liệu nào được nhập.")
        st.stop()

    df["Tuần"] = df["Thời gian"].dt.isocalendar().week
    df["Năm"] = df["Thời gian"].dt.isocalendar().year
    df["Tuần_full"] = df["Năm"].astype(str) + " - Tuần " + df["Tuần"].astype(str).str.zfill(2)

    unique_weeks = df["Tuần_full"].drop_duplicates().sort_values(ascending=False)
    selected_week = st.selectbox("📅 Chọn tuần để thống kê:", unique_weeks)

    def get_week_range(year: int, week: int):
        start = datetime.strptime(f'{year}-W{week}-1', "%G-W%V-%u").date()
        end = start + timedelta(days=6)
        return pd.to_datetime(start), pd.to_datetime(end)

    year, week = map(int, selected_week.replace(" - Tuần ", "-").split("-"))
    start_date, end_date = get_week_range(year, week)
    st.write(f"📆 Từ **{start_date.date()}** đến **{end_date.date()}**")

    df_week = df[(df["Thời gian"] >= start_date) & (df["Thời gian"] <= end_date)].copy()
    if df_week.empty:
        st.info("⛔ Không có dữ liệu trong tuần này.")
        st.stop()

    df_week["Số lượng"] = df_week[["Chai", "Ly", "Túi nylon", "Khác"]].sum(axis=1)

    df_summary = df_week.groupby("Lớp")["Số lượng"].sum().reset_index()
    df_summary = df_summary.rename(columns={"Số lượng": "Tổng rác thải"})
    df_summary["Xếp hạng"] = df_summary["Tổng rác thải"].rank(method="min", ascending=True).astype(int)
    df_summary = df_summary.sort_values("Xếp hạng")

    st.markdown("### 🏆 Bảng xếp hạng các lớp")
    st.dataframe(df_summary.reset_index(drop=True), use_container_width=True)

    import io
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_summary.to_excel(writer, index=False, sheet_name='XepHangLop')
    output.seek(0)
    st.download_button(
        label="⬇️ Tải bảng xếp hạng ra Excel",
        data=output,
        file_name=f"xep_hang_tuan_{year}_{week}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
