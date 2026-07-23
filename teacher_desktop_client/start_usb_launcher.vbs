Set WshShell = CreateObject("WScript.Shell")
' Runs usb_auto_launcher.py silently in the background without any command prompt or terminal window
WshShell.Run "pythonw.exe usb_auto_launcher.py", 0, False
