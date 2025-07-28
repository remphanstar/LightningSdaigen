# ~ diagnose_and_fix.py | Diagnostic and Fix Script for LightningSdaigen ~

import sys
import os
from pathlib import Path
import subprocess
import json

def get_paths():
    """Get the correct paths for the current environment."""
    osENV = os.environ
    PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
    
    if PATHS:
        HOME = PATHS['home_path']
        VENV = PATHS['venv_path']
        SCR_PATH = PATHS['scr_path']
        SETTINGS_PATH = PATHS['settings_path']
    else:
        # Fallback detection
        if '/content' in os.getcwd():
            HOME = Path('/content')
        elif '/kaggle' in os.getcwd():
            HOME = Path('/kaggle/working')
        else:
            HOME = Path.cwd()
        
        SCR_PATH = HOME / 'ANXETY'
        VENV = HOME / 'venv'
        SETTINGS_PATH = SCR_PATH / 'settings.json'
    
    return HOME, VENV, SCR_PATH, SETTINGS_PATH

def check_environment():
    """Check the current environment and identify issues."""
    
    print("🔍 LightningSdaigen Diagnostic Tool")
    print("=" * 50)
    
    HOME, VENV, SCR_PATH, SETTINGS_PATH = get_paths()
    
    issues = []
    fixes = []
    
    print(f"🏠 Home directory: {HOME}")
    print(f"📁 Script directory: {SCR_PATH}")
    print(f"🐍 Venv directory: {VENV}")
    print(f"⚙️ Settings file: {SETTINGS_PATH}")
    print()
    
    # Check 1: Directory structure
    print("📋 Checking directory structure...")
    required_dirs = {
        'ANXETY': SCR_PATH,
        'modules': SCR_PATH / 'modules',
        'scripts': SCR_PATH / 'scripts',
        '__configs__': SCR_PATH / '__configs__'
    }
    
    for name, path in required_dirs.items():
        if path.exists():
            print(f"  ✅ {name}: {path}")
        else:
            print(f"  ❌ {name}: {path} (MISSING)")
            issues.append(f"Missing directory: {path}")
            fixes.append(f"Create directory: mkdir -p {path}")
    
    # Check 2: Core files
    print("\n📄 Checking core files...")
    core_files = {
        'settings.json': SETTINGS_PATH,
        'json_utils.py': SCR_PATH / 'modules' / 'json_utils.py',
        'widgets-en.py': SCR_PATH / 'scripts' / 'widgets-en.py',
        'downloading-en.py': SCR_PATH / 'scripts' / 'downloading-en.py',
        'launch.py': SCR_PATH / 'scripts' / 'launch.py'
    }
    
    for name, path in core_files.items():
        if path.exists():
            print(f"  ✅ {name}: {path}")
        else:
            print(f"  ❌ {name}: {path} (MISSING)")
            issues.append(f"Missing file: {path}")
    
    # Check 3: Virtual environment
    print("\n🐍 Checking virtual environment...")
    if VENV.exists():
        print(f"  ✅ Venv directory: {VENV}")
        
        # Check for Python executable
        venv_python_paths = [
            VENV / 'bin' / 'python',
            VENV / 'Scripts' / 'python.exe'
        ]
        
        venv_python_found = False
        for python_path in venv_python_paths:
            if python_path.exists():
                print(f"  ✅ Python executable: {python_path}")
                venv_python_found = True
                break
        
        if not venv_python_found:
            print(f"  ❌ Python executable not found in venv")
            issues.append("Virtual environment Python executable missing")
            fixes.append("Recreate virtual environment")
        
        # Check for pip
        pip_paths = [
            VENV / 'bin' / 'pip',
            VENV / 'Scripts' / 'pip.exe'
        ]
        
        pip_found = False
        for pip_path in pip_paths:
            if pip_path.exists():
                print(f"  ✅ Pip executable: {pip_path}")
                pip_found = True
                break
        
        if not pip_found:
            print(f"  ❌ Pip not found in venv")
            issues.append("Pip missing from virtual environment")
            fixes.append("Reinstall pip in virtual environment")
    else:
        print(f"  ❌ Virtual environment not found: {VENV}")
        issues.append("Virtual environment missing")
        fixes.append("Create virtual environment")
    
    # Check 4: Settings file
    print("\n⚙️ Checking settings...")
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, 'r') as f:
                settings = json.load(f)
            
            print(f"  ✅ Settings file readable")
            
            # Check required sections
            required_sections = ['WEBUI', 'WIDGETS', 'ENVIRONMENT']
            for section in required_sections:
                if section in settings:
                    print(f"    ✅ {section} section present")
                else:
                    print(f"    ❌ {section} section missing")
                    issues.append(f"Settings section missing: {section}")
            
        except json.JSONDecodeError as e:
            print(f"  ❌ Settings file corrupted: {e}")
            issues.append("Settings file corrupted")
            fixes.append("Recreate settings file")
        except Exception as e:
            print(f"  ❌ Settings file error: {e}")
            issues.append(f"Settings file error: {e}")
    else:
        print(f"  ❌ Settings file missing: {SETTINGS_PATH}")
        issues.append("Settings file missing")
        fixes.append("Run setup cell to create settings")
    
    # Check 5: Dependencies
    print("\n📦 Checking system dependencies...")
    required_tools = ['git', 'curl', 'wget']
    
    for tool in required_tools:
        if subprocess.run(['which', tool], capture_output=True).returncode == 0:
            print(f"  ✅ {tool} available")
        else:
            print(f"  ❌ {tool} missing")
            issues.append(f"System tool missing: {tool}")
            fixes.append(f"Install {tool}: apt-get install {tool}")
    
    # Summary
    print("\n" + "=" * 50)
    if issues:
        print(f"❌ Found {len(issues)} issues:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        print(f"\n🔧 Suggested fixes:")
        for i, fix in enumerate(fixes, 1):
            print(f"  {i}. {fix}")
    else:
        print("✅ No major issues detected!")
    
    return issues, fixes

def fix_venv():
    """Fix virtual environment issues."""
    
    HOME, VENV, SCR_PATH, SETTINGS_PATH = get_paths()
    
    print("🔧 Fixing virtual environment...")
    
    # Remove existing broken venv
    if VENV.exists():
        print(f"🗑️ Removing existing venv: {VENV}")
        import shutil
        shutil.rmtree(VENV)
    
    # Create new venv
    print(f"🌱 Creating new virtual environment...")
    try:
        subprocess.run([sys.executable, '-m', 'venv', str(VENV)], check=True)
        print("✅ Virtual environment created successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create venv: {e}")
        return False
    
    # Install pip if needed
    venv_python = VENV / 'bin' / 'python'
    if not venv_python.exists():
        venv_python = VENV / 'Scripts' / 'python.exe'
    
    if venv_python.exists():
        print("🔧 Ensuring pip is available...")
        try:
            subprocess.run([str(venv_python), '-m', 'ensurepip', '--upgrade'], 
                         check=False, capture_output=True)
            print("✅ Pip ensured in virtual environment")
        except Exception as e:
            print(f"⚠️ Pip setup warning: {e}")
    
    return True

def fix_settings():
    """Fix or recreate settings file."""
    
    HOME, VENV, SCR_PATH, SETTINGS_PATH = get_paths()
    
    print("🔧 Fixing settings file...")
    
    # Create basic settings structure
    default_settings = {
        "ENVIRONMENT": {
            "env_name": "Google Colab",
            "fork": "remphanstar/LightningSdaigen",
            "branch": "main",
            "start_timer": 0
        },
        "WEBUI": {
            "current": "A1111",
            "latest": None,
            "webui_path": str(HOME / "A1111")
        },
        "WIDGETS": {}
    }
    
    # Ensure directory exists
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Write settings
    try:
        with open(SETTINGS_PATH, 'w') as f:
            json.dump(default_settings, f, indent=4)
        print(f"✅ Settings file created: {SETTINGS_PATH}")
        return True
    except Exception as e:
        print(f"❌ Failed to create settings: {e}")
        return False

def run_fixes():
    """Run all available fixes."""
    
    print("🔧 Running automatic fixes...")
    
    # Fix 1: Create missing directories
    HOME, VENV, SCR_PATH, SETTINGS_PATH = get_paths()
    
    required_dirs = [
        SCR_PATH,
        SCR_PATH / 'modules',
        SCR_PATH / 'scripts',
        SCR_PATH / '__configs__',
        SCR_PATH / 'CSS',
        SCR_PATH / 'JS'
    ]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            print(f"📁 Creating directory: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # Fix 2: Fix virtual environment
    venv_python = VENV / 'bin' / 'python'
    if not venv_python.exists():
        venv_python = VENV / 'Scripts' / 'python.exe'
    
    if not venv_python.exists():
        fix_venv()
    
    # Fix 3: Fix settings
    if not SETTINGS_PATH.exists():
        fix_settings()
    
    print("✅ Automatic fixes completed!")

def main():
    """Main diagnostic function."""
    
    issues, fixes = check_environment()
    
    if issues:
        print(f"\n❓ Would you like to run automatic fixes? (y/n)")
        response = input().strip().lower()
        
        if response in ['y', 'yes']:
            run_fixes()
            print(f"\n🔍 Re-running diagnostics...")
            issues, fixes = check_environment()
            
            if not issues:
                print(f"\n🎉 All issues fixed!")
            else:
                print(f"\n⚠️ Some issues remain - manual intervention may be required")
        else:
            print("Manual fixes required. Please follow the suggested fixes above.")
    
    print(f"\n💡 Next steps:")
    print("1. Run Cell 1 (Setup) if not already done")
    print("2. Run Cell 2 (Widgets) to configure your setup")
    print("3. Run Cell 3 (Download) to install WebUI and models")
    print("4. Run Cell 4 (Launch) to start your WebUI")

if __name__ == "__main__":
    main()
