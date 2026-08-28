"""
Fetches the public YouTube RSS feed for the FrankenOrg playlist and writes
the latest episodes to assets/episodes.json for the site to render.

No API key required — this uses YouTube's public Atom feed:
https://www.youtube.com/feeds/videos.xml?playlist_id=<PLAYLIST_ID>
"""
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

PLAYLIST_ID = "PLMADD-VEXGwY"
FEED_URL = f"https://www.youtube.com/feeds/videos.xml?playlist_id={PLAYLIST_ID}"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "episodes.json"
MAX_EPISODES = 6

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


def fetch_feed() -> bytes:
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def parse_feed(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    episodes = []

    for entry in root.findall("atom:entry", NS):
        video_id = entry.findtext("yt:videoId", default="", namespaces=NS)
        title = entry.findtext("atom:title", default="", namespaces=NS)
        published = entry.findtext("atom:published", default="", namespaces=NS)

        link_el = entry.find("atom:link", NS)
        url = (
            link_el.get("href")
            if link_el is not None
            else f"https://www.youtube.com/watch?v={video_id}"
        )

        thumbnail = ""
        description = ""
        group = entry.find("media:group", NS)
        if group is not None:
            thumb_el = group.find("media:thumbnail", NS)
            if thumb_el is not None:
                thumbnail = thumb_el.get("url", "")
            desc_el = group.find("media:description", NS)
            if desc_el is not None and desc_el.text:
                description = desc_el.text.strip()

        episodes.append(
            {
                "videoId": video_id,
                "title": title,
                "url": url,
                "published": published,
                "thumbnail": thumbnail,
                "description": description[:180],
            }
        )

    episodes.sort(key=lambda e: e["published"], reverse=True)
    return episodes[:MAX_EPISODES]


def main() -> None:
    xml_bytes = fetch_feed()
    episodes = parse_feed(xml_bytes)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(episodes, indent=2), encoding="utf-8")
    print(f"Wrote {len(episodes)} episodes to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
