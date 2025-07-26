import argparse, os, subprocess
from pathlib import Path

SCRIPTS = ["widgets-en.py",
           "downloading-en.py", 
           "launch.py"]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--branch", default="main")
    args = p.parse_args()
    
    # Use /content instead of /root for Colab compatibility
    home = Path("/content")
    # Put everything directly in scripts/ folder (no en/ subdirectory)
    dst = home / "ANXETY" / "scripts"
    os.makedirs(dst, exist_ok=True)
    
    # Base URL points directly to scripts/ folder (no en/ subfolder)
    base = f"https://raw.githubusercontent.com/remphanstar/LightningSdaigen/{args.branch}/scripts"
    
    print(f"Downloading {len(SCRIPTS)} scripts to {dst}...")
    failed_downloads = []
    
    for f in SCRIPTS:
        url = f"{base}/{f}"
        print(f"Downloading {f}...")
        try:
            result = subprocess.run(["curl", "-sLo", str(dst/f), url], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ {f} downloaded successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to download {f}: {e}")
            failed_downloads.append(f)
    
    if failed_downloads:
        print(f"\n❌ Failed to download {len(failed_downloads)} files:")
        for f in failed_downloads:
            print(f"  - {f}")
        print(f"✅ Successfully downloaded {len(SCRIPTS) - len(failed_downloads)}/{len(SCRIPTS)} files")
    else:
        print(f"✅ All {len(SCRIPTS)} files downloaded successfully!")
    
    # Set environment variable for other scripts to find the base path
    os.environ["scr_path"] = str(home / "ANXETY")
    print(f"Environment variable scr_path set to: {os.environ['scr_path']}")

if __name__ == "__main__":
    main()
