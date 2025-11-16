import streamlit as st
import pandas as pd
import sqlite3
import time
from datetime import datetime

# Kết nối SQLite
conn = sqlite3.connect('guests.db')
c = conn.cursor()

# Tạo bảng nếu chưa có
c.execute('''CREATE TABLE IF NOT EXISTS guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    position TEXT,
    checked_in BOOLEAN DEFAULT 0,
    gift_received BOOLEAN DEFAULT 0,
    check_in_time TEXT,
    gift_confirm_time TEXT
)''')
conn.commit()

# Hàm load dữ liệu từ DB
def load_guests():
    df = pd.read_sql_query("SELECT * FROM guests", conn)
    return df

# Hàm save dữ liệu vào DB
def save_guest(name, position):
    c.execute("INSERT INTO guests (name, position) VALUES (?, ?)", (name, position))
    conn.commit()

# Hàm update check-in
def update_checkin(guest_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE guests SET checked_in = 1, check_in_time = ? WHERE id = ?", (now, guest_id))
    conn.commit()

# Hàm update gift received
def update_gift(guest_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE guests SET gift_received = 1, gift_confirm_time = ? WHERE id = ?", (now, guest_id))
    conn.commit()

# Hàm import từ Excel
def import_excel(uploaded_file):
    df = pd.read_excel(uploaded_file, usecols=['name', 'position'])
    for _, row in df.iterrows():
        save_guest(row['name'], row['position'])

# Hàm lọc dữ liệu
def filter_guests(df, search, checkin_filter, gift_filter):
    if search:
        df = df[df['name'].str.contains(search, case=False) | df['position'].str.contains(search, case=False)]
    if checkin_filter == "Đã check-in":
        df = df[df['checked_in'] == 1]
    elif checkin_filter == "Chưa check-in":
        df = df[df['checked_in'] == 0]
    if gift_filter == "Đã nhận quà":
        df = df[df['gift_received'] == 1]
    elif gift_filter == "Chưa nhận quà":
        df = df[df['gift_received'] == 0]
    return df

# UI Streamlit với sidebar
st.set_page_config(page_title="Quản lý Khách mời", page_icon="🎉", layout="wide")

# CSS cho theme xanh và hình khối
st.markdown("""
    <style>
    body { background-color: #e0f7fa; }  /* Xanh nhạt */
    .stButton>button { background-color: #00796b; color: white; border-radius: 10px; border: 2px solid #004d40; box-shadow: 2px 2px 5px #004d40; width: 100%; height: 50px; font-size: 18px; }
    .stTextInput, .stSelectbox, .stFileUploader { border-radius: 10px; border: 2px solid #00796b; padding: 10px; }
    .stExpander { border: 2px solid #00796b; border-radius: 10px; box-shadow: 2px 2px 5px #004d40; margin-bottom: 10px; }
    .stMetric { background-color: #b2dfdb; border-radius: 10px; padding: 10px; box-shadow: 2px 2px 5px #004d40; }
    @media (max-width: 768px) { .stColumns { flex-direction: column; } }
    </style>
""", unsafe_allow_html=True)

# Sidebar cho menu
st.sidebar.title("🎉 Menu")
menu = st.sidebar.radio("Chọn chức năng", ["Nhập/Import Danh sách", "Xem Danh sách"])

if menu == "Nhập/Import Danh sách":
    st.header("📝 Nhập hoặc Import Danh sách Khách mời")
    
    # Nhập thủ công
    st.subheader("Nhập Thủ công")
    with st.form("add_guest_form"):
        name = st.text_input("Tên khách mời")
        position = st.text_input("Chức danh")
        submitted = st.form_submit_button("➕ Thêm Khách mời")
        if submitted and name and position:
            save_guest(name, position)
            st.success(f"Đã thêm {name} ({position})!")
    
    # Import Excel
    st.subheader("Import từ File Excel")
    uploaded_file = st.file_uploader("Upload file Excel (.xlsx) với cột: name, position", type="xlsx")
    if uploaded_file is not None:
        if st.button("📤 Import Excel"):
            import_excel(uploaded_file)
            st.success("Đã import thành công!")

elif menu == "Xem Danh sách":
    st.header("📋 Danh sách Khách mời")
    
    # Load dữ liệu
    df = load_guests()
    
    # Thống kê
    st.subheader("📊 Thống kê")
    total_guests = len(df)
    checked_in_count = df['checked_in'].sum()
    gift_received_count = df['gift_received'].sum()
    checkin_rate = (checked_in_count / total_guests * 100) if total_guests > 0 else 0
    gift_rate = (gift_received_count / total_guests * 100) if total_guests > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng Khách mời", total_guests)
    with col2:
        st.metric("Đã Check-in", f"{checked_in_count} ({checkin_rate:.1f}%)")
    with col3:
        st.metric("Đã Nhận Quà", f"{gift_received_count} ({gift_rate:.1f}%)")
    with col4:
        st.metric("Tỷ lệ Hoàn thành", f"{(checked_in_count + gift_received_count) / (2 * total_guests) * 100:.1f}%" if total_guests > 0 else "0%")
    
    # Tìm kiếm và lọc
    st.subheader("🔍 Tìm kiếm và Lọc")
    search = st.text_input("Tìm kiếm theo tên hoặc chức danh", placeholder="Nhập từ khóa...")
    checkin_filter = st.selectbox("Lọc theo Check-in", ["Tất cả", "Đã check-in", "Chưa check-in"])
    gift_filter = st.selectbox("Lọc theo Nhận quà", ["Tất cả", "Đã nhận quà", "Chưa nhận quà"])
    
    # Áp dụng lọc
    filtered_df = filter_guests(df, search, checkin_filter, gift_filter)
    
    # Export báo cáo
    if not filtered_df.empty:
        csv = filtered_df.to_csv(index=False)
        st.download_button("📥 Export Báo cáo (CSV)", csv, "guests_report.csv", "text/csv", key="download_csv")
    
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    # Hiển thị danh sách đã lọc
    if not filtered_df.empty:
        for index, row in filtered_df.iterrows():
            with st.expander(f"👤 {row['name']} - {row['position']}"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**Checked In:** {'✅ Yes' if row['checked_in'] else '❌ No'}")
                with col2:
                    st.write(f"**Gift Received:** {'🎁 Yes' if row['gift_received'] else '❌ No'}")
                with col3:
                    if not row['checked_in']:
                        if st.button(f"✅ Check In", key=f"checkin_{row['id']}"):
                            update_checkin(row['id'])
                            st.success(f"Đã check-in {row['name']}!")
                            st.rerun()
                with col4:
                    if not row['gift_received']:
                        if st.button(f"🎁 Confirm Gift", key=f"gift_{row['id']}"):
                            update_gift(row['id'])
                            st.success(f"Đã xác nhận quà cho {row['name']}!")
                            st.rerun()
    else:
        st.write("Không tìm thấy khách mời nào phù hợp với bộ lọc.")
    
    # Auto-refresh mỗi 5 giây
    placeholder = st.empty()
    while True:
        time.sleep(5)
        st.rerun()
