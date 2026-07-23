import time
import sys
import os
import subprocess
import webbrowser
import serial.tools.list_ports

# Target web portal URL (configurable for local dev, Render, or College Subdomain)
PORTAL_URL = os.environ.get("ATTENDANCE_PORTAL_URL", "https://smartattendance-jlal.onrender.com/instructor")

# Known ESP32 USB Vendor IDs (303A: Native ESP32 USB CDC, 10C4: CP2102, 1A86: CH340)
ESP32_VIDS = [0x303A, 0x10C4, 0x1A86]

def detect_esp32_port():
    """Scans system serial ports for connected ESP32 hardware"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.vid in ESP32_VIDS or "ESP32" in (port.description or "").upper() or "CP210" in (port.description or "").upper():
            return port.device, port.description
    return None, None

def show_windows_toast_notification(title, message, target_url):
    """Triggers a native Windows Notification popup when ESP32 USB cable is plugged in"""
    ps_script = f'''
    [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
    $notification = New-Object System.Windows.Forms.NotifyIcon
    $notification.Icon = [System.Drawing.SystemIcons]::Information
    $notification.BalloonTipTitle = "{title}"
    $notification.BalloonTipText = "{message}"
    $notification.Visible = $True
    $notification.add_BalloonTipClicked({{
        Start-Process "{target_url}"
    }})
    $notification.ShowBalloonTip(10000)
    Start-Sleep -Seconds 10
    $notification.Dispose()
    '''
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print("Toast Notification Notice:", e)

def main():
    print("=" * 60)
    print(" 🚀 PROXIMITY ATTENDANCE - USB HARDWARE POPUP LAUNCHER")
    print(f" Monitoring USB ports for ESP32 insertion...")
    print(f" Target Domain: {PORTAL_URL}")
    print("=" * 60)

    last_detected_port = None
    cooldown_until = 0

    while True:
        try:
            device, description = detect_esp32_port()
            current_time = time.time()

            if device and device != last_detected_port and current_time > cooldown_until:
                print(f"\n[USB EVENT DETECTED] ESP32 plugged in on {device} ({description})")
                print("Displaying Windows Notification Popup...")
                
                # 1. Trigger Native Windows Toast Notification Popup
                show_windows_toast_notification(
                    title="⚡ Proximity Attendance Node Connected",
                    message=f"Hardware connected on {device}. Click here to open Attendance Console.",
                    target_url=PORTAL_URL
                )

                # 2. Also open default web browser (Chrome / Edge) directly to the online portal
                webbrowser.open(PORTAL_URL, new=2)
                
                last_detected_port = device
                cooldown_until = current_time + 10  # 10-second cooldown

            elif not device:
                last_detected_port = None

            time.sleep(1.5)  # Poll USB ports every 1.5 seconds

        except KeyboardInterrupt:
            print("\nHardware listener stopped.")
            sys.exit(0)
        except Exception as e:
            print(f"Error in USB monitor loop: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
