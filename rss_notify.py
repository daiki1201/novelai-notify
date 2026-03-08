import requests
import xml.etree.ElementTree as ET
import json
import os

RSS_URL = "https://blog.novelai.net/feed"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
LAST_FILE = "last_entry.json"


def get_latest_entry():
    response = requests.get(RSS_URL, timeout=10, allow_redirects=True)
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


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print(f"Telegram送信エラー: {response.status_code} {response.text}")
    else:
        print("Telegram通知送信成功")


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
        send_telegram_message(text)
        save_last(latest)
    else:
        print("新しい記事なし")


if __name__ == "__main__":
    main()
