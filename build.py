import os
import sys
import shutil
import subprocess
import yaml

# Load .env file manually if it exists
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

# ANSI COLORS
CLR_RESET  = "\033[0m"
CLR_BOLD   = "\033[1m"
CLR_RED    = "\033[31m"
CLR_GREEN  = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_BLUE   = "\033[34m"
CLR_CYAN   = "\033[36m"
CLR_GRAY   = "\033[90m"

def log_step(msg): print(f"{CLR_BOLD}{CLR_CYAN}-- {msg}{CLR_RESET}")
def log_info(msg): print(f"{CLR_GRAY}[INFO]{CLR_RESET} {msg}")
def log_ok(msg):   print(f"{CLR_GREEN}[DONE]{CLR_RESET} {msg}")
def log_warn(msg): print(f"{CLR_YELLOW}[WARN]{CLR_RESET} {msg}")
def log_err(msg):  print(f"{CLR_RED}[FAIL]{CLR_RESET} {msg}")

IS_WINDOWS = sys.platform == "win32"
SEP = ";" if IS_WINDOWS else ":"
EXE_EXT = ".exe" if IS_WINDOWS else ""

if IS_WINDOWS:
    os.system('')

def draw_progress(percent, label="Building"):
    bar_len = 35
    filled_len = int(bar_len * percent / 100)
    bar = "#" * filled_len + "-" * (bar_len - filled_len)
    sys.stdout.write(f"\r  {CLR_CYAN}{bar}{CLR_RESET} {CLR_BOLD}{percent:>3}%{CLR_RESET}  {CLR_GRAY}{label:<25}{CLR_RESET}")
    sys.stdout.flush()

def get_customtkinter_path():
    try:
        import customtkinter
        return os.path.dirname(customtkinter.__file__)
    except ImportError:
        log_err("customtkinter is not installed.")
        sys.exit(1)

def sign_binary(binary_path):
    if not IS_WINDOWS:
        return
        
    thumbprint = os.environ.get("PLANMINER_SIGN_THUMBPRINT")
    pfx_pass = os.environ.get("PLANMINER_PFX_PASS")
    pfx_path = os.path.join("code-sign", "codesign.pfx")
    
    if not thumbprint and not pfx_pass:
        log_warn("Neither PLANMINER_SIGN_THUMBPRINT nor PLANMINER_PFX_PASS is set. Skipping signing.")
        return
        
    signtool = None
    search_paths = [
        r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe",
        r"C:\Program Files (x86)\Windows Kits\10\App Certification Kit\signtool.exe"
    ]
    for p in search_paths:
        if os.path.exists(p):
            signtool = p
            break
    if not signtool:
        signtool = shutil.which("signtool.exe")
    if not signtool:
        log_warn("signtool.exe not found. Skipping signing.")
        return
        
    log_step(f"Signing binary: {os.path.basename(binary_path)}...")
    
    try:
        if thumbprint:
            # Secure signing via Windows Certificate Store (no CLI password arguments)
            cmd = [signtool, "sign", "/sha1", thumbprint,
                   "/fd", "SHA256", "/t", "http://timestamp.digicert.com", "/v", os.path.abspath(binary_path)]
        else:
            # Legacy file-based signing with password
            log_warn("SECURITY WARNING: Passing password via command line argument can expose credentials to process monitors.")
            if not os.path.exists(pfx_path):
                log_info(f"Codesign PFX not found at {pfx_path}. Skipping signing.")
                return
            cmd = [signtool, "sign", "/f", os.path.abspath(pfx_path), "/p", pfx_pass,
                   "/fd", "SHA256", "/t", "http://timestamp.digicert.com", "/v", os.path.abspath(binary_path)]
                   
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            log_ok("Binary successfully signed.")
        else:
            log_warn(f"Signing failed with code {result.returncode}")
            if result.stderr:
                log_warn(f"Error details: {result.stderr.strip()}")
    except Exception as e:
        log_warn(f"Signing error: {e}")

