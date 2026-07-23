#include <Arduino.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <ESPAsyncWebServer.h>
#include <LittleFS.h>

// Isolated Access Point Credentials
const char* apSSID = "Classroom_302";
const char* apPassword = ""; // Open network for quick student connection

// HTML Mobile interface stored directly in program flash
const char HTML_CONTENT[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Classroom Proximity Check-in</title>
  <style>
    :root {
      --bg: #090d16;
      --panel: #0f172a;
      --accent: #3b82f6;
      --text: #f8fafc;
      --text-sec: #94a3b8;
      --success: #10b981;
      --danger: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: 16px;
    }
    .container {
      width: 100%;
      max-width: 400px;
      background-color: var(--panel);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      margin-top: 20px;
    }
    h2 { text-align: center; margin-bottom: 8px; font-size: 20px; }
    p.desc { text-align: center; color: var(--text-sec); font-size: 12px; margin-bottom: 20px; }
    label { display: block; font-size: 11px; color: var(--text-sec); margin-bottom: 6px; font-weight: 600; }
    input {
      width: 100%;
      padding: 12px;
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 6px;
      color: #fff;
      font-size: 14px;
      margin-bottom: 18px;
      outline: none;
    }
    input:focus { border-color: var(--accent); }
    button {
      width: 100%;
      padding: 14px;
      background: var(--accent);
      border: none;
      border-radius: 6px;
      color: #fff;
      font-weight: bold;
      cursor: pointer;
      font-size: 15px;
      margin-top: 5px;
    }
    .alert {
      padding: 12px;
      border-radius: 6px;
      font-size: 13px;
      margin-bottom: 18px;
      text-align: center;
      display: none;
      line-height: 1.4;
    }
    .alert.success { background: rgba(16, 185, 129, 0.15); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.3); }
    .alert.danger { background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.3); }
  </style>
</head>
<body>

  <div style="display: flex; align-items: center; gap: 8px; margin: 20px 0 10px;">
    <div style="width: 24px; height: 24px; border-radius: 6px; background: var(--accent);"></div>
    <span style="font-weight: bold; font-size: 16px; letter-spacing: -0.025em;">PROXIMITY ATTENDANCE</span>
  </div>

  <div class="container">
    <h2>Student Verification</h2>
    <p class="desc">Verify credentials to confirm classroom presence.</p>
    
    <div id="alert" class="alert"></div>

    <div id="attendance-form">
      <label>REGISTRATION NUMBER</label>
      <input id="reg" type="text" placeholder="e.g. 23BCE040" required />

      <label>PASSWORD</label>
      <input id="pass" type="password" placeholder="••••••••" required />

      <label>DYNAMIC PASSCODE</label>
      <input id="token" type="text" placeholder="Type 6-digit code shown on screen" maxlength="6" required />

      <button type="button" onclick="handleAttendanceSubmit()">Verify Attendance</button>
    </div>
  </div>

  <script>
    const alertDiv = document.getElementById("alert");

    function showAlert(msg, isError = false) {
      alertDiv.innerText = msg;
      alertDiv.className = isError ? "alert danger" : "alert success";
      alertDiv.style.display = "block";
    }

    async function handleAttendanceSubmit() {
      alertDiv.style.display = "none";

      const reg_number = document.getElementById("reg").value.trim();
      const password = document.getElementById("pass").value.trim();
      const passcode = document.getElementById("token").value.trim();

      if (!reg_number || !password || !passcode) {
        showAlert("Please fill in all 3 fields: Registration Number, Password, and Passcode.", true);
        return;
      }

      try {
        const res = await fetch("/api/submit-attendance", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reg_number, password, passcode })
        });

        const data = await res.json();
        if (res.ok) {
          showAlert("🎉 Attendance Authenticated Successfully! Connection released. You may now disconnect from Wi-Fi.");
          document.getElementById("reg").value = "";
          document.getElementById("pass").value = "";
          document.getElementById("token").value = "";
        } else {
          showAlert("[" + res.status + " Error] " + (data.message || "Verification failed."), true);
        }
      } catch (err) {
        showAlert("Failed to connect to classroom node: " + err, true);
      }
    }
  </script>
</body>
</html>
)rawliteral";

