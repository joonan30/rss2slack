import feedparser
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

# 환경 변수에서 API 키 가져오기
openai.api_key = os.getenv("OPENAI_API_KEY")
slack_token = os.getenv("SLACK_BOT_TOKEN")

def summarize_text(text):
    response = openai.Completion.create(
        model="gpt-4",
        prompt=f"Summarize this: {text}",
        max_tokens=50
    )
    return response.choices[0].text.strip()

def send_to_slack(channel, message):
    client = WebClient(token=slack_token)
    try:
        response = client.chat_postMessage(
            channel=channel,
            text=message
        )
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

# 여러 RSS 피드 요약 및 전송
feed_urls = [
    "https://www.nature.com/ncomms.rss"
]

for feed_url in feed_urls:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:5]:  # 각 피드에서 5개 항목을 요약
        summary = summarize_text(entry.summary)
        message = f"*{entry.title}*\n{summary}"
        send_to_slack("#your-slack-channel", message)