def build():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(app_dir, "assets", "config.yaml")
    
    if not os.path.exists("assets") or not os.path.exists(config_path):
        log_err("Build script must be run from the 'planminer' root directory.")
        sys.exit(1)
        
    print(f"\n{CLR_BOLD}{CLR_BLUE}============================================================{CLR_RESET}")
    print(f"{CLR_BOLD}{CLR_BLUE}             PlanMiner - Build Pipeline                    {CLR_RESET}")
    print(f"{CLR_BOLD}{CLR_BLUE}============================================================{CLR_RESET}\n")

    cfg = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

    branding = cfg.get("branding", {})
    app_name = branding.get("app_name", "PlanMiner")
    company = branding.get("company_name", "Unknown")
    version_file_name = branding.get("version_file", "VERSION")
    version_file = os.path.join(app_dir, version_file_name)
    
    licensing = cfg.get("licensing", {})
    license_to = licensing.get("licensed_to", "Unknown")
    expiry = licensing.get("expiry_date", "None")

    # Load version
    app_version = "Unknown"
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            app_version = f.read().strip()

    # PRE-FLIGHT CHECK
    print(f"{CLR_BOLD}{CLR_YELLOW}+-- PRE-FLIGHT CHECK ---------------------------------------+{CLR_RESET}")
    print(f"{CLR_YELLOW}|{CLR_RESET}  Application   : {CLR_BOLD}{CLR_CYAN}{app_name:<38}{CLR_RESET} {CLR_YELLOW}|{CLR_RESET}")
    print(f"{CLR_YELLOW}|{CLR_RESET}  Company       : {CLR_BOLD}{company:<38}{CLR_RESET} {CLR_YELLOW}|{CLR_RESET}")
    print(f"{CLR_YELLOW}|{CLR_RESET}  Version       : {CLR_BOLD}{app_version:<38}{CLR_RESET} {CLR_YELLOW}|{CLR_RESET}")
    print(f"{CLR_YELLOW}|{CLR_RESET}  Licensed To   : {CLR_BOLD}{license_to:<38}{CLR_RESET} {CLR_YELLOW}|{CLR_RESET}")
    print(f"{CLR_YELLOW}|{CLR_RESET}  Expiry Date   : {CLR_BOLD}{CLR_RED if expiry != 'None' else ''}{expiry:<38}{CLR_RESET} {CLR_YELLOW}|{CLR_RESET}")
    print(f"{CLR_BOLD}{CLR_YELLOW}+-----------------------------------------------------------+{CLR_RESET}")

    # Assets Compliance Verification
    log_step("Verifying assets compliance...")
    compliance_checks = [
        ("Logo PNG", os.path.join("assets", "logo", "logo.png")),
        ("Favicon Icon", os.path.join("assets", "logo", "favicon.ico")),
        ("Presets DB", os.path.join("assets", "presets", "presets.json")),
        ("Version File", "VERSION")
    ]
    all_ok = True
    for label, path in compliance_checks:
        exists = os.path.exists(path)
        status = f"[{CLR_GREEN}FOUND{CLR_RESET}]" if exists else f"[{CLR_RED}MISSING{CLR_RESET}]"
        if not exists: all_ok = False
        print(f"  {label:<20} : {path:<40} {status}")
        
    if not all_ok:
        log_err("Asset verification failed. Cancelled build.")
        sys.exit(1)

    confirm = input(f"\n{CLR_BOLD}Proceed with build? [y/N]: {CLR_RESET}").lower().strip()
    if confirm != 'y':
        log_warn("Build aborted by user.")
        sys.exit(0)

    # 1. Clean
    log_step("Cleaning up previous build artifacts...")
    for folder in ['build', 'dist', 'PlanMiner_Dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            os.remove(file)

    # 2. PyInstaller
    log_step("Executing PyInstaller build...")
    ctk_path = get_customtkinter_path()
    add_data_flag = f"{ctk_path}{SEP}customtkinter"
    assets_data = f"assets{SEP}assets"
    version_data = f"VERSION{SEP}."
    icon_path = os.path.join("assets", "logo", "favicon.ico")
    main_script = "app_gui.py"

    exclusions = ["torch", "torchvision", "tensorflow", "transformers", "onnxruntime", 
                  "scipy", "pandas", "matplotlib", "sympy", "nltk", "numba", "llvmlite", "lxml", "pyarrow"]

    cmd = [
        "pyinstaller", "--onefile", "--noconsole", "--noconfirm",
        f"--add-data={add_data_flag}", f"--add-data={assets_data}", f"--add-data={version_data}",
        f"--icon={icon_path}", "--name=PlanMiner"
    ]
    for exc in exclusions:
        cmd.append(f"--exclude-module={exc}")
    cmd.append(main_script)

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        draw_progress(0, "Initiating Analysis")
        for line in process.stdout:
            if "checking Analysis" in line: draw_progress(15, "Analyzing Code")
            elif "Building Analysis" in line: draw_progress(30, "Analyzing Dependencies")
            elif "Building PYZ" in line: draw_progress(50, "Packaging Modules")
            elif "Building PKG" in line: draw_progress(70, "Creating Bundle")
            elif "Building EXE" in line: draw_progress(90, "Finalizing Executable")
            elif "Completed successfully" in line:
                draw_progress(100, "Build Complete")
                print()
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
        log_ok("PyInstaller build completed.")
    except Exception as e:
        log_err(f"Build failed: {e}")
        sys.exit(1)

    # 3. Post-build cleanup
    log_step("Performing post-build cleanup...")
    if os.path.exists('build'):
        shutil.rmtree('build')
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            os.remove(file)

    # 4. Move executable and sign
    log_step("Finalizing binary output...")
    final_output_dir = "PlanMiner_Dist"
    if os.path.exists('dist'):
        os.makedirs(final_output_dir, exist_ok=True)
        exe_name = f"PlanMiner{EXE_EXT}"
        src_exe = os.path.join('dist', exe_name)
        dst_exe = os.path.join(final_output_dir, exe_name)
        shutil.move(src_exe, dst_exe)
        shutil.rmtree('dist')

        # Rename binary with version info
        ver_suffix = app_version.replace(".", "_")
        final_exe_name = f"PlanMiner_v{ver_suffix}{EXE_EXT}"
        final_exe_path = os.path.join(final_output_dir, final_exe_name)
        if os.path.exists(final_exe_path):
            os.remove(final_exe_path)
        os.rename(dst_exe, final_exe_path)

        # Copy deployment guides and cert
        cert_src = os.path.join("code-sign", "codesign.cer")
        guide_src = os.path.join("code-sign", "CERT_DEPLOYMENT_GUIDE.html")
        
        if os.path.exists(cert_src):
            shutil.copy(cert_src, os.path.join(final_output_dir, "codesign.cer"))
            log_info("Copied codesign.cer to dist folder")
            
        if os.path.exists(guide_src):
            shutil.copy(guide_src, os.path.join(final_output_dir, "CERT_DEPLOYMENT_GUIDE.html"))
            log_info("Copied CERT_DEPLOYMENT_GUIDE.html to dist folder")

        sign_binary(final_exe_path)
        
        print(f"\n{CLR_BOLD}{CLR_GREEN}============================================================{CLR_RESET}")
        print(f"{CLR_BOLD}{CLR_GREEN} SUCCESS! Standalone build ready in '{final_output_dir}'{CLR_RESET}")
        print(f"{CLR_BOLD}{CLR_GREEN}============================================================{CLR_RESET}")
        log_info(f"Binary path: {CLR_CYAN}{final_exe_path}{CLR_RESET}\n")
    else:
        log_err("dist folder not found.")

if __name__ == "__main__":
    try:
        build()
    except KeyboardInterrupt:
        print(f"\n{CLR_YELLOW}[WARN]{CLR_RESET} Build interrupted by user.")
        sys.exit(0)
