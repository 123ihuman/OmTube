import subprocess
import os
import urllib.request
import json
import glob

# 🔥 MAGIC: Find all files ending in _channels.txt in the repo
channel_files = glob.glob('*_channels.txt')
all_sql = []

for file_path in channel_files:
    # Extract the app name from the filename (e.g., "islamtube_channels.txt" -> "islamtube")
    app_tag = file_path.replace('_channels.txt', '').strip().lower()
    
    with open(file_path, 'r') as f:
        channels = [line.strip() for line in f if line.strip()]

    for ch in channels:
        url = f"https://www.youtube.com/channel/{ch}/videos"
        try:
            result = subprocess.run(
                ['yt-dlp', '--flat-playlist', '--playlist-end', '3', '--print', '%(id)s|%(title)s', url],
                capture_output=True, text=True, timeout=15
            )
            for line in result.stdout.strip().split('\n'):
                if '|' in line:
                    vid, title = line.split('|', 1)
                    # Tag dynamically based on the filename
                    title = f"[{app_tag}] " + title.replace("'", "''")
                    all_sql.append(f"('{vid}', '{title}')")
        except Exception:
            pass

if all_sql:
    sql_statements = ""
    for i in range(0, len(all_sql), 50):
        batch = all_sql[i:i+50]
        sql_statements += "INSERT OR REPLACE INTO videos (video_id, title) VALUES " + ", ".join(batch) + ";\n"
    
    ACCOUNT_ID = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
    API_TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN')
    DATABASE_ID = os.environ.get('DATABASE_ID')
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/d1/database/{DATABASE_ID}/query"
    data = json.dumps({"sql": sql_statements}).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {API_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req) as response:
            print("✅ Successfully uploaded auto-updated videos for ALL apps!")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
