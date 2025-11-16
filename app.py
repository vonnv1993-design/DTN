import streamlit as st
import pandas as pd
import sqlite3
import time
from datetime import datetime

# Kết nối SQLite
conn = sqlite3.connect('guests.db')
c = conn.cursor()

# Tạo bảng nếu chưa có (chỉ lưu name và position)
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
    df = pd.read_excel(uploaded_file, usecols=['name', 'position'])  # Chỉ lấy 2 cột
    for _, row in df.iterrows():
        save_guest(row['name'], row['position'])

# UI Streamlit với sidebar
st.set_page_config(page_title="Quản lý Khách mời", page_icon="🎉", layout="wide")  # Responsive layout

# Sidebar cho menu
st.sidebar.title("🎉 Menu")
menu = st.sidebar.radio("Chọn chức năng", ["Nhập/Import Danh sách", "Xem Danh sách"])

# Thêm CSS cơ bản cho mobile-friendly (responsive)
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 50px; font-size: 18px; }
    .stTextInput, .stFileUploader { font-size: 16px; }
    @media (max-width: 768px) { .stColumns { flex-direction: column; } }
    </style>
""", unsafe_allow_html=True)

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
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    # Auto-refresh mỗi 5 giây
    placeholder = st.empty()
    while True:
        with placeholder.container():
            df = load_guests()
            if not df.empty:
                for index, row in df.iterrows():
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
                st.write("Chưa có khách mời nào. Hãy nhập hoặc import danh sách!")
        time.sleep(5)  # Refresh mỗi 5 giây
        st.rerun()
