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
    email TEXT,
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
def save_guest(name, position, email):
    c.execute("INSERT INTO guests (name, position, email) VALUES (?, ?, ?)", (name, position, email))
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

# Hàm import từ CSV
def import_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)
    for _, row in df.iterrows():
        save_guest(row['name'], row['position'], row['email'])

# UI Streamlit
st.title("Quản lý Danh sách Khách mời Sự kiện")

# Phần Import CSV
st.header("Import Danh sách Khách mời")
uploaded_file = st.file_uploader("Upload file CSV (cột: name, position, email)", type="csv")
if uploaded_file is not None:
    if st.button("Import"):
        import_csv(uploaded_file)
        st.success("Đã import thành công!")

# Phần Hiển thị và Quản lý
st.header("Danh sách Khách mời")
if st.button("Refresh Data"):  # Manual refresh
    st.rerun()

# Auto-refresh mỗi 5 giây (simulate near-real-time)
placeholder = st.empty()
while True:
    with placeholder.container():
        df = load_guests()
        if not df.empty:
            for index, row in df.iterrows():
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.write(f"**{row['name']}** ({row['position']}) - {row['email']}")
                with col2:
                    st.write(f"Checked In: {'Yes' if row['checked_in'] else 'No'}")
                with col3:
                    st.write(f"Gift Received: {'Yes' if row['gift_received'] else 'No'}")
                with col4:
                    if not row['checked_in']:
                        if st.button(f"Check In {row['id']}", key=f"checkin_{row['id']}"):
                            update_checkin(row['id'])
                            st.success(f"Đã check-in {row['name']}!")
                            st.rerun()
                with col5:
                    if not row['gift_received']:
                        if st.button(f"Confirm Gift {row['id']}", key=f"gift_{row['id']}"):
                            update_gift(row['id'])
                            st.success(f"Đã xác nhận quà cho {row['name']}!")
                            st.rerun()
        else:
            st.write("Chưa có khách mời nào.")
    time.sleep(5)  # Refresh mỗi 5 giây
    st.rerun()
