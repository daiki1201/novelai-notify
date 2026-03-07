import requests
import xml.etree.ElementTree as ET
import json
import os

RSS_URL = "https://blog.novelai.net/feed"
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
LAST_FILE = "last_entry.json"


def get_latest_entry():
    response = requests.get(RSS_URL, timeout=10)
    root = ET.fromstring(response.content)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    # Medium RSSはitem要素を使う
    channel = root.find("channel")
    item = channel.find("item")
    if item is None:
        return None

    title = item.findtext("title", "")
    link = item.findtext("link", "")
    pub_date = item.findtext("pubDate", "")
    return {"title": title, "link": link, "pub_date": pub_date}


def load_last():
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, "r") as f:
            return json.load(f)
    return None


def save_last(entry):
    with open(LAST_FILE, "w") as f:
        json.dump(entry, f)


def send_line_message(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": text}],
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"LINE送信エラー: {response.status_code} {response.text}")
    else:
        print("LINE通知送信成功")


def main():
    latest = get_latest_entry()
    if latest is None:
        print("記事取得失敗")
        return

    last = load_last()

    if last is None:
        # 初回実行時は現在の最新記事を保存するだけ
        save_last(latest)
        print(f"初回実行: {latest['title']} を記録しました")
        return

    if latest["link"] != last["link"]:
        # 新しい記事が投稿された
        text = f"【NovelAI新着記事】\n{latest['title']}\n{latest['link']}"
        send_line_message(text)
        save_last(latest)
    else:
        print("新しい記事なし")


if __name__ == "__main__":
    main()
