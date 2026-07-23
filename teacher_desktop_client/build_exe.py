import os
import subprocess
import sys

def build_standalone_exe():
    print("Setting up PyInstaller compilation environment...")
    
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller is not installed. Installing it now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
    try:
        import customtkinter
    except ImportError:
        print("customtkinter is not installed. Installing it now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
        import customtkinter

    # Find the customtkinter folder location to bundle its fonts and JSON theme files
    ctk_path = os.path.dirname(customtkinter.__file__)
    print(f"Located customtkinter library path: {ctk_path}")

    # Build options
    # On Windows, PyInstaller data files are separated by a semicolon (;)
    add_data_param = f"{ctk_path}{os.pathsep}customtkinter"
    
    commands = [
        "app.py",                    # Target entry file
        "--name=InstructorConsole",   # Output name
        "--noconfirm",               # Overwrite existing build
        "--onedir",                  # Bundle as directory containing executable
        "--windowed",                # Hide console window on startup
        f"--add-data={add_data_param}", # Bundle customtkinter components
        "--add-data=token_generator.py;.", # Bundle sibling scripts
    ]

    print(f"Running command: pyinstaller {' '.join(commands)}")
    
    import PyInstaller.__main__
    PyInstaller.__main__.run(commands)
    
    print("\n==================================================")
    print("Compilation completed! Standalone bundle is saved in:")
    print(f"{os.path.join(os.getcwd(), 'dist', 'InstructorConsole')}")
    print("==================================================")

if __name__ == "__main__":
    build_standalone_exe()
