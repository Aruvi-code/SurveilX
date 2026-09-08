"""
SurveilX — Public Hosting Script (localhost.run)
=================================================
Run this script to:
1. Start the SurveilX server
2. Create a FREE public tunnel via localhost.run
3. Get a shareable URL for friends/mentors

Usage:
    python host.py

No signup needed! No installation needed! Just run it.
"""
import subprocess
import sys
import time
import threading
import re

def start_server():
    """Start the SurveilX FastAPI server"""
    print("\n" + "=" * 60)
    print("🚀 SurveilX Server Starting...")
    print("=" * 60)
    server = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=".",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(5)  # Wait for server + AI models to load
    print("✅ Server ready on http://localhost:5000")
    return server

def start_tunnel():
    """Create SSH tunnel via localhost.run (free, no signup)"""
    print("\n🌐 Creating public tunnel (localhost.run)...")
    print("   No signup needed — completely free!\n")
    
    tunnel = subprocess.Popen(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:5000", "nokey@localhost.run"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    
    # Read the public URL from tunnel output
    for line in iter(tunnel.stdout.readline, ''):
        line = line.strip()
        if line:
            print(f"   {line}")
        # Look for the URL
        url_match = re.search(r'(https://[a-zA-Z0-9\-]+\.lhr\.life\S*)', line)
        if not url_match:
            url_match = re.search(r'(https://[a-zA-Z0-9\-]+\.localhost\.run\S*)', line)
        if url_match:
            public_url = url_match.group(1)
            print("\n" + "=" * 60)
            print("🎉 SurveilX is LIVE! Share this URL:")
            print(f"\n   👉  {public_url}")
            print(f"\n📱 Phone browser-la open pannunga!")
            print(f"💻 PC-la same localhost:5000 la work aagum")
            print(f"\n📤 WhatsApp/Telegram-la share pannunga!")
            print("=" * 60)
            print("\n⚠️  Stop panna: Ctrl+C press pannunga\n")
            break
    
    return tunnel

if __name__ == "__main__":
    server = None
    tunnel = None
    try:
        # Step 1: Start SurveilX
        server = start_server()
        
        # Step 2: Create tunnel
        tunnel = start_tunnel()
        
        # Keep running
        if tunnel:
            tunnel.wait()
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down SurveilX...")
        if tunnel:
            tunnel.terminate()
        if server:
            server.terminate()
        print("✅ Done. Bye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if server:
            server.terminate()
