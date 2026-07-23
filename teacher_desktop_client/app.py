import os
import sys
import time
import threading
import sqlite3
import requests
import serial
import serial.tools.list_ports
import qrcode
from PIL import Image
import customtkinter as ctk

# Import token generator
from token_generator import generate_dynamic_token

# Configure CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TeacherAttendanceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Proximity Attendance - Instructor Console")
        self.geometry("1000x700")
        
        # Connection Configs
        self.API_BASE_URL = os.getenv("API_BASE_URL", "https://smartattendance-jlal.onrender.com")
        self.serial_port = None
        self.esp32_uid = None
        self.auth_token = None
        
        # Active Schedule Details
        self.schedule_id = None
        self.room_number = "Scanning USB..."
        self.teacher_name = "..."
        self.subject_name = "..."
        self.course_code = "..."
        self.section_name = "..."
        
        # Roster and Live Stats State
        self.roster_students = []       # Active class roster list from DB
        self.present_reg_numbers = set() # Set of checked-in student reg numbers
        
        # Logs state
        self.student_logs = [] # List of strings to display
        self.is_online = True
        self.pending_sync_count = 0
        
        # Thread controller flags
        self.running = True
        
        # Setup Local SQLite cache
        self.init_sqlite_cache()
        
        # Display the login UI first
        self.build_login_ui()
        
    def init_sqlite_cache(self):
        """Initialize SQLite file database for offline queuing"""
        self.db_path = "caching.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_number TEXT NOT NULL,
                schedule_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        self.update_pending_count()

    def update_pending_count(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM cached_logs")
            self.pending_sync_count = cursor.fetchone()[0]
            conn.close()
        except Exception:
            pass

    def build_login_ui(self):
        """Builds a secure staff credentials login screen"""
        self.login_frame = ctk.CTkFrame(self, width=400, height=450, corner_radius=15, fg_color="#0f172a")
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Header
        lbl = ctk.CTkLabel(self.login_frame, text="STAFF VERIFICATION", font=("Outfit", 20, "bold"), text_color="#3b82f6")
        lbl.pack(pady=(35, 10))
        
        lbl_sec = ctk.CTkLabel(self.login_frame, text="Log in to start session for this period", font=("Outfit", 12), text_color="#94a3b8")
        lbl_sec.pack(pady=(0, 25))
        
        # Error Label
        self.err_lbl = ctk.CTkLabel(self.login_frame, text="", font=("Outfit", 12), text_color="#ef4444")
        self.err_lbl.pack(pady=(0, 10))
        
        # Email Input
        self.email_entry = ctk.CTkEntry(self.login_frame, width=280, placeholder_text="Staff Email (e.g. jenkins@college.edu)", font=("Outfit", 13))
        self.email_entry.pack(pady=10)
        
        # Password Input
        self.pass_entry = ctk.CTkEntry(self.login_frame, width=280, placeholder_text="Password", show="*", font=("Outfit", 13))
        self.pass_entry.pack(pady=10)
        
        # Login Button
        self.login_btn = ctk.CTkButton(self.login_frame, width=280, text="Authenticate Console", font=("Outfit", 14, "bold"), command=self.trigger_login_thread)
        self.login_btn.pack(pady=(25, 35))

    def trigger_login_thread(self):
        """Runs authentication in a background thread to prevent GUI freezing"""
        threading.Thread(target=self.handle_login, daemon=True).start()

    def handle_login(self):
        email = self.email_entry.get().strip()
        password = self.pass_entry.get().strip()
        
        if not email or not password:
            self.err_lbl.configure(text="Please fill in all credentials fields.")
            return
            
        self.err_lbl.configure(text="Authenticating...", text_color="#3b82f6")
        self.login_btn.configure(state="disabled")
        
        try:
            res = requests.post(
                f"{self.API_BASE_URL}/api/auth/login", 
                json={"username": email, "password": password},
                timeout=5
            )
            
            if res.status_code == 200:
                data = res.json()
                role = data.get("role")
                
                if role == "admin":
                    self.auth_token = data.get("access_token")
                    self.teacher_name = data.get("name")
                    self.teacher_id = data.get("teacher_id") # Save teacher ID for room swap checks
                    
                    # Destroy login screen and load main dashboard safely on main thread
                    self.after(0, self.complete_login_transition)
                else:
                    self.err_lbl.configure(text="Access Denied: Student logins unauthorized here.", text_color="#ef4444")
                    self.login_btn.configure(state="normal")
            else:
                self.err_lbl.configure(text="Invalid email or password.", text_color="#ef4444")
                self.login_btn.configure(state="normal")
                
        except Exception as e:
            self.err_lbl.configure(text="Connection Error: Is backend server running?", text_color="#ef4444")
            self.login_btn.configure(state="normal")

    def complete_login_transition(self):
        """Safely transitions from login frame to main dashboard on the Tkinter main thread"""
        try:
            if hasattr(self, 'login_frame') and self.login_frame:
                self.login_frame.destroy()
        except Exception:
            pass
            
        self.build_dashboard_ui()
        
        # Start communication loops after successful verification
        threading.Thread(target=self.serial_loop, daemon=True).start()
        threading.Thread(target=self.token_loop, daemon=True).start()
        threading.Thread(target=self.sync_loop, daemon=True).start()

    def build_dashboard_ui(self):
        # Master grid layout
        self.grid_columnconfigure(0, weight=1) # Left details panel
        self.grid_columnconfigure(1, weight=1) # Right QR/Projector panel
        self.grid_rowconfigure(0, weight=1)
        
        # ----------------------------------------------------
        # LEFT PANEL: Metadata & Live Logs
        # ----------------------------------------------------
        left_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#0f172a")
        left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        left_frame.grid_rowconfigure(3, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Title Header
        header_lbl = ctk.CTkLabel(left_frame, text="LECTURE ATTENDANCE CONSOLE", font=("Outfit", 18, "bold"), text_color="#3b82f6")
        header_lbl.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Metadata Block
        self.meta_frame = ctk.CTkFrame(left_frame, fg_color="#131a2a", corner_radius=10)
        self.meta_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        
        self.room_lbl = ctk.CTkLabel(self.meta_frame, text="Room: Connecting ESP32...", font=("Outfit", 15, "bold"))
        self.room_lbl.pack(anchor="w", padx=15, pady=6)
        
        self.subject_lbl = ctk.CTkLabel(self.meta_frame, text="Subject: ...", font=("Outfit", 13))
        self.subject_lbl.pack(anchor="w", padx=15, pady=4)
        
        self.section_lbl = ctk.CTkLabel(self.meta_frame, text="Designated Section: ...", font=("Outfit", 13))
        self.section_lbl.pack(anchor="w", padx=15, pady=4)
        
        self.teacher_lbl = ctk.CTkLabel(self.meta_frame, text="Instructor: ...", font=("Outfit", 13), text_color="#94a3b8")
        self.teacher_lbl.pack(anchor="w", padx=15, pady=6)

        # ----------------------------------------------------
        # LIVE ATTENDANCE STATS CARD (TOTAL, PRESENT, ABSENT)
        # ----------------------------------------------------
        self.stats_frame = ctk.CTkFrame(left_frame, fg_color="#131a2a", corner_radius=10)
        self.stats_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.stats_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # 1. Total Enrolled
        enrolled_box = ctk.CTkFrame(self.stats_frame, fg_color="#1e293b", corner_radius=8)
        enrolled_box.grid(row=0, column=0, padx=6, pady=8, sticky="ew")
        ctk.CTkLabel(enrolled_box, text="TOTAL", font=("Outfit", 10, "bold"), text_color="#94a3b8").pack(pady=(4, 0))
        self.total_lbl = ctk.CTkLabel(enrolled_box, text="0", font=("Outfit", 16, "bold"), text_color="#38bdf8")
        self.total_lbl.pack(pady=(0, 4))

        # 2. Present Count
        present_box = ctk.CTkFrame(self.stats_frame, fg_color="#1e293b", corner_radius=8)
        present_box.grid(row=0, column=1, padx=6, pady=8, sticky="ew")
        ctk.CTkLabel(present_box, text="PRESENT", font=("Outfit", 10, "bold"), text_color="#94a3b8").pack(pady=(4, 0))
        self.present_lbl = ctk.CTkLabel(present_box, text="0", font=("Outfit", 16, "bold"), text_color="#4ade80")
        self.present_lbl.pack(pady=(0, 4))

        # 3. Absent Count
        absent_box = ctk.CTkFrame(self.stats_frame, fg_color="#1e293b", corner_radius=8)
        absent_box.grid(row=0, column=2, padx=6, pady=8, sticky="ew")
        ctk.CTkLabel(absent_box, text="ABSENT", font=("Outfit", 10, "bold"), text_color="#94a3b8").pack(pady=(4, 0))
        self.absent_lbl = ctk.CTkLabel(absent_box, text="0", font=("Outfit", 16, "bold"), text_color="#f87171")
        self.absent_lbl.pack(pady=(0, 4))

        # 4. View Absentees Button
        self.absent_btn = ctk.CTkButton(
            self.stats_frame, 
            text="👥 View Absentees List", 
            font=("Outfit", 12, "bold"), 
            fg_color="#ef4444", 
            hover_color="#dc2626",
            height=30,
            command=self.show_absentees_modal
        )
        self.absent_btn.grid(row=1, column=0, columnspan=3, padx=6, pady=(0, 8), sticky="ew")

        # Sync/Network Status Panel
        self.status_bar = ctk.CTkFrame(left_frame, fg_color="#0f2f22", corner_radius=8, height=30)
        self.status_bar.grid(row=4, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.status_lbl = ctk.CTkLabel(self.status_bar, text="Status: Checking Network...", text_color="#10b981", font=("Outfit", 11, "bold"))
        self.status_lbl.pack(side="left", padx=15, pady=4)
        
        # Checked-In Students Log List
        self.log_textbox = ctk.CTkTextbox(left_frame, fg_color="#090d16", border_color="#1e293b", text_color="#34d399", font=("Courier New", 12))
        self.log_textbox.grid(row=3, column=0, padx=20, pady=(5, 10), sticky="nsew")
        self.log_textbox.insert("0.0", "--- Waiting for student USB CDC streams ---")
        self.log_textbox.configure(state="disabled")
        
        # ----------------------------------------------------
        # RIGHT PANEL: Dynamic Passcode Presentation (Classroom Screen / Projector)
        # ----------------------------------------------------
        right_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#090d16")
        right_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Token Countdown header
        self.timer_lbl = ctk.CTkLabel(right_frame, text="GENERATING PASSCODE...", font=("Outfit", 16, "bold"), text_color="#ef4444")
        self.timer_lbl.pack(pady=(35, 10))
        
        # Center Hero Display for the Passcode
        passcode_card = ctk.CTkFrame(right_frame, fg_color="#131a2a", border_color="#3b82f6", border_width=2, corner_radius=20)
        passcode_card.pack(padx=25, pady=15, fill="both", expand=True)
        
        ctk.CTkLabel(passcode_card, text="DYNAMIC SECURITY PASSCODE", font=("Outfit", 14, "bold"), text_color="#94a3b8").pack(pady=(45, 10))
        
        # Massive, high-visibility 6-digit Passcode
        self.passcode_val_lbl = ctk.CTkLabel(passcode_card, text="000000", font=("Outfit", 56, "bold"), text_color="#38bdf8")
        self.passcode_val_lbl.pack(pady=10)
        
        ctk.CTkLabel(passcode_card, text="⚡ Code shifts automatically every 10 seconds", font=("Outfit", 12), text_color="#64748b").pack(pady=(5, 45))
        
        # Instructions Box (Large & Ultra-Clear for Students in Classroom)
        instruct_card = ctk.CTkFrame(right_frame, fg_color="#131a2a", border_color="#1e293b", border_width=1, corner_radius=15)
        instruct_card.pack(padx=25, pady=(0, 25), fill="x")
        
        ctk.CTkLabel(instruct_card, text="📱 STUDENT CHECK-IN INSTRUCTIONS", font=("Outfit", 15, "bold"), text_color="#38bdf8").pack(pady=(15, 8))
        
        self.step1_lbl = ctk.CTkLabel(
            instruct_card, 
            text="STEP 1: Connect Mobile Wi-Fi to: Classroom AP", 
            font=("Outfit", 14, "bold"), 
            text_color="#f8fafc"
        )
        self.step1_lbl.pack(pady=3)
        
        ctk.CTkLabel(
            instruct_card, 
            text="STEP 2: Open Mobile Browser at  http://192.168.4.1", 
            font=("Outfit", 15, "bold"), 
            text_color="#4ade80"
        ).pack(pady=3)
        
        ctk.CTkLabel(
            instruct_card, 
            text="STEP 3: Enter Reg Number, Password & 6-Digit Passcode Above", 
            font=("Outfit", 13, "bold"), 
            text_color="#cbd5e1"
        ).pack(pady=(3, 18))

    def update_metadata_ui(self):
        """Refreshes schedule details on GUI"""
        self.room_lbl.configure(text=f"Room Station: {self.room_number}")
        self.subject_lbl.configure(text=f"Subject: {self.subject_name} ({self.course_code})")
        self.section_lbl.configure(text=f"Designated Section: {self.section_name}")
        self.teacher_lbl.configure(text=f"Instructor: {self.teacher_name}")
        self.step1_lbl.configure(text=f"STEP 1: Connect Mobile Wi-Fi to: Classroom_{self.room_number}")
        
    def add_log_ui(self, log_msg):
        """Append log to terminal UI box"""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"\n[{time.strftime('%H:%M:%S')}] {log_msg}")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    # ==========================================
    # BACKGROUND SERIAL THREAD
    # ==========================================
    def serial_loop(self):
        """Monitors USB lines to handshake with ESP32 and stream logs"""
        while self.running:
            if not self.serial_port:
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    try:
                        # Attempt connection
                        ser = serial.Serial(p.device, 115200, timeout=1)
                        time.sleep(1.5) # Wait for ESP32 CDC connection to stabilize
                        
                        # Clear any bootloader garbage or AP active messages from buffer
                        ser.reset_input_buffer()
                        
                        # Handshake query
                        ser.write(b"GET_UID\n")
                        
                        # Read lines for up to 1.5 seconds to find the UID response
                        start_time = time.time()
                        uid_found = False
                        while time.time() - start_time < 1.5:
                            if ser.in_waiting > 0:
                                response = ser.readline().decode(errors='ignore').strip()
                                if response.startswith("UID:"):
                                    self.serial_port = ser
                                    self.esp32_uid = response[4:]
                                    self.add_log_ui(f"Connected to ESP32 (UID: {self.esp32_uid}) on {p.device}")
                                    self.resolve_cloud_schedule()
                                    uid_found = True
                                    break
                        
                        if uid_found:
                            break
                        else:
                            ser.close() # Not our target device
                    except Exception as e:
                        pass
                
                if not self.serial_port:
                    self.room_number = "USB ESP32 Missing"
                    self.update_metadata_ui()
                    time.sleep(3) # Wait before rescan
            else:
                # Read check-in stream logs
                try:
                    if self.serial_port.in_waiting > 0:
                        line = self.serial_port.readline().decode().strip()
                        if line.startswith("REG_NUM:"):
                            # Format: "REG_NUM:23BCE040, STATUS:VALID"
                            parts = line.split(",")
                            reg = parts[0].split(":")[1].strip()
                            status = parts[1].split(":")[1].strip()
                            
                            self.add_log_ui(f"VALIDATED: Student {reg} Present")
                            self.present_reg_numbers.add(reg)
                            self.after(0, self.update_stats_ui)
                            self.queue_attendance_log(reg)
                except Exception as e:
                    self.add_log_ui(f"Serial connection disconnected: {e}")
                    self.serial_port = None
                    self.esp32_uid = None
            time.sleep(0.1)

    def resolve_cloud_schedule(self):
        """Calls the central database API to resolve the active timetable slot"""
        try:
            url = f"{self.API_BASE_URL}/api/schedule/resolve?uid={self.esp32_uid}"
            if hasattr(self, 'teacher_id') and self.teacher_id:
                url += f"&teacher_id={self.teacher_id}"
                
            res = requests.get(url, timeout=4)
            if res.status_code == 200:
                data = res.json()
                self.schedule_id = data.get("schedule_id")
                self.room_number = data.get("room_number")
                self.teacher_name = data.get("teacher_name")
                self.subject_name = data.get("subject_name")
                self.course_code = data.get("course_code")
                self.section_name = data.get("section_name")
                
                self.update_metadata_ui()
                self.add_log_ui(f"Timetable matched: {self.subject_name} for Section {self.section_name}")
                
                # Clear previous session locks for the new lecture slot
                if self.serial_port:
                    try:
                        self.serial_port.write(b"RESET_CLASS\n")
                    except Exception:
                        pass
                
                # Auto-sync active roster down to ESP32
                self.sync_roster_to_hardware()
            else:
                self.add_log_ui("Database schedule resolve error: active schedule missing.")
        except Exception as e:
            self.add_log_ui(f"Database network down. Timetable matching offline: {e}")

    def sync_roster_to_hardware(self):
        """Fetches the active student roster for this timetable schedule from the database and syncs it to the ESP32"""
        if not self.schedule_id:
            return
            
        try:
            res = requests.get(f"{self.API_BASE_URL}/api/schedule/{self.schedule_id}/roster", timeout=5)
            
            if res.status_code == 200:
                roster = res.json()
                self.roster_students = roster
                self.present_reg_numbers.clear()
                self.after(0, self.update_stats_ui)
                self.add_log_ui(f"Syncing {len(roster)} student profiles to offline hardware...")
                
                if self.serial_port:
                    try:
                        # Write roster to ESP32 over serial CDC
                        self.serial_port.write(b"ROSTER_START\n")
                        time.sleep(0.3) # Allow ESP32 to open file
                        
                        for student in roster:
                            reg = student.get("reg_number")
                            pwd = student.get("plain_password") or "password123"
                            line = f"{reg},{pwd}\n"
                            self.serial_port.write(line.encode())
                            time.sleep(0.03) # Brief delay to prevent serial buffer overflow
                            
                        self.serial_port.write(b"ROSTER_END\n")
                        self.add_log_ui("Roster successfully uploaded to ESP32!")
                    except Exception as ex:
                        self.add_log_ui(f"Hardware roster sync serial write error: {ex}")
            else:
                self.add_log_ui(f"Roster fetch from server failed ({res.status_code}).")
        except Exception as e:
            self.add_log_ui(f"Failed to sync roster to hardware: {e}")

    def update_stats_ui(self):
        """Updates the Total, Present, and Absent counters on the GUI"""
        total = len(self.roster_students)
        present = len(self.present_reg_numbers)
        absent = max(0, total - present)
        
        self.total_lbl.configure(text=str(total))
        self.present_lbl.configure(text=str(present))
        self.absent_lbl.configure(text=str(absent))

    def show_absentees_modal(self):
        """Opens a modal popup listing all students who are currently absent"""
        absent_students = [s for s in self.roster_students if s.get("reg_number") not in self.present_reg_numbers]
        
        modal = ctk.CTkToplevel(self)
        modal.title("Absent Students List")
        modal.geometry("450x450")
        modal.configure(fg_color="#0f172a")
        modal.attributes("-topmost", True)
        
        # Header
        ctk.CTkLabel(
            modal, 
            text=f"ABSENTEE ROSTER ({len(absent_students)} Students)", 
            font=("Outfit", 16, "bold"), 
            text_color="#ef4444"
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            modal, 
            text=f"Section: {self.section_name} | Subject: {self.subject_name}", 
            font=("Outfit", 12), 
            text_color="#94a3b8"
        ).pack(pady=(0, 15))
        
        # Scrollable list of absentees
        scroll_frame = ctk.CTkScrollableFrame(modal, fg_color="#090d16", border_color="#1e293b", corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        if not absent_students:
            ctk.CTkLabel(scroll_frame, text="🎉 All students are present!", font=("Outfit", 14, "bold"), text_color="#4ade80").pack(pady=40)
        else:
            for idx, student in enumerate(absent_students, 1):
                reg = student.get("reg_number", "N/A")
                name = student.get("name", reg)
                row_frame = ctk.CTkFrame(scroll_frame, fg_color="#1e293b" if idx % 2 == 0 else "#131a2a", corner_radius=6)
                row_frame.pack(fill="x", padx=5, pady=4)
                
                ctk.CTkLabel(row_frame, text=f"{idx}. {reg}", font=("Outfit", 13, "bold"), text_color="#f87171").pack(side="left", padx=12, pady=8)
                ctk.CTkLabel(row_frame, text=name, font=("Outfit", 12), text_color="#e2e8f0").pack(side="right", padx=12, pady=8)

    # ==========================================
    # BACKGROUND TOKEN LOOP
    # ==========================================
    def token_loop(self):
        """Generates shifting OTP codes, sends them to ESP32, and updates screen QR"""
        while self.running:
            if self.serial_port:
                token, remaining = generate_dynamic_token()
                
                # Update Timer title and raw code text
                self.timer_lbl.configure(text=f"PASSCODE SHIFTING IN: {int(remaining)+1}s", text_color="#ef4444")
                self.passcode_val_lbl.configure(text=token)
                
                # Push code down the USB Serial wire
                try:
                    self.serial_port.write(f"TOKEN:{token}\n".encode())
                except Exception:
                    pass
                
                time.sleep(0.5)
            else:
                time.sleep(1)

    # ==========================================
    # ATTENDANCE QUEUE & SYNC
    # ==========================================
    def queue_attendance_log(self, reg_number):
        """Upload log immediately, or cache in local SQLite if offline"""
        timestamp = time.strftime('%Y-%m-%dT%H:%M:%S')
        log_entry = {
            "reg_number": reg_number,
            "schedule_id": self.schedule_id or 1,
            "status": "Present",
            "timestamp": timestamp
        }
        
        # Try uploading instantly
        uploaded = False
        if self.is_online:
            try:
                res = requests.post(f"{self.API_BASE_URL}/api/attendance/submit", json=[log_entry], timeout=3)
                if res.status_code == 200:
                    self.add_log_ui(f"Cloud synced: Student {reg_number}")
                    uploaded = True
            except Exception:
                pass
                
        if not uploaded:
            # Cache locally
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO cached_logs (reg_number, schedule_id, status, timestamp) VALUES (?, ?, ?, ?)",
                    (reg_number, self.schedule_id or 1, "Present", timestamp)
                )
                conn.commit()
                conn.close()
                self.update_pending_count()
                self.add_log_ui(f"Cached offline: Student {reg_number} (Local SQLite)")
            except Exception as e:
                self.add_log_ui(f"SQLite caching failure: {e}")

    def sync_loop(self):
        """Thread monitoring connectivity and uploading cached logs"""
        while self.running:
            # Test connectivity
            try:
                res = requests.get(f"{self.API_BASE_URL}/api/health", timeout=3) # Ping public health check
                self.is_online = (res.status_code == 200) # 200 OK means server is alive and well
            except Exception:
                self.is_online = False
                
            self.update_pending_count()
            
            # Update connection status label
            if self.is_online:
                if self.pending_sync_count > 0:
                    self.status_bar.configure(fg_color="#2d1d07")
                    self.status_lbl.configure(text=f"Status: Online | Syncing {self.pending_sync_count} cached logs...", text_color="#f59e0b")
                    self.sync_cached_logs()
                else:
                    self.status_bar.configure(fg_color="#0f2f22")
                    self.status_lbl.configure(text="Status: Online | Sync completed", text_color="#10b981")
            else:
                self.status_bar.configure(fg_color="#2a0f0f")
                self.status_lbl.configure(text=f"Status: Offline | Caching Active ({self.pending_sync_count} pending)", text_color="#ef4444")
                
            time.sleep(15)

    def sync_cached_logs(self):
        """Reads rows from SQLite, uploads them, and clears database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, reg_number, schedule_id, status, timestamp FROM cached_logs")
            rows = cursor.fetchall()
            
            if not rows:
                conn.close()
                return
                
            payload = []
            row_ids = []
            for r in rows:
                row_ids.append(r[0])
                payload.append({
                    "reg_number": r[1],
                    "schedule_id": r[2],
                    "status": r[3],
                    "timestamp": r[4]
                })
                
            # Submit to API
            res = requests.post(f"{self.API_BASE_URL}/api/attendance/submit", json=payload, timeout=5)
            if res.status_code == 200:
                # Delete rows
                placeholders = ",".join("?" for _ in row_ids)
                cursor.execute(f"DELETE FROM cached_logs WHERE id IN ({placeholders})", row_ids)
                conn.commit()
                self.add_log_ui(f"Sync complete: Uploaded {len(payload)} cached logs to database.")
            conn.close()
            self.update_pending_count()
        except Exception as e:
            self.add_log_ui(f"Cached sync worker error: {e}")

    def destroy(self):
        self.running = False
        if self.serial_port:
            try:
                self.serial_port.close()
            except Exception:
                pass
        super().destroy()

if __name__ == "__main__":
    app = TeacherAttendanceApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.destroy()
