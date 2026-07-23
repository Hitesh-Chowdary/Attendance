import time
import sys
import os
import webbrowser
import serial.tools.list_ports

# Target web portal URL (configurable for local dev, Render, or College Subdomain)
# Default live Render cloud URL:
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

def main():
    print("=" * 60)
    print(" 🚀 PROXIMITY ATTENDANCE - USB HARDWARE AUTO-LAUNCHER")
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
                print(f"Auto-opening web portal: {PORTAL_URL}")
                
                # Open default web browser (Chrome / Edge) to the online instructor portal
                webbrowser.open(PORTAL_URL, new=2)
                
                last_detected_port = device
                cooldown_until = current_time + 10  # 10-second cooldown to prevent duplicate tabs
            
            elif not device:
                last_detected_port = None

            time.sleep(1.5)  # Poll USB ports every 1.5 seconds

        except KeyboardInterrupt:
            print("\nAuto-launcher stopped.")
            sys.exit(0)
        except Exception as e:
            print(f"Error in USB monitor loop: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
