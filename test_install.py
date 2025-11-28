
import sys
from playwright.__main__ import main

if __name__ == "__main__":
    print("Attempting to run playwright install...")
    try:
        sys.argv = ["playwright", "install", "chromium"]
        main()
        print("Install finished.")
    except SystemExit:
        print("SystemExit caught (expected from main)")
    except Exception as e:
        print(f"Error: {e}")
