import feedparser
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

# 환경 변수에서 API 키 가져오기
openai.api_key = os.getenv("OPENAI_API_KEY")
slack_token = os.getenv("SLACK_BOT_TOKEN")

# 텍스트 요약 함수 수정
def summarize_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # 또는 사용 가능한 모델 ID로 변경
        messages=[{"role": "user", "content": f"Summarize this: {text}"}],
        max_tokens=50
    )
    return response['choices'][0]['message']['content'].strip()

# 슬랙 메시지 보내기 함수
def send_to_slack(channel, message):
    client = WebClient(token=slack_token)
    try:
        client.chat_postMessage(
            channel=channel,
            text=message
        )
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

# 여러 RSS 피드 요약 및 전송
feed_urls = [
    "https://www.nature.com/ncomms.rss"
]

# 각 RSS 피드를 반복하여 요약하고 슬랙에 전송
for feed_url in feed_urls:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:5]:  # 각 피드에서 5개 항목을 요약
        summary = summarize_text(entry.summary)
        message = f"*{entry.title}*\n{summary}"
        send_to_slack("#your-slack-channel", message)
