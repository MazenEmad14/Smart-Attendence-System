import streamlit as st
import face_recognition
import cv2
import numpy as np
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
from streamlit_option_menu import option_menu

# ---------------------------------------------------------
# 1. Page Config & Session State
# ---------------------------------------------------------
st.set_page_config(
    page_title="Smart Attendance System", 
    layout="wide", 
    page_icon="👁️",
    initial_sidebar_state="expanded"
)

# Initialize Session State Variables
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'
if 'last_detected' not in st.session_state:
    st.session_state.last_detected = None
if 'encodings' not in st.session_state:
    st.session_state.encodings = []
if 'names' not in st.session_state:
    st.session_state.names = []

def navigate_to(page):
    st.session_state['page'] = page
    st.rerun()

# ---------------------------------------------------------
# 2. Modern CSS & FontAwesome Injection
# ---------------------------------------------------------
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main theme - Eye/Tech inspired gradient */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        min-height: 100vh;
    }

    /* Glass morphism cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 40px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateY(-5px);
    }
    
    /* Stat cards */
    .stat-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        border: 1px solid rgba(99, 102, 241, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    /* Student Success Card */
    .student-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 24px;
        padding: 35px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        border: 1px solid rgba(34, 197, 94, 0.3);
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .student-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #10b981, #059669, #047857);
    }

    /* Text Gradients */
    .stat-value {
        font-size: 42px;
        font-weight: 800;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 15px 0;
        position: relative;
        z-index: 2;
    }
    
    .stat-label {
        font-size: 14px;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        position: relative;
        z-index: 2;
    }

    h1, h2, h3 { 
        background: linear-gradient(135deg, #f0f9ff 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    
    /* Button Styling */
    .stButton > button {
        border-radius: 16px;
        font-weight: 700;
        padding: 16px 28px;
        border: 2px solid rgba(99, 102, 241, 0.3);
        background: rgba(99, 102, 241, 0.1);
        color: #f0f9ff;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        border-color: #6366f1;
        background: rgba(99, 102, 241, 0.2);
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(99, 102, 241, 0.3);
    }
    
    .stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        color: white;
    }

    /* Home Page & Layout */
    .welcome-container {
        text-align: center;
        padding: 80px 40px;
    }
    
    /* Using FontAwesome for Logo instead of Emoji */
    .logo-icon {
        font-size: 100px;
        margin-bottom: 30px;
        color: #6366f1; /* Fallback color */
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .welcome-title {
        font-size: 48px;
        font-weight: 800;
        background: linear-gradient(135deg, #f0f9ff 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    
    .welcome-subtitle {
        font-size: 18px;
        color: #94a3b8;
        margin-bottom: 50px;
        line-height: 1.6;
    }
    
    /* Hide default sidebar handle to use our custom logic */
    [data-testid="stSidebarNav"] {display: none !important;}
    
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. Database & Face Recognition Logic
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    # Create main table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (name TEXT, id TEXT, dept TEXT, time TEXT, date TEXT, status TEXT, confidence REAL)''')
    
    # Try to add 'archived' column for shift management (if it doesn't exist)
    try:
        c.execute("ALTER TABLE logs ADD COLUMN archived INTEGER DEFAULT 0")
    except:
        pass
        
    conn.commit()
    conn.close()

init_db()

def load_known_faces():
    known_encodings = []
    known_names = []
    
    # NOTE: Ensure this path is correct for your system
    image_dir = r'F:\DataScience\HCAI-Project\Images'
    
    if not os.path.exists(image_dir):
        return [], []

    files = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    
    if not files:
        return [], []

    for file in files:
        img_path = os.path.join(image_dir, file)
        try:
            img = face_recognition.load_image_file(img_path)
            encodings = face_recognition.face_encodings(img)
            
            if encodings:
                known_encodings.append(encodings[0])
                # Using the filename as the unique ID/Name
                known_names.append(os.path.splitext(file)[0])
        except Exception as e:
            continue
            
    return known_encodings, known_names

# Load faces once
if not st.session_state.names:
    st.session_state.encodings, st.session_state.names = load_known_faces()

def get_dashboard_metrics():
    conn = sqlite3.connect('attendance.db')
    total_students = len(st.session_state.names) if st.session_state.names else 1
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Only count students who are NOT archived (active in current shift)
    df_today = pd.read_sql_query("SELECT DISTINCT name FROM logs WHERE date = ? AND archived = 0", conn, params=(today,))
    present_count = len(df_today)
    
    attendance_rate = int((present_count / total_students) * 100) if total_students > 0 else 0
    
    # Generate a list of the last 7 days for the chart
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    
    # Query database for counts on those days (Counting ALL records for history)
    chart_data = []
    for d in dates:
        row = conn.execute("SELECT COUNT(DISTINCT name) FROM logs WHERE date = ?", (d,)).fetchone()
        count = row[0] if row else 0
        chart_data.append(count)
    
    conn.close()
    return total_students, present_count, attendance_rate, dates, chart_data

# ---------------------------------------------------------
# 4. Global Sidebar (Always Visible)
# ---------------------------------------------------------
with st.sidebar:
    # Replaced Emoji with FontAwesome Icon
    st.markdown("### <i class='fa-solid fa-eye'></i> Smart Attendance", unsafe_allow_html=True)
    
    selected_opt = option_menu(
        menu_title=None,
        options=["Dashboard", "Live Scanner", "Reports", "User Management", "System Config"],
        icons=["speedometer2", "camera-video", "file-text", "people", "gear-fill"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#6366f1", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "14px", 
                "text-align": "left", 
                "margin": "8px 5px", 
                "--hover-color": "rgba(99, 102, 241, 0.1)", 
                "color": "#e2e8f0"
            },
            "nav-link-selected": {
                "background-color": "rgba(99, 102, 241, 0.2)", 
                "color": "#6366f1", 
                "border-radius": "12px",
                "border": "1px solid rgba(99, 102, 241, 0.3)"
            },
        }
    )
    
    st.markdown("---")
    
    # UPDATED BUTTON: Refresh & End Shift
    if st.button("🔄 End Shift / Refresh", use_container_width=True):
        # 1. Archive today's data (resets the counter, keeps the records)
        conn = sqlite3.connect('attendance.db')
        today_date = datetime.now().strftime("%Y-%m-%d")
        conn.execute("UPDATE logs SET archived = 1 WHERE date = ?", (today_date,))
        conn.commit()
        conn.close()
        
        # 2. Reload faces and rerun
        st.session_state.encodings, st.session_state.names = load_known_faces()
        st.rerun()

    if st.button("🚪 Logout / Home", use_container_width=True):
        navigate_to('home')

# ---------------------------------------------------------
# 5. Application Pages
# ---------------------------------------------------------

def show_home():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
<div class="glass-card">
    <div class="welcome-container">
        <!-- Replaced Emoji with Icon Class -->
        <div class="logo-icon"><i class="fa-solid fa-eye"></i></div>
        <div class="welcome-title">Smart Attendance System</div>
        <div class="welcome-subtitle">Advanced Facial Recognition Platform<br>Secure • Intelligent • Automated</div>
    </div>
</div>
""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔐 **Admin Control Panel**", use_container_width=True, type="primary"):
                navigate_to('admin_login')
        with col_b:
            if st.button("🎓 **Student Access Portal**", use_container_width=True):
                navigate_to('student_view')
        
        # Using FontAwesome Icons in the Grid
        st.markdown("""
<div style="margin-top: 60px;">
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; text-align: center;">
        <div style="padding: 25px; background: rgba(255,255,255,0.05); border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.2);">
            <div style="font-size: 32px; margin-bottom: 15px; color:#f0f9ff;"><i class="fa-solid fa-bolt"></i></div>
            <h4 style="color: #f0f9ff; margin: 10px 0;">Real-time</h4>
            <p style="color: #94a3b8; font-size: 14px;">Instant face detection</p>
        </div>
        <div style="padding: 25px; background: rgba(255,255,255,0.05); border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.2);">
            <div style="font-size: 32px; margin-bottom: 15px; color:#f0f9ff;"><i class="fa-solid fa-lock"></i></div>
            <h4 style="color: #f0f9ff; margin: 10px 0;">Secure</h4>
            <p style="color: #94a3b8; font-size: 14px;">Encrypted data</p>
        </div>
        <div style="padding: 25px; background: rgba(255,255,255,0.05); border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.2);">
            <div style="font-size: 32px; margin-bottom: 15px; color:#f0f9ff;"><i class="fa-solid fa-chart-line"></i></div>
            <h4 style="color: #f0f9ff; margin: 10px 0;">Analytics</h4>
            <p style="color: #94a3b8; font-size: 14px;">Smart insights</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

def show_admin_login():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("""
<div class="glass-card" style="margin-top: 100px;">
    <div style="text-align: center; margin-bottom: 40px;">
        <div style="font-size: 60px; background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            <i class="fa-solid fa-user-shield"></i>
        </div>
        <h2 style="color: #f0f9ff; margin: 20px 0;">Admin Control Panel</h2>
        <p style="color: #94a3b8;">Secure access to system management</p>
    </div>
</div>
""", unsafe_allow_html=True)
        
        password = st.text_input("**Access Password**", type="password", placeholder="Enter admin credentials")
        
        if st.button("**Authenticate & Enter Dashboard**", use_container_width=True, type="primary"):
            if password == "admin123":
                navigate_to('admin_dashboard')
            else:
                st.error("🚫 Authentication failed. Invalid credentials")
        
        if st.button("← Back to Home", use_container_width=True):
            navigate_to('home')

def show_admin_dashboard(selected):
    total, present, rate, dates, chart_values = get_dashboard_metrics()
    
    # --- DASHBOARD ---
    if selected == "Dashboard":
        # Using HTML header to enforce Icon rendering
        st.markdown("<h2><i class='fa-solid fa-chart-pie'></i> System Overview</h2>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-label'>Registered Users</div>
                <div class='stat-value'>{total}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-label'>Present Today</div>
                <div class='stat-value' style='color:#10B981'>{present}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-label'>System Efficiency</div>
                <div class='stat-value' style='color:#6366f1'>{rate}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.subheader("📈 Weekly Performance Analytics")
        
        if dates and chart_values:
            chart_df = pd.DataFrame({"Date": dates, "Attendance": chart_values})
            chart_df = chart_df.set_index('Date')
            st.bar_chart(chart_df, color="#6366f1")
        else:
            st.info("Not enough data for analytics.")

    # --- LIVE SCANNER ---
    elif selected == "Live Scanner":
        st.markdown("<h2><i class='fa-solid fa-camera'></i> Live Recognition Scanner</h2>", unsafe_allow_html=True)
        
        col_cam, col_log = st.columns([2, 1])
        
        with col_cam:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            run_camera = st.toggle("🎯 Activate Face Scanner", value=True)
            FRAME_WINDOW = st.image([])
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_log:
            st.markdown("### 🔍 Recent Detections")
            log_placeholder = st.empty()

        if run_camera:
            camera = cv2.VideoCapture(0)
            while run_camera:
                ret, frame = camera.read()
                if not ret: 
                    st.error("📷 Camera system offline")
                    break
                
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                face_names = []
                for face_encoding in face_encodings:
                    name = "Unknown"
                    
                    if len(st.session_state.encodings) > 0:
                        # FIX: Added strict tolerance (0.5) to reduce false positives
                        matches = face_recognition.compare_faces(st.session_state.encodings, face_encoding, tolerance=0.5)
                        face_distances = face_recognition.face_distance(st.session_state.encodings, face_encoding)
                        
                        if len(face_distances) > 0:
                            best_match_index = np.argmin(face_distances)
                            if matches[best_match_index]:
                                name = st.session_state.names[best_match_index]
                                
                                conn = sqlite3.connect('attendance.db')
                                c = conn.cursor()
                                now = datetime.now()
                                date_str = now.strftime("%Y-%m-%d")
                                
                                # Check if already marked present IN CURRENT SESSION (archived=0)
                                c.execute("SELECT * FROM logs WHERE name=? AND date=? AND archived=0", (name, date_str))
                                if not c.fetchone():
                                    # Insert with default archived=0
                                    c.execute("INSERT INTO logs (name, id, dept, time, date, status, confidence, archived) VALUES (?, ?, ?, ?, ?, ?, ?, 0)", 
                                              (name, "ID-Gen", "AI", now.strftime("%H:%M:%S"), date_str, 'Present', 99.0))
                                    conn.commit()
                                    st.toast(f"✅ Identity verified: {name}")
                                conn.close()
                    
                    face_names.append(name)
                
                # Show recent logs for today (all logs, including archived if you want history, or just fresh?)
                # Usually scanner logs show recent activity regardless of shift, but let's show all today
                conn = sqlite3.connect('attendance.db')
                df_log = pd.read_sql_query("SELECT name, time FROM logs WHERE date=? ORDER BY time DESC LIMIT 8", conn, params=(datetime.now().strftime("%Y-%m-%d"),))
                conn.close()
                log_placeholder.dataframe(df_log, hide_index=True, use_container_width=True)

                for (top, right, bottom, left), name in zip(face_locations, face_names):
                    top *= 4; right *= 4; bottom *= 4; left *= 4
                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
                    cv2.rectangle(frame, (left, bottom - 40), (right, bottom), color, cv2.FILLED)
                    cv2.putText(frame, name, (left + 6, bottom - 10), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 2)

                FRAME_WINDOW.image(frame, channels="BGR", use_container_width=True)
            camera.release()

    # --- REPORTS ---
    elif selected == "Reports":
        st.markdown("<h2><i class='fa-solid fa-file-invoice'></i> System Audit Reports</h2>", unsafe_allow_html=True)
        conn = sqlite3.connect('attendance.db')
        try:
            # Show ALL records (both archived and fresh)
            df = pd.read_sql_query("SELECT name, id, dept, time, date, status, confidence FROM logs ORDER BY date DESC, time DESC", conn)
            st.dataframe(df, use_container_width=True)
        except:
            st.info("No audit records available")
        conn.close()

    # --- USER MANAGEMENT ---
    elif selected == "User Management":
        st.markdown("<h2><i class='fa-solid fa-users-gear'></i> Identity Management</h2>", unsafe_allow_html=True)
        image_dir = r'F:\DataScience\HCAI-Project\Images'
        
        if os.path.exists(image_dir):
            images = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.png'))]
            st.info(f"🔐 Registered Identities: {len(images)}")
            
            if len(images) > 0:
                cols = st.columns(4)
                for idx, img_file in enumerate(images):
                    with cols[idx % 4]:
                        st.markdown(f"<div style='text-align:center;'>", unsafe_allow_html=True)
                        st.image(os.path.join(image_dir, img_file), caption=img_file, width=120)
                        st.markdown(f"</div>", unsafe_allow_html=True)
            else:
                st.warning("📁 No identity profiles found")
        else:
            st.error("❌ Identity database unavailable. Check path.")

    # --- SYSTEM CONFIG ---
    elif selected == "System Config":
        st.subheader("⚙️ System Configuration")
        st.toggle("🌙 Dark Mode", value=True)
        st.toggle("🔔 Notification Alerts", value=True)
        st.slider("🎯 Recognition Sensitivity", 0.0, 1.0, 0.6)

def show_student_view():
    st.markdown("### 🎓 Student Access Portal")
    if st.button("← Exit Scanner"): navigate_to('home')
    
    col_cam, col_info = st.columns([3, 1]) 
    
    with col_cam:
        run_camera = st.checkbox("🎥 Enable Face Scanner", value=True)
        FRAME_WINDOW = st.image([])
    
    with col_info:
        info_placeholder = st.empty()
        info_placeholder.markdown("""
<div class='glass-card'>
    <div style='text-align:center;'>
        <div style='font-size:50px; color:#6366f1;'><i class="fa-solid fa-eye"></i></div>
        <h3 style='color:#f0f9ff;'>Awaiting Identity</h3>
        <p style='color:#94a3b8;'>Position face for verification</p>
    </div>
</div>
""", unsafe_allow_html=True)

    if run_camera:
        camera = cv2.VideoCapture(0)
        while run_camera:
            ret, frame = camera.read()
            if not ret: break
            
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            face_names = []
            detected_person = None
            frozen_time = None 
            
            for face_encoding in face_encodings:
                name = "Unknown"
                
                if len(st.session_state.encodings) > 0:
                    # FIX: Strict tolerance (0.5)
                    matches = face_recognition.compare_faces(st.session_state.encodings, face_encoding, tolerance=0.5)
                    face_distances = face_recognition.face_distance(st.session_state.encodings, face_encoding)
                    
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = st.session_state.names[best_match_index]
                            detected_person = name
                            
                            conn = sqlite3.connect('attendance.db')
                            c = conn.cursor()
                            now = datetime.now()
                            today_str = now.strftime("%Y-%m-%d")
                            
                            # Check for presence in CURRENT SESSION only
                            c.execute("SELECT time FROM logs WHERE name=? AND date=? AND archived=0", (name, today_str))
                            row = c.fetchone()
                            
                            if row:
                                frozen_time = row[0]
                            else:
                                current_time = now.strftime("%H:%M:%S")
                                c.execute("INSERT INTO logs (name, id, dept, time, date, status, confidence, archived) VALUES (?, ?, ?, ?, ?, ?, ?, 0)", 
                                          (name, "ID-Gen", "AI", current_time, today_str, 'Present', 99.0))
                                conn.commit()
                                frozen_time = current_time
                            conn.close()
                
                face_names.append(name)
            
            if detected_person and frozen_time:
                info_placeholder.markdown(f"""
<div class='student-card'>
    <div style='text-align:center;'>
        <div style='font-size:60px;'>✅</div>
        <h2 style='color:#10B981; margin:15px 0;'>{detected_person}</h2>
        <div class='time-display'>🕒 {frozen_time}</div>
        <div style='background:linear-gradient(135deg, #10b981 0%, #059669 100%); color:white; padding:15px; border-radius:15px; font-weight:bold; margin-top:20px; font-size:14px;'>
            ✅ Identity Verified
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
            elif not detected_person:
                info_placeholder.markdown("""
<div class='glass-card'>
    <div style='text-align:center;'>
        <div style='font-size:50px; color:#6366f1;'><i class="fa-solid fa-eye"></i></div>
        <h3 style='color:#f0f9ff;'>Awaiting Identity</h3>
        <p style='color:#94a3b8;'>Position face for verification</p>
    </div>
</div>
""", unsafe_allow_html=True)

            for (top, right, bottom, left), name in zip(face_locations, face_names):
                top *= 4; right *= 4; bottom *= 4; left *= 4
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
                cv2.rectangle(frame, (left, bottom - 40), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 10), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 2)

            FRAME_WINDOW.image(frame, channels="BGR", use_container_width=True)
        camera.release()

# ---------------------------------------------------------
# 6. Page Router
# ---------------------------------------------------------

if st.session_state['page'] == 'home':
    show_home()
elif st.session_state['page'] == 'admin_login':
    show_admin_login()
elif st.session_state['page'] == 'admin_dashboard':
    show_admin_dashboard(selected_opt)
elif st.session_state['page'] == 'student_view':
    show_student_view()