"""
Script Scraper Data X / Twitter
Dibuat untuk tugas/project analisis media sosial.
Dapat dijalankan langsung dengan Python standard library tanpa perlu library eksternal.
"""

import json
import csv
import re
import urllib.request
import urllib.error
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def extract_tweet_info_from_url(url: str):
    """
    Ekstrak username dan tweet_id dari URL X/Twitter.
    Contoh: https://x.com/ejaaipongg/status/2108384969894842817
    """
    url = url.strip()
    pattern = r"(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)/status/([0-9]+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Format URL tidak valid: {url}")
    return match.group(1), match.group(2)

def scrape_tweet(url: str) -> dict:
    username, tweet_id = extract_tweet_info_from_url(url)
    api_url = f"https://api.fxtwitter.com/{username}/status/{tweet_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    req = urllib.request.Request(api_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Gagal mengambil data dari API (HTTP {e.code}): {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Terjadi kesalahan saat fetching: {e}")
        
    if res_data.get("code") != 200 or "tweet" not in res_data:
        raise RuntimeError(f"Respons tidak valid atau tweet tidak ditemukan: {res_data.get('message')}")
        
    tweet = res_data["tweet"]
    author = tweet.get("author", {})
    
    media_items = []
    if "media" in tweet and "all" in tweet["media"]:
        for m in tweet["media"]["all"]:
            media_items.append({
                "type": m.get("type"),
                "url": m.get("url"),
                "thumbnail_url": m.get("thumbnail_url"),
                "duration": m.get("duration")
            })

    structured_data = {
        "tweet_id": tweet.get("id"),
        "tweet_url": tweet.get("url"),
        "created_at": tweet.get("created_at"),
        "created_timestamp": tweet.get("created_timestamp"),
        "text": tweet.get("text"),
        "lang": tweet.get("lang"),
        "views": tweet.get("views"),
        "likes": tweet.get("likes"),
        "retweets": tweet.get("retweets"),
        "quotes": tweet.get("quotes"),
        "replies": tweet.get("replies"),
        "bookmarks": tweet.get("bookmarks"),
        "author_name": author.get("name"),
        "author_username": author.get("screen_name"),
        "author_id": author.get("id"),
        "author_description": author.get("description"),
        "author_location": author.get("location"),
        "author_followers": author.get("followers"),
        "author_following": author.get("following"),
        "author_verified": author.get("verification", {}).get("verified") if isinstance(author.get("verification"), dict) else False,
        "author_avatar_url": author.get("avatar_url"),
        "media_count": len(media_items),
        "media_urls": [m["url"] for m in media_items if m.get("url")]
    }
    
    return {
        "structured": structured_data,
        "raw": tweet,
        "media_list": media_items
    }

def save_to_json(data, filepath: str = "hasil_scrape.json"):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Data disimpan ke JSON: {filepath}")

def save_to_csv(data_list, filepath: str = "hasil_scrape.csv"):
    if not data_list:
        return
    if isinstance(data_list, dict):
        data_list = [data_list]
        
    rows = []
    for item in data_list:
        row = dict(item)
        if isinstance(row.get("media_urls"), list):
            row["media_urls"] = "; ".join(row["media_urls"])
        rows.append(row)
        
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Data disimpan ke CSV: {filepath}")

def download_media_files(media_urls, folder: str = "downloads"):
    os.makedirs(folder, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0"}
    for idx, url in enumerate(media_urls, 1):
        ext = ".mp4" if ".mp4" in url else ".jpg"
        clean_url = url.split("?")[0]
        filename = os.path.basename(clean_url)
        if not filename.endswith(ext):
            filename = f"media_{idx}{ext}"
        filepath = os.path.join(folder, filename)
        print(f"Mengunduh media {idx} -> {filepath}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as resp, open(filepath, "wb") as out:
                out.write(resp.read())
            print(f"Berhasil mengunduh: {filepath}")
        except Exception as e:
            print(f"Gagal mengunduh {url}: {e}")

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://x.com/ejaaipongg/status/2108384969894842817"
    print(f"Memulai scraping untuk URL: {target_url}...")
    
    try:
        result = scrape_tweet(target_url)
        save_to_json(result["raw"], "hasil_scrape_raw.json")
        save_to_json(result["structured"], "hasil_scrape.json")
        save_to_csv(result["structured"], "hasil_scrape.csv")
        
        print("\n" + "="*60)
        print("HASIL SCRAPING TWEET:")
        print("="*60)
        s = result["structured"]
        print(f"Author        : {s['author_name']} (@{s['author_username']})")
        print(f"Followers     : {s['author_followers']:,}")
        print(f"Lokasi        : {s['author_location']}")
        print(f"Waktu Dibuat  : {s['created_at']}")
        print(f"Statistik     : {s['views']:,} Views | {s['likes']:,} Likes | {s['retweets']:,} Retweets | {s['replies']:,} Replies | {s['quotes']:,} Quotes | {s['bookmarks']:,} Bookmarks")
        print("-" * 60)
        print("Isi Tweet / Konten:")
        print(s['text'])
        print("-" * 60)
        print(f"Lampiran Media ({s['media_count']} file):")
        for idx, m_url in enumerate(s['media_urls'], 1):
            print(f"  [{idx}] {m_url}")
        print("="*60)
        
        # Opsi unduh media jika ada argumen --download
        if "--download" in sys.argv:
            download_media_files(s['media_urls'])
            
    except Exception as err:
        print(f"Error: {err}")
