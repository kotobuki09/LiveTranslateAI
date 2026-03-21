"""
Build script — creates a standalone LiveTranslate.exe via PyInstaller.

Usage:
    python scripts/build_exe.py

Output: dist/LiveTranslate.exe (single file, no console window)

Key fixes vs previous version:
  - Does NOT bundle config.json inside the exe — configuration is written
    next to the exe (or to %APPDATA%\\LiveTranslate) at runtime by json_config.py
  - Adds missing hidden-imports for azure.cognitiveservices.speech DLLs
  - Adds --runtime-tmpdir to avoid permission errors on some systems
  - Copies final exe to plan/release/ for GitHub upload
"""
import subprocess
import sys
from pathlib import Path
import shutil

ROOT     = Path(__file__).parent.parent
SRC      = ROOT / "src"
ICON     = SRC / "assets" / "icon.ico"
RELEASES = ROOT / "plan" / "release"
sys.path.insert(0, str(ROOT / "src"))


def main():
    # Ensure release directory exists
    RELEASES.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=LiveTranslate",
        "--onedir",
        "--windowed",                           # No console window
        "--noconfirm",                          # Force overwrite without prompting
        f"--add-data={SRC};src",

        # ── Core hidden imports ────────────────────────────────────────
        "--hidden-import=pystray",
        "--hidden-import=pystray._win32",
        "--hidden-import=keyboard",
        "--hidden-import=pyaudio",
        "--hidden-import=PIL",
        "--hidden-import=PIL._imagingtk",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=pydantic",
        "--hidden-import=requests",
        "--hidden-import=websocket",
        "--hidden-import=websockets",
        "--hidden-import=google.genai",
        "--hidden-import=dotenv",
        "--hidden-import=python_dotenv",

        # ── PyQt5 ─────────────────────────────────────────────────────
        "--hidden-import=PyQt5",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.sip",

        # ── Azure Speech SDK (DLLs collected separately) ───────────────
        "--hidden-import=azure.cognitiveservices.speech",

        # ── Collect full packages ──────────────────────────────────────
        "--collect-all=azure.cognitiveservices.speech",
        "--collect-all=google.genai",
        "--collect-all=PyQt5",

        # ── Suppress console on Windows (belt-and-suspenders) ─────────
        "--noconsole",
        f"--version-file={ROOT / 'scripts' / 'version_info.txt'}",
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
        dist_dir = ROOT / "dist" / "LiveTranslate"
        if dist_dir.exists():
            print(f"\n✓  Build complete! Zipping the final application...")
            import config
            zip_path = RELEASES / f"LiveTranslate_v{config.VERSION}_Portable"
            try:
                shutil.make_archive(str(zip_path), "zip", dist_dir)
                print(f"✓  Release generated: {zip_path}.zip")
            except Exception as e:
                print(f"⚠  Warning: Could not create zip archive: {e}")
                print("   (Proceeding anyway — dist/ folder is still available)")
            
            print(f"✓  Output folder: dist/LiveTranslate  (Fast Startup Version)")
            print()
            print("NOTE: On first launch users will see a Windows SmartScreen warning.")
            print("      They must click 'More info' → 'Run anyway'.")
            print("      This is normal for unsigned executables.")
        else:
            print("\n✗  Build finished but output folder was not found in dist/")
    else:
        print("\n✗  Build failed — check output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
