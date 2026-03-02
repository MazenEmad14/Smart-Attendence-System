# 👁️ Smart Attendance System

A modern, highly secure, and real-time Smart Attendance System built with **Python**, **Streamlit**, and **OpenCV**. This project automates the attendance tracking process using advanced computer vision, providing a seamless, glass-morphism UI for both administrators and students.

## 🌟 Key Features

### 🔐 Admin Control Panel
* **Live Dashboard:** View real-time metrics including Total Registered Users, Present Today, and overall System Efficiency.
* **Weekly Analytics:** Interactive bar charts tracking attendance performance over the last 7 days.
* **Live Scanner:** Activate the webcam to detect and log recognized faces instantly. Uses a strict tolerance limit to prevent false positives.
* **System Audit Reports:** Comprehensive logs of all attendance records (Name, ID, Department, Time, Date) stored securely using SQLite.
* **Identity Management:** Visually browse all registered user profiles dynamically loaded from the database.
* **Shift Management:** A dedicated "End Shift / Refresh" functionality to archive current session data without losing historical records.

### 🎓 Student Access Portal
* **Fast Verification:** A streamlined, easy-to-use interface for students to verify their identity via the camera.
* **Visual Feedback:** Instant confirmation card displaying the student's name, exact check-in time, and verification status.

---

## 🛠️ Technology Stack
* **Frontend:** Streamlit, `streamlit-option-menu`, Custom HTML/CSS (Glass-morphism design), FontAwesome Icons
* **Computer Vision:** OpenCV (`cv2`), `face_recognition`
* **Data Processing & Analytics:** Pandas, NumPy
* **Database:** SQLite3
