import uvicorn
import os
import sys

if __name__ == "__main__":
    print("----------------------------------------------------------------")
    print("🚀 STARTING BACKEND SERVER...")
    print(f"📂 Current Directory: {os.getcwd()}")
    print(f"🐍 Python Executable: {sys.executable}")
    print("----------------------------------------------------------------")
    
    try:
        # Check if main.py exists
        if not os.path.exists("main.py"):
            print("❌ ERROR: main.py not found! Are you in the 'backend' folder?")
        else:
            # Run the server directly
            uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
            
    except ImportError as e:
        print(f"❌ LIBRARY ERROR: {e}")
        print("👉 Run: pip install fastapi uvicorn langchain langchain-community chromadb")
    except Exception as e:
        print(f"❌ UNKNOWN ERROR: {e}")