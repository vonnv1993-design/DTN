import streamlit as st
import pandas as pd
import sqlite3
import time
from datetime import datetime
from io import BytesIO
from openpyxl.styles import Font

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

# Hàm reset check-in (undo)
def reset_checkin(guest_id):
    c.execute("UPDATE guests SET checked_in = 0, check_in_time = NULL WHERE id = ?", (guest_id,))
    conn.commit()

# Hàm reset gift received (undo)
def reset_gift(guest_id):
    c.execute("UPDATE guests SET gift_received = 0, gift_confirm_time = NULL WHERE id = ?", (guest_id,))
    conn.commit()

# Hàm import từ Excel (hỗ trợ .xls và .xlsx)
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

# Hàm tạo XLS cho export với font Times New Roman
def create_export_xls(filtered_df):
    export_df = pd.DataFrame({
        'STT': range(1, len(filtered_df) + 1),
        'Tên': filtered_df['name'],
        'Vị trí': filtered_df['position'],
        'Đã check in': filtered_df['checked_in'].map({1: 'Yes', 0: 'No'}),
        'Đã nhận quà': filtered_df['gift_received'].map({1: 'Yes', 0: 'No'}),
        'Thời gian check in': filtered_df['check_in_time'].fillna(''),
        'Thời gian nhận quà': filtered_df['gift_confirm_time'].fillna('')
    })
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, sheet_name='Guests', index=False)
        # Set font Times New Roman cho toàn bộ sheet
        workbook = writer.book
        sheet = workbook['Guests']
        times_new_roman = Font(name='Times New Roman')
        for row in sheet.iter_rows():
            for cell in row:
                cell.font = times_new_roman
    buffer.seek(0)
    return buffer

# UI Streamlit với sidebar
st.set_page_config(page_title="Quản lý Khách mời", page_icon="✈️", layout="wide")

# CSS cho theme Vietnam Airlines (xanh và vàng đồng), trẻ trung, fix màu chữ sidebar và tiêu đề
st.markdown("""
    <style>
    body { background: linear-gradient(135deg, #003366 0%, #FFD700 100%); color: white; font-family: Arial, sans-serif; }
    .stButton>button { background: linear-gradient(45deg, #FFD700, #FFA500); color: #003366; border-radius: 15px; border: 3px solid #003366; box-shadow: 4px 4px 10px rgba(0,0,0,0.3); width: 100%; height: 50px; font-size: 18px; font-weight: bold; transition: transform 0.2s; }
    .stButton>button:hover { transform: scale(1.05); }
    .stTextInput, .stSelectbox, .stFileUploader { border-radius: 15px; border: 3px solid #FFD700; padding: 10px; background-color: rgba(255,255,255,0.9); color: #003366; }
    .stExpander { border: 3px solid #FFD700; border-radius: 15px; box-shadow: 4px 4px 10px rgba(0,0,0,0.3); margin-bottom: 15px; background-color: rgba(255,255,255,0.1); }
    .stMetric { background: linear-gradient(45deg, #FFD700, #FFA500); border-radius: 15px; padding: 15px; box-shadow: 4px 4px 10px rgba(0,0,0,0.3); color: #003366; font-weight: bold; }
    .stSidebar { background-color: #DEA600; color: white; }
    .stRadio label { color: white !important; }
    .stHeader, .stSubheader, h1, h2 { color: white !important; }  /* Fix màu tiêu đề trắng */
    @media (max-width: 768px) { .stColumns { flex-direction: column; } }
    </style>
""", unsafe_allow_html=True)

# Sidebar cho menu
st.sidebar.title("✈️ Menu")
menu = st.sidebar.radio("Chọn chức năng", ["Nhập/Import Danh sách", "Xem Danh sách"])

if menu == "Nhập/Import Danh sách":
    st.header("📝 Nhập/Import Danh sách")
    
    # Nhập thủ công
    st.subheader("Nhập Thủ công")
    with st.form("add_guest_form"):
        name = st.text_input("Tên khách mời")
        position = st.text_input("Chức danh")
        submitted = st.form_submit_button("➕ Thêm Khách mời")
        if submitted and name and position:
            save_guest(name, position)
            st.success(f"Đã thêm {name} ({position})!")
    
    # Import Excel (hỗ trợ .xls và .xlsx)
    st.subheader("Import từ File Excel")
    uploaded_file = st.file_uploader("Upload file Excel (.xls hoặc .xlsx) với cột: name, position", type=["xls", "xlsx"])
    if uploaded_file is not None:
        if st.button("📤 Import Excel"):
            import_excel(uploaded_file)
            st.success("Đã import thành công!")

elif menu == "Xem Danh sách":
    st.header("📋 Xem Danh sách")
    
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
    
    # Tìm kiếm và lọc với form submit
    st.subheader("🔍 Tìm kiếm và Lọc")
    with st.form("filter_form"):
        search = st.text_input("Tìm kiếm theo tên hoặc chức danh", placeholder="Nhập từ khóa...")
        checkin_filter = st.selectbox("Lọc theo Check-in", ["Tất cả", "Đã check-in", "Chưa check-in"])
        gift_filter = st.selectbox("Lọc theo Nhận quà", ["Tất cả", "Đã nhận quà", "Chưa nhận quà"])
        submitted = st.form_submit_button("🔍 Áp dụng Tìm kiếm và Lọc")
    
    # Áp dụng lọc chỉ khi submit
    if submitted:
        filtered_df = filter_guests(df, search, checkin_filter, gift_filter)
        st.session_state['filtered_df'] = filtered_df  # Lưu vào session để giữ sau refresh
    else:
        filtered_df = st.session_state.get('filtered_df', df)  # Sử dụng dữ liệu đã lọc trước đó nếu có
    
    # Export báo cáo (chỉ XLS)
    if not filtered_df.empty:
        xls_buffer = create_export_xls(filtered_df)
        st.download_button("📥 Export Báo cáo (XLS)", xls_buffer, "guests_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="download_xls")
        
        st.info("💡 File XLS đã được export với font Times New Roman và hỗ trợ tiếng Việt hoàn toàn.")
    
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
                    else:
                        if st.button(f"🔄 Undo Check-in", key=f"undo_checkin_{row['id']}"):
                            reset_checkin(row['id'])
                            st.warning(f"Đã undo check-in cho {row['name']}!")
                            st.rerun()
                with col4:
                    if not row['gift_received']:
                        if st.button(f"🎁 Confirm Gift", key=f"gift_{row['id']}"):
                            update_gift(row['id'])
                            st.success(f"Đã xác nhận quà cho {row['name']}!")
                            st.rerun()
                    else:
                        if st.button(f"🔄 Undo Gift", key=f"undo_gift_{row['id']}"):
                            reset_gift(row['id'])
                            st.warning(f"Đã undo nhận quà cho {row['name']}!")
                            st.rerun()
    else:
        st.write("Không tìm thấy khách mời nào phù hợp với bộ lọc.")
    
    # Auto-refresh mỗi 5 giây
    placeholder = st.empty()
    while True:
        time.sleep(5)
        st.rerun()
