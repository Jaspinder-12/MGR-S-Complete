#!/usr/bin/env python3
"""
MGR-S Unified Cross-Platform Build System
Handles PyInstaller, MSIX (Windows), and AppImage (Linux) bundling.
"""

import os
import sys
import subprocess
import shutil
import argparse
import platform
import glob

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_DIR = os.path.join(PROJECT_ROOT, "ui")
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")
APP_NAME = "MGR-S"
VERSION = "0.2"

def run_cmd(cmd, cwd=None):
    """Wrapper for running shell commands."""
    if isinstance(cmd, list):
        # On Windows, joins with spaces. Avoid manual quoting in the list.
        cmd_str = " ".join(cmd)
    else:
        cmd_str = cmd
    print(f"Executing: {cmd_str}")
    result = subprocess.run(cmd_str, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f"Error: Command failed with return code {result.returncode}")
        sys.exit(result.returncode)

def build_windows_exe():
    """Builds the standalone Windows executable using PyInstaller."""
    print("--- Building Windows Executable (Onefile) ---")
    spec_path = os.path.join(UI_DIR, "mgrs_app.spec")
    run_cmd(["python", "-m", "PyInstaller", spec_path, "--noconfirm"], cwd=PROJECT_ROOT)
    
    # Deploy to root for convenience
    src_exe = os.path.join(DIST_DIR, "mgrs_app.exe")
    dest_exe = os.path.join(PROJECT_ROOT, "mgrs_app.exe")
    if os.path.exists(src_exe):
        shutil.copy2(src_exe, dest_exe)
        print(f"Success: {dest_exe}")

def build_windows_msix():
    """Builds the modern MSIX package for Windows."""
    print("--- Building MSIX Package (Windows Modern Standard) ---")
    
    # 1. Ensure assets exist
    from create_icon import generate_msix_assets
    icon_png = os.path.join(UI_DIR, "resources", "mgrs_icon.png")
    msix_assets = os.path.join(PROJECT_ROOT, "installer", "Assets")
    generate_msix_assets(icon_png, msix_assets)
    
    # 2. Prepare staging area
    staging = os.path.join(BUILD_DIR, "msix_staging")
    if os.path.exists(staging): shutil.rmtree(staging)
    os.makedirs(staging)
    
    # Copy exe and manifest
    shutil.copy2(os.path.join(PROJECT_ROOT, "mgrs_app.exe"), staging)
    shutil.copy2(os.path.join(PROJECT_ROOT, "installer", "AppxManifest.xml"), staging)
    shutil.copytree(msix_assets, os.path.join(staging, "Assets"))
    
    # 3. Create Package
    makeappx = r"C:\Program Files (x86)\Windows Kits\10\App Certification Kit\makeappx.exe"
    output_msix = os.path.join(DIST_DIR, f"{APP_NAME}_{VERSION}.msix")
    
    # Use quotes for paths with spaces, but let run_cmd handle the joining
    run_cmd([
        f'"{makeappx}"', 
        "pack", 
        "/d", f'"{staging}"', 
        "/p", f'"{output_msix}"', 
        "/o"
    ])
    
    print(f"Success: {output_msix}")
    print("Note: MSIX must be signed with a trusted certificate before installation.")

def build_linux_appimage():
    """Builds an AppImage for Linux/Ubuntu distribution."""
    print("--- Building Linux AppImage (Ubuntu/Universal) ---")
    # This logic assumes running on Ubuntu with linuxdeploy installed
    desktop_content = f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Exec=mgrs_app
Icon=mgrs_icon
Categories=Utility;System;
Comment=Multi-GPU Runtime System
"""
    os.makedirs(os.path.join(PROJECT_ROOT, "linux"), exist_ok=True)
    with open(os.path.join(PROJECT_ROOT, "linux", f"{APP_NAME}.desktop"), "w") as f:
        f.write(desktop_content)
    
    print("Linux desktop entry created. Run 'linuxdeploy --appdir AppDir -e mgrs_app -i icon.png -d linux/MGR-S.desktop --output appimage' on Ubuntu.")

def main():
    parser = argparse.ArgumentParser(description="MGR-S Build System")
    parser.add_argument("--windows", action="store_true", help="Build Windows artifacts (EXE, MSIX)")
    parser.add_argument("--linux", action="store_true", help="Build Linux artifacts (AppImage)")
    parser.add_argument("--all", action="store_true", help="Build for all platforms")
    
    args = parser.parse_args()
    
    if args.all or args.windows:
        build_windows_exe()
        build_windows_msix()
        
    if args.all or args.linux:
        build_linux_appimage()

    if not (args.windows or args.linux or args.all):
        parser.print_help()

if __name__ == "__main__":
    main()
