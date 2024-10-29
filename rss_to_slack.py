import feedparser
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

# 환경 변수에서 API 키 가져오기
openai.api_key = os.getenv("OPENAI_API_KEY")
slack_token = os.getenv("SLACK_BOT_TOKEN")

# 텍스트 요약 함수
def summarize_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # gpt-4 모델을 사용
        messages=[{"role": "user", "content": f"Summarize this article: {text}"}],
        max_tokens=100  # 원하는 요약 길이에 맞게 조정
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

# 여러 RSS 피드 URL 목록
feed_urls = [
    "https://www.nature.com/ncomms.rss"
]

# 각 RSS 피드를 반복하여 요약하고 슬랙에 전송
for feed_url in feed_urls:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:5]:  # 피드에서 최대 5개 항목 요약
        summary = summarize_text(entry.summary)
        message = f"*{entry.title}*\n{summary}\n<{entry.link}>"
        send_to_slack("#your-slack-channel", message)
