# Proximity-Based Student Attendance Automation Platform
### Enterprise IoT System for Campus Attendance Automation

This repository contains the complete workspace codebase, environment scaffolding, and structural implementations for the Proximity-Based Student Attendance system.

---

## 📂 Project Directory Structure

- **`database_layer/`**: Relational database configuration and ORM schema models.
  - `connection.py`: SQLAlchemy engine setup and db session handlers.
  - `models.py`: Optimized normalized tables with scanning indexes.
  - `seed.py`: Python seeding script pre-loaded with mock branches, sections, classrooms, students, and timetable schedules.
- **`unified_web_portal/`**: Dual React frontend + FastAPI backend admin/student cloud dashboard.
  - `backend/`: REST APIs with JWT security, pandas importer, and ReportLab PDF reporting pipe.
  - `frontend/`: Elegant responsive glassmorphic dashboard (Vite + React) displaying SVG analytics graphs and color-coded scorecards.
- **`local_hardware_node/`**: C++ ESP32-S3 IoT firmware files and static web portal.
  - `local_hardware_node.ino`: Arduino firmware hosting an AsyncWebServer and listening on Serial CDC.
  - `data/`: LittleFS memory files including `index.html` (mobile scanner page), `students.txt` (offline manifests), and `html5-qrcode.min.js` (offline scan driver).
- **`teacher_desktop_client/`**: Standalone CustomTkinter Python client.
  - `app.py`: Projector console displaying dynamic QRs, checking CDC USB serial lines, and managing local SQLite fallback caches (`caching.db`).
  - `token_generator.py`: Mathematical OTP module shifting token hashes every 5 seconds.
  - `build_exe.py`: PyInstaller compilation helper.

---

## 🛠️ Step-by-Step Setup Guide

### STEP 1: Set up PostgreSQL Database (pgAdmin 4)

1. Open **pgAdmin 4** on your local machine and connect to your server.
2. Right-click **Databases** -> **Create** -> **Database...**
3. Input the database name: `hardwareattendance` and click **Save**.
4. Create a `.env` file in the root workspace directory `hardwareattendance/` with your PostgreSQL credentials:
   ```env
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/hardwareattendance
   API_BASE_URL=http://localhost:8000
   JWT_SECRET=super_secret_key_proximity_attendance
   ```
   *(Replace `YOUR_PASSWORD` with your actual pgAdmin 4 superuser password).*

---

### STEP 2: Scaffolding the Database & Seeding Mock Data

Open a terminal at the project root and execute:

```powershell
# 1. Navigate to database layer
cd database_layer

# 2. Install database core packages
pip install -r requirements.txt

# 3. Create tables and inject mock data
python seed.py
```
*Verify inside pgAdmin 4 that tables (branches, sections, classrooms, students, teachers, timetable_schedules, attendance_logs) are created and filled under the `hardwareattendance` schema.*

---

### STEP 3: Deploying the Unified Web Portal

#### A. Start the FastAPI Backend
```powershell
cd ../unified_web_portal/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
*API docs will be viewable at http://localhost:8000/docs*

#### B. Start the React Frontend Portal
```powershell
cd ../frontend
npm install
npm run dev
```
*Open http://localhost:3000 in your browser. Log in as **Admin** (`admin@college.edu` / `admin123`) or **Student** (`23BCE040` / `password123`).*

---

### STEP 4: Physical Connection, Wiring & Flashing the ESP32-S3

#### 🔌 How to physically connect the ESP32-S3 Dev Module
ESP32-S3 developer boards usually feature **two USB Type-C ports**:
1. **UART (labeled COM/UART)**: Connected to an onboard USB-to-Serial converter chip (CP210x or CH340).
2. **USB (labeled native USB/CDC)**: Wired directly to the internal ESP32-S3 pins.

- **Flashing**: Connect your computer to the **UART** port using a standard USB data cable.
- **Running the Teacher Client App**: Plug your computer into the **USB/native** port. This establishes native CDC serial communication to receive passcode tokens and stream check-in validation logs.

*Note: If your system does not register the COM port in Windows Device Manager, install the Silicon Labs [CP210x USB to UART Bridge VCP Drivers](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers).*

#### 💻 Flashing via Arduino IDE Workflow
1. Open **Arduino IDE**. Go to **File** -> **Preferences**. Add this URL to "Additional Boards Manager URLs":
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
2. Go to **Tools** -> **Board** -> **Boards Manager...** Search for `esp32` and install version `2.0.x` or `3.0.x`.
3. Select **Tools** -> **Board** -> **ESP32** -> **ESP32S3 Dev Module**.
4. Configure these critical settings under **Tools**:
   - **USB CDC On Boot**: `Enabled` *(CRITICAL: required to map `Serial` to the USB port for the desktop app connection).*
   - **Flash Size**: `8MB` (or matching your board spec).
   - **Partition Scheme**: `8MB with LittleFS` (allocates space for internal flash assets).
5. Go to **Sketch** -> **Include Library** -> **Manage Libraries...** Search and install:
   - `ESPAsyncWebServer` (and its dependency `AsyncTCP`)
6. Open `local_hardware_node.ino` in Arduino IDE.
7. Click **Upload** to compile and flash the firmware.

#### 📁 Uploading LittleFS Static Assets to Flash
To flash the static mobile files (`index.html`, `students.txt`, `html5-qrcode.min.js`) directly inside the ESP32-S3:
1. Download the **Arduino ESP32 LittleFS Filesystem Uploader** plugin or tool for your IDE version.
2. In Arduino IDE, click **Tools** -> **ESP32 LittleFS Data Upload** (or compile/run LittleFS image building tools).
3. The contents of the `local_hardware_node/data/` folder will compile and write directly into the board's internal flash memory.

---

### STEP 5: Running & Packaging the Teacher App Desktop Client

```powershell
cd ../../teacher_desktop_client
pip install -r requirements.txt

# Launch application
python app.py
```

#### 🚀 Auto-detection and Log Streaming Action:
- The desktop app scans for connected devices. When you plug the ESP32-S3's **native USB** port into your laptop, it will automatically connect, handshake (`GET_UID`), and fetch classroom schedule details from the cloud backend.
- A projector-optimized window shows the shifting 5-second QR code passcode.
- Students connect their phones to the ESP32 Wi-Fi AP (`Classroom_302_Attendance`), open `192.168.4.1`, log in, scan the QR, and verify.
- As logs stream up the USB serial line, they list live on screen.
- **Offline Caching**: If the database server connection drops, the app caches records in a local SQLite file (`caching.db`). It automatically synchronizes these records back to PostgreSQL once the connection is restored.

#### 📦 Compiling into a Standalone `.exe`
To package the app for teachers to run with a single click (no Python installation required):
```powershell
python build_exe.py
```
This builds a standalone portable package inside the `dist/InstructorConsole/` folder, ready for distribution.