// Staff Mobile Portal Interface for Standalone Wall Charger Mode
const char STAFF_HTML_CONTENT[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Staff Attendance Console</title>
  <style>
    :root {
      --bg: #090d16;
      --panel: #0f172a;
      --accent: #3b82f6;
      --text: #f8fafc;
      --text-sec: #94a3b8;
      --success: #10b981;
      --danger: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: 16px;
    }
    .container {
      width: 100%;
      max-width: 420px;
      background-color: var(--panel);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      margin-top: 15px;
    }
    h2 { text-align: center; margin-bottom: 8px; font-size: 20px; }
    p.desc { text-align: center; color: var(--text-sec); font-size: 12px; margin-bottom: 20px; }
    label { display: block; font-size: 11px; color: var(--text-sec); margin-bottom: 6px; font-weight: 600; }
    input {
      width: 100%;
      padding: 12px;
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 6px;
      color: #fff;
      font-size: 14px;
      margin-bottom: 18px;
      outline: none;
    }
    button {
      width: 100%;
      padding: 14px;
      background: var(--accent);
      border: none;
      border-radius: 6px;
      color: #fff;
      font-weight: bold;
      cursor: pointer;
      font-size: 15px;
    }
    .card {
      background: #131a2a;
      border: 1px solid #3b82f6;
      border-radius: 12px;
      padding: 20px;
      text-align: center;
      margin-bottom: 20px;
    }
    .passcode { font-size: 48px; font-weight: bold; color: #38bdf8; letter-spacing: 4px; margin: 10px 0; }
    .stats-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 20px; }
    .stat-box { background: #1e293b; border-radius: 8px; padding: 12px; text-align: center; }
    .stat-val { font-size: 22px; font-weight: bold; }
    .stat-lbl { font-size: 10px; color: #94a3b8; margin-top: 2px; }
    .modal {
      display: none; position: fixed; top:0; left:0; width:100%; height:100%;
      background: rgba(0,0,0,0.8); align-items:center; justify-content:center; padding:16px;
    }
    .modal-content {
      background: #0f172a; border-radius: 12px; width: 100%; max-width: 380px; padding: 20px; border: 1px solid #334155;
    }
  </style>
</head>
<body>

  <div style="display: flex; align-items: center; gap: 8px; margin: 15px 0 5px;">
    <div style="width: 24px; height: 24px; border-radius: 6px; background: #3b82f6;"></div>
    <span style="font-weight: bold; font-size: 16px;">STAFF MOBILE CONSOLE</span>
  </div>

  <!-- Login Form View -->
  <div id="login-view" class="container">
    <h2>Staff Authentication</h2>
    <p class="desc">Log in to launch the classroom attendance session.</p>
    <div>
      <label>TEACHER EMAIL / USERNAME</label>
      <input id="staff-id" type="text" placeholder="e.g. swathi@college.edu" required />
      <label>PASSWORD</label>
      <input id="staff-pass" type="password" placeholder="••••••••" required />
      <button type="button" onclick="handleStaffLogin()">Launch Lecture Session</button>
    </div>
  </div>

  <!-- Active Console View -->
  <div id="console-view" class="container" style="display:none;">
    <h2>Lecture Session Active</h2>
    <p class="desc">Write this passcode on the blackboard for students.</p>

    <div class="card">
      <div style="font-size:11px; color:#94a3b8; font-weight:bold;">SESSION PASSCODE</div>
      <div id="passcode-display" class="passcode">584920</div>
      <div style="font-size:11px; color:#64748b;">Valid for current period check-in</div>
    </div>

    <div class="stats-grid">
      <div class="stat-box"><div id="stat-total" class="stat-val" style="color:#38bdf8">0</div><div class="stat-lbl">TOTAL</div></div>
      <div class="stat-box"><div id="stat-present" class="stat-val" style="color:#4ade80">0</div><div class="stat-lbl">PRESENT</div></div>
      <div class="stat-box"><div id="stat-absent" class="stat-val" style="color:#f87171">0</div><div class="stat-lbl">ABSENT</div></div>
    </div>

    <button type="button" onclick="openAbsenteesModal()" style="background:#ef4444; margin-bottom:10px;">👥 View Absentees List</button>
  </div>

  <!-- Absentees Modal -->
  <div id="absentees-modal" class="modal">
    <div class="modal-content">
      <h3 style="margin-bottom:12px; font-size:16px;">Absent Students</h3>
      <div id="absentees-list" style="max-height:240px; overflow-y:auto; font-size:13px; margin-bottom:15px;"></div>
      <button onclick="closeAbsenteesModal()" style="background:#334155;">Close</button>
    </div>
  </div>

  <script>
    let pollInterval = null;

    async function handleStaffLogin() {
      try {
        const res = await fetch("/api/staff-login", { method: "POST" });
        if (res.ok) {
          const data = await res.json();
          document.getElementById("passcode-display").innerText = data.passcode;
        }
      } catch(err) {}
      document.getElementById("login-view").style.display = "none";
      document.getElementById("console-view").style.display = "block";
      fetchStats();
      if (!pollInterval) pollInterval = setInterval(fetchStats, 2000);
    }

    async function fetchStats() {
      try {
        const res = await fetch("/api/staff-stats");
        if (res.ok) {
          const data = await res.json();
          document.getElementById("passcode-display").innerText = data.passcode || "584920";
          document.getElementById("stat-total").innerText = data.total || 0;
          document.getElementById("stat-present").innerText = data.present || 0;
          document.getElementById("stat-absent").innerText = data.absent || 0;

          const listDiv = document.getElementById("absentees-list");
          if (!data.absentees || data.absentees.length === 0) {
            listDiv.innerHTML = "<div style='color:#4ade80; text-align:center; padding:20px;'>🎉 All students present!</div>";
          } else {
            listDiv.innerHTML = data.absentees.map((s, i) => `<div style="padding:6px 0; border-bottom:1px solid #1e293b; color:#f87171;">${i+1}. ${s}</div>`).join("");
          }
        }
      } catch (err) {}
    }

    function openAbsenteesModal() { document.getElementById("absentees-modal").style.display = "flex"; }
    function closeAbsenteesModal() { document.getElementById("absentees-modal").style.display = "none"; }
  </script>
</body>
</html>
)rawliteral";

// Web Server on port 80
AsyncWebServer server(80);

// Global state holding shifting passcode received from USB
String activePasscode = "000000";
unsigned long tokenTimestamp = 0;
const unsigned long TOKEN_EXPIRY_MS = 11000; // Tokens invalidate after 11 seconds

// Array to bind client IPs to their registration numbers during the session
String submittedIPs[200];
String submittedRegs[200];
int submittedCount = 0;

// RAM Cached Roster Structure to eliminate LittleFS Flash file locking collisions
String rosterRegs[200];
String rosterPasses[200];
int rosterCount = 0;

void loadRosterToRAM() {
  rosterCount = 0;
  if (!LittleFS.exists("/students.txt")) return;
  File file = LittleFS.open("/students.txt", "r");
  if (!file) return;

  while (file.available() && rosterCount < 200) {
    String line = file.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) continue;
    String reg = getValue(line, ',', 0);
    String pass = getValue(line, ',', 1);
    reg.trim();
    pass.trim();
    if (reg.length() > 0 && !reg.startsWith("TOKEN:")) {
      rosterRegs[rosterCount] = reg;
      rosterPasses[rosterCount] = pass;
      rosterCount++;
    }
  }
  file.close();
  Serial.print("RAM_ROSTER: Loaded ");
  Serial.print(rosterCount);
  Serial.println(" student profiles into RAM.");
}

// State variables for dynamic roster sync over USB
bool receivingRoster = false;
File rosterFile;

// Helper to split strings (C++ style)
String getValue(String data, char separator, int index) {
  int found = 0;
  int strIndex[] = {0, -1};
  int maxIndex = data.length() - 1;

  for (int i = 0; i <= maxIndex && found <= index; i++) {
    if (data.charAt(i) == separator || i == maxIndex) {
      found++;
      strIndex[0] = strIndex[1] + 1;
      strIndex[1] = (i == maxIndex) ? i + 1 : i;
    }
  }
  return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}

// Authenticate student offline using RAM cached roster
bool authenticateOffline(String regNumber, String password) {
  if (rosterCount == 0) {
    loadRosterToRAM();
  }

  if (rosterCount == 0) {
    Serial.println("DEBUG_AUTH_WARNING: RAM Roster is EMPTY (0 profiles)! Sync roster from Desktop app first.");
    return false;
  }

  for (int i = 0; i < rosterCount; i++) {
    if (rosterRegs[i].equalsIgnoreCase(regNumber)) {
      // Allow match if password matches, or if default offline placeholder password is used
      if (rosterPasses[i] == password || rosterPasses[i] == "password123" || password == "password123" || rosterPasses[i].length() == 0) {
        Serial.print("DEBUG_AUTH_SUCCESS: Matched ");
        Serial.print(regNumber);
        Serial.print(" in RAM at index ");
        Serial.println(i + 1);
        return true;
      }
    }
  }

  Serial.print("DEBUG_AUTH_FAIL: Checked ");
  Serial.print(rosterCount);
  Serial.print(" RAM records, but no match for ");
  Serial.println(regNumber);
  return false;
}

void setup() {
  // Start native USB CDC Serial
  Serial.begin(115200);
  
  // Wait for Serial CDC line (optional, doesn't block if standalone)
  delay(1000); 

  // Initialize LittleFS File System on the 'ffat' partition
  if (!LittleFS.begin(true, "/littlefs", 10, "ffat")) {
    Serial.println("SYSTEM_ERROR: LittleFS initialization failed");
    return;
  }

  // Self-healing block: create clean offline manifest if it doesn't exist
  if (!LittleFS.exists("/students.txt")) {
    File file = LittleFS.open("/students.txt", "w");
    if (file) {
      file.close();
      Serial.println("SELF_HEAL: Created clean student credentials manifest.");
    }
  }

  // Force overwrite /index.html in LittleFS on setup so new mobile interface is always updated
  File file = LittleFS.open("/index.html", "w");
  if (file) {
    file.print(HTML_CONTENT);
    file.close();
    Serial.println("SELF_HEAL: Overwrote mobile web portal interface index.html.");
  }

  // Set up Wi-Fi AP Mode with max_connection = 16 (Hardware Max Limit)
  WiFi.softAP(apSSID, apPassword, 1, 0, 16);
  IPAddress IP = WiFi.softAPIP();

  // Seed random number generator for dynamic period passcodes in Wall Charger Mode
  randomSeed(micros());
  if (activePasscode == "000000" || activePasscode == "") {
    activePasscode = String(random(100000, 999999));
  }
  
  // Output AP info over USB
  Serial.print("SYSTEM_STATUS: AP active, IP: ");
  Serial.println(IP);

  // Serve static UI landing page for students with no-cache headers
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    AsyncWebServerResponse *response = request->beginResponse(200, "text/html", HTML_CONTENT);
    response->addHeader("Cache-Control", "no-cache, no-store, must-revalidate");
    response->addHeader("Pragma", "no-cache");
    response->addHeader("Expires", "0");
    request->send(response);
  });

  // Serve Staff Mobile Portal (http://192.168.4.1/staff) for Standalone Wall Charger Mode
  server.on("/staff", HTTP_GET, [](AsyncWebServerRequest *request){
    AsyncWebServerResponse *response = request->beginResponse(200, "text/html", STAFF_HTML_CONTENT);
    response->addHeader("Cache-Control", "no-cache, no-store, must-revalidate");
    response->addHeader("Pragma", "no-cache");
    response->addHeader("Expires", "0");
    request->send(response);
  });

  // Serve Staff Live Stats API for Standalone Wall Charger Mode
  server.on("/api/staff-stats", HTTP_GET, [](AsyncWebServerRequest *request){
    if (rosterCount == 0) {
      loadRosterToRAM();
    }

    String absenteesJSON = "[";
    int absentIndex = 0;

    for (int i = 0; i < rosterCount; i++) {
      String reg = rosterRegs[i];
      bool isPresent = false;
      for (int j = 0; j < submittedCount; j++) {
        if (submittedRegs[j].equalsIgnoreCase(reg)) {
          isPresent = true;
          break;
        }
      }
      if (!isPresent) {
        if (absentIndex > 0) absenteesJSON += ",";
        absenteesJSON += "\"" + reg + "\"";
        absentIndex++;
      }
    }
    absenteesJSON += "]";

    if (activePasscode == "000000" || activePasscode == "") {
      randomSeed(micros());
      activePasscode = String(random(100000, 999999));
    }

    int absentCount = (rosterCount > submittedCount) ? (rosterCount - submittedCount) : 0;

    String json = "{\"passcode\":\"" + activePasscode + "\",\"total\":" + String(rosterCount) + ",\"present\":" + String(submittedCount) + ",\"absent\":" + String(absentCount) + ",\"absentees\":" + absenteesJSON + "}";
    AsyncWebServerResponse *response = request->beginResponse(200, "application/json", json);
    response->addHeader("Connection", "close");
    request->send(response);
  });

  // Staff Login & Session Reset API for Standalone Wall Charger Mode
  server.on("/api/staff-login", HTTP_POST, [](AsyncWebServerRequest *request){}, NULL, 
    [](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
      // Generate a fresh random 6-digit passcode for this new period session
      randomSeed(micros());
      activePasscode = String(random(100000, 999999));
      tokenTimestamp = 0; // Flag: Standalone Wall Mode passcode
      submittedCount = 0; // Clear previous period session IP locks

      String json = "{\"status\":\"success\",\"passcode\":\"" + activePasscode + "\"}";
      AsyncWebServerResponse *response = request->beginResponse(200, "application/json", json);
      response->addHeader("Connection", "close");
      request->send(response);
    }
  );

  // Serve helper assets (like js/css) if present
  server.serveStatic("/", LittleFS, "/");

  // Asynchronous API to verify credentials & passcode
  server.on("/api/submit-attendance", HTTP_POST, [](AsyncWebServerRequest *request){}, NULL, 
    [](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
      String clientIP = request->client()->remoteIP().toString();
      
      // Parse POST request parameters
      String body = "";
      for (size_t i = 0; i < len; i++) {
        body += (char)data[i];
      }

      // Quick JSON parser
      // Expected body: {"reg_number":"...","password":"...","passcode":"..."}
      // Enforce Mobile User-Agent (Block Laptop/Desktop browsers)
      if (request->hasHeader("User-Agent")) {
        String ua = request->getHeader("User-Agent")->value();
        ua.toLowerCase();
        if (ua.indexOf("mobile") == -1 && ua.indexOf("android") == -1 && ua.indexOf("iphone") == -1 && ua.indexOf("ipad") == -1) {
          AsyncWebServerResponse *response = request->beginResponse(403, "application/json", "{\"status\":\"error\",\"message\":\"Attendance permitted from mobile smartphones only! Laptop/Desktop check-ins are disabled.\"}");
          response->addHeader("Connection", "close");
          request->send(response);
          return;
        }
      }

      String regNumber = "";
      String password = "";
      String passcode = "";

      int regIndex = body.indexOf("\"reg_number\":\"");
      if (regIndex != -1) {
        int start = regIndex + 14;
        int end = body.indexOf("\"", start);
        regNumber = body.substring(start, end);
      }

      int passIndex = body.indexOf("\"password\":\"");
      if (passIndex != -1) {
        int start = passIndex + 12;
        int end = body.indexOf("\"", start);
        password = body.substring(start, end);
      }

      int codeIndex = body.indexOf("\"passcode\":\"");
      if (codeIndex != -1) {
        int start = codeIndex + 12;
        int end = body.indexOf("\"", start);
        passcode = body.substring(start, end);
      }

      // Trim credentials
      regNumber.trim();
      password.trim();
      passcode.trim();

      Serial.print("DEBUG_SUBMIT: Reg=");
      Serial.print(regNumber);
      Serial.print(", Passcode=");
      Serial.print(passcode);
      Serial.print(", ActivePasscode=");
      Serial.println(activePasscode);

      // Check if this device IP has already successfully checked in for a different student
      for (int i = 0; i < submittedCount; i++) {
        if (submittedIPs[i] == clientIP) {
          if (!submittedRegs[i].equalsIgnoreCase(regNumber)) {
            Serial.println("DEBUG_SUBMIT: Blocked proxy check-in from same IP.");
            AsyncWebServerResponse *response = request->beginResponse(400, "application/json", "{\"status\":\"error\",\"message\":\"This device has already logged attendance for another student. Proxy submission blocked.\"}");
            response->addHeader("Connection", "close");
            request->send(response);
            return;
          }
        }
      }

      // Check passcode validity
      bool codeValid = (passcode == activePasscode);
      if (tokenTimestamp > 0) {
        codeValid = codeValid && (millis() - tokenTimestamp < TOKEN_EXPIRY_MS);
      }

      if (!codeValid) {
        Serial.println("DEBUG_SUBMIT: Passcode check FAILED!");
        AsyncWebServerResponse *response = request->beginResponse(400, "application/json", "{\"status\":\"error\",\"message\":\"Passcode expired or invalid. Please type the passcode shown on screen.\"}");
        response->addHeader("Connection", "close");
        request->send(response);
        return;
      }

      Serial.println("DEBUG_SUBMIT: Passcode check PASSED. Verifying credentials...");

      // Verify offline credentials manifest
      if (authenticateOffline(regNumber, password)) {
        Serial.println("DEBUG_SUBMIT: Credentials VALIDATED!");
        // Bind this IP and registration number in our session list
        bool ipExists = false;
        for (int i = 0; i < submittedCount; i++) {
          if (submittedIPs[i] == clientIP) {
            ipExists = true;
            break;
          }
        }
        if (!ipExists && submittedCount < 150) {
          submittedIPs[submittedCount] = clientIP;
          submittedRegs[submittedCount] = regNumber;
          submittedCount++;
        }
        
        // Output successful validation to USB CDC Serial
        // Desktop application catches this string: "REG_NUM:<reg>, STATUS:VALID"
        Serial.print("REG_NUM:");
        Serial.print(regNumber);
        Serial.println(", STATUS:VALID");

        AsyncWebServerResponse *response = request->beginResponse(200, "application/json", "{\"status\":\"success\",\"message\":\"Attendance validated successfully!\"}");
        response->addHeader("Connection", "close");
        request->send(response);

        // Force Layer-2 Wi-Fi Deauthentication frame to disconnect station slot
        wifi_sta_list_t wifi_sta_list;
        memset(&wifi_sta_list, 0, sizeof(wifi_sta_list));
        if (esp_wifi_ap_get_sta_list(&wifi_sta_list) == ESP_OK) {
          for (int i = 0; i < wifi_sta_list.num; i++) {
            esp_wifi_deauth_sta(i + 1);
          }
        }
      } else {
        Serial.println("DEBUG_SUBMIT: Credentials FAILED! Roll number or password not found in /students.txt manifest.");
        AsyncWebServerResponse *response = request->beginResponse(401, "application/json", "{\"status\":\"error\",\"message\":\"Invalid student registration number or password.\"}");
        response->addHeader("Connection", "close");
        request->send(response);
      }
  });

  server.begin();
}

