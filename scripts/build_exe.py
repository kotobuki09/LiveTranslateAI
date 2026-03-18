"""
Build script — creates a standalone LiveTranslate.exe via PyInstaller.

Usage:
    python scripts/build_exe.py

Output: dist/LiveTranslate.exe (single file, no console window)
"""
import subprocess
import sys
from pathlib import Path

import shutil

ROOT = Path(__file__).parent.parent
SRC  = ROOT / "src"
ICON = SRC / "assets" / "icon.ico"
RELEASES = ROOT / "plan" / "release"


def main():
    # Ensure release directory exists
    RELEASES.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=LiveTranslate",
        "--onefile",
        "--windowed",                          # No console window
        f"--add-data={SRC};src",
        "--hidden-import=pystray",
        "--hidden-import=keyboard",
        "--hidden-import=pyaudio",
        "--hidden-import=PIL",
        "--hidden-import=PIL._imagingtk",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=pydantic",
        "--hidden-import=requests",
        "--hidden-import=websocket",
        "--collect-all=azure.cognitiveservices.speech",
        "--collect-all=google.genai",
        "--collect-all=PyQt5",
    ]
    
    if ICON.exists():
        cmd.append(f"--icon={ICON}")
        print(f"Using icon: {ICON}")
    else:
        print("Warning: icon.ico not found, building without it.")

    cmd.append(str(ROOT / "main.py"))

    print("Building LiveTranslate.exe …")
    result = subprocess.run(cmd, cwd=ROOT)
    
    if result.returncode == 0:
        exe_src = ROOT / "dist" / "LiveTranslate.exe"
        if exe_src.exists():
            shutil.copy2(exe_src, RELEASES / "LiveTranslate.exe")
            print(f"\n✓  Build complete!")
            print(f"✓  Output saved to: dist/LiveTranslate.exe")
            print(f"✓  Release copied to: {RELEASES}/LiveTranslate.exe")
        else:
            print("\n✗  Build finished but .exe was not found in dist/")
    else:
        print("\n✗  Build failed — check output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
