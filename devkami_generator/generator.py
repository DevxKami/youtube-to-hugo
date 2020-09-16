import argparse
import os
import shelve

from dateutil.parser import parse
from googleapiclient.discovery import build
from slugify import slugify

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


def fetch_video(developer_key):
    youtube = build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        developerKey=developer_key,
    )
    # Initial query
    search_response = youtube.search().list(
        q="",
        part="id,snippet",
        channelId="UCMs8l2DQ7S6tiBDBSn_4isA",
        maxResults=10,
        order="date",
    ).execute()
    db = shelve.open("post.db")

    while True:
        next_page = search_response.get("nextPageToken")
        for result in search_response.get("items", []):
            if result["id"]["kind"] == "youtube#video":
                post_id = result["id"]["videoId"]
                # Let's not regen old file
                if post_id not in db:
                    title = result["snippet"]["title"]
                    publish_time = parse(result["snippet"]["publishTime"])
                    content = create_post(title, publish_time, post_id)
                    db[post_id] = content

        if next_page:
            search_response = youtube.search().list(
                q="",
                part="id,snippet",
                channelId="UCMs8l2DQ7S6tiBDBSn_4isA",
                maxResults=10,
                order="date",
                pageToken=next_page,
            ).execute()
        else:
            break


def create_post(title, publish_time, video_id):

    content = f'---\ntitle: "{title.replace("#","")}"\ndate: {publish_time}\nyoutubeid: "{video_id}"\n---'
    slug = slugify(title)
    filename = f"{publish_time.day:02}-{slug}.md"
    year_path = f"content/{publish_time.year}"
    if not os.path.exists(year_path):
        os.makedirs(year_path)
    month_path = os.path.join(year_path, str(publish_time.month).zfill(2))
    if not os.path.exists(month_path):
        os.makedirs(month_path)
    full_path = os.path.join(month_path, filename)
    with open(full_path, "w") as f:
        f.write(content)
    return content


def main():
    parser = argparse.ArgumentParser(description='Create devkami markdown')
    parser.add_argument('api_key', help='youtube data api key')
    args = parser.parse_args()
    fetch_video(args.api_key)


if __name__ == "__main__":
    main()

