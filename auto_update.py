import subprocess
import os
import urllib.request
import json

def fetch_videos(channel_file, app_tag):
    if not os.path.exists(channel_file): return []
    with open(channel_file, 'r') as f:
        channels = [line.strip() for line in f if line.strip()]

    sql_values = []
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
                    # 🔥 Add the Tag to the title!
                    title = f"[{app_tag}] " + title.replace("'", "''")
                    sql_values.append(f"('{vid}', '{title}')")
        except Exception:
            pass
    return sql_values

# 1. Fetch for OmTube
omtube_sql = fetch_videos('omtube_channels.txt', 'omtube')

# 2. Fetch for ProTube
protube_sql = fetch_videos('protube_channels.txt', 'protube')

# 3. Combine and Upload
all_sql = omtube_sql + protube_sql

if all_sql:
    sql = "INSERT OR IGNORE INTO videos (video_id, title) VALUES " + ", ".join(all_sql) + ";"
    
    ACCOUNT_ID = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
    API_TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN')
    DATABASE_ID = os.environ.get('DATABASE_ID')
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/d1/database/{DATABASE_ID}/query"
    data = json.dumps({"sql": sql}).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {API_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req) as response:
            print("✅ Successfully uploaded tagged videos to Cloudflare!")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
