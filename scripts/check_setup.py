import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    print("Checking project setup...")
    print("Python version:", sys.version)
    
    required_dirs = ["data/raw", "data/sampled", "configs", "src", "scripts"]
    print("\nDirectory check:")
    for dir_name in required_dirs:
        path = ROOT / dir_name
        status = "OK" if path.exists() else "MISSING"
        print(f"{status}: {dir_name}")
        
    print("\nSetup check complete!")

if __name__ == "__main__":
    main()

