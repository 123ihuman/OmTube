import subprocess
import requests
import json
import re
import time

# 🔥 YOUR CLOUDFLARE DETAILS
ACCOUNT_ID = "5e8795133a1609ed5afdafa6bc040751"
DATABASE_ID = "e9e8f7ad-f6a6-4456-aa87-29f01d1eec90"
API_TOKEN = "cfut_0Ts9feAEdYyMKjJL5AIeOojkUWF0kXQIg8M2T5FE412358ac"

CHANNELS_FILE = "all_new_channels.txt"

def get_latest_videos(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}"
    try:
        # Grabs the 10 newest videos
        result = subprocess.run(
            ['yt-dlp', '--flat-playlist', '--playlist-end', '10', '--print', '%(id)s|%(title)s', url],
            capture_output=True, text=True, timeout=60
        )
        return result.stdout.strip().split('\n')
    except:
        return []

def push_to_cloudflare(sql_query):
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/d1/database/{DATABASE_ID}/query"
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    data = {"sql": sql_query}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def main():
    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    sql_values = []
    for line in lines:
        id_match = re.search(r'(UC[a-zA-Z0-9_-]{22})', line)
        if not id_match: continue
        channel_id = id_match.group(1)
        channel_name = line.replace(channel_id, '').strip()

        videos = get_latest_videos(channel_id)
        for v in videos:
            if '|' in v:
                vid_id, title = v.split('|', 1)
                safe_title = title.replace("'", "''")
                # Tag for Study Tube AND YouTube Pro
                full_title = f"[studytube] [protube] [ch:{channel_name}] {safe_title}"
                sql_values.append(f"('{vid_id}', '{full_title}')")
        
        # 1 second delay between channels to avoid YouTube blocks
        time.sleep(1)

    if sql_values:
        for i in range(0, len(sql_values), 50):
            batch = sql_values[i:i+50]
            sql = "INSERT OR IGNORE INTO videos (video_id, title) VALUES " + ", ".join(batch) + ";"
            print(push_to_cloudflare(sql))
        print(f"✅ Pushed {len(sql_values)} new videos to Cloudflare.")
    else:
        print("No new videos found.")

if __name__ == "__main__":
    main()