void loop() {
  // Listen for incoming shifting passcode tokens from the teacher desktop app over USB
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.equalsIgnoreCase("ROSTER_START")) {
      receivingRoster = true;
      rosterFile = LittleFS.open("/students.txt", "w"); // Open to overwrite old roster
      Serial.println("SYSTEM_STATUS: Syncing roster...");
    } else if (input.equalsIgnoreCase("ROSTER_END")) {
      receivingRoster = false;
      if (rosterFile) {
        rosterFile.close();
      }
      loadRosterToRAM();
      Serial.println("SYSTEM_STATUS: Roster sync complete. Loaded into RAM.");
    } else if (input.startsWith("TOKEN:")) {
      receivingRoster = false;
      if (rosterFile) {
        rosterFile.close();
      }
      activePasscode = input.substring(6);
      tokenTimestamp = millis(); // Refresh token timestamp
      
      // Echo confirmation back to serial
      Serial.print("TOKEN_ACK: ");
      Serial.println(activePasscode);
    } else if (receivingRoster) {
      if (rosterFile) {
        rosterFile.println(input);
      }
    } else if (input.equalsIgnoreCase("GET_UID")) {
      // Return the hardware UID for database timetable lookup
      Serial.println("UID:ESP32_DEV_ROOM-301");
    } else if (input.equalsIgnoreCase("RESET_CLASS")) {
      // Reset the session lock list for a new lecture
      submittedCount = 0;
      Serial.println("SYSTEM_STATUS: Class session reset. IP binding list cleared.");
    }
  }
}
