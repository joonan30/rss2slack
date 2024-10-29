import feedparser
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
import re

# 환경 변수에서 API 키 가져오기
openai.api_key = os.getenv("OPENAI_API_KEY")
slack_token = os.getenv("SLACK_BOT_TOKEN")

# 슬랙 클라이언트 초기화
client = WebClient(token=slack_token)

# 필터링할 키워드 목록 (OR 조건)
keywords = [
    "single cell atlas",
    "autism",
    "whole genome sequencing",
    "deep learning genomics",
    "oligogenic",
    "foundation model genomics"
]

# 제외할 제목 키워드 목록
exclude_titles = ["Author Correction", "Publisher Correction"]

# 키워드 필터링 함수 (OR 조건으로 검색)
def contains_keywords(text, keywords):
    pattern = '|'.join([re.escape(keyword) for keyword in keywords])  # 키워드를 OR 조건으로 결합
    return re.search(pattern, text, re.IGNORECASE)  # 대소문자 구분 없이 검색

# 제외 제목 필터링 함수
def should_exclude(title, exclude_titles):
    return any(excluded in title for excluded in exclude_titles)

# 텍스트 요약 함수
def summarize_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # gpt-4 모델을 사용해도 됨
        messages=[{"role": "user", "content": f"Summarize this article: {text}"}],
        max_tokens=100  # 원하는 요약 길이에 맞게 조정
    )
    return response['choices'][0]['message']['content'].strip()

# 슬랙 메시지 보내기 함수
def send_to_slack(channel, message):
    try:
        client.chat_postMessage(
            channel=channel,
            text=message
        )
        print(f"Message sent to {channel}")
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

# RSS 피드 URL 목록
feed_urls = [
    "https://www.nature.com/ncomms.rss"
]

# 각 RSS 피드를 반복하여 조건에 맞는 경우만 요약 및 슬랙 전송
for feed_url in feed_urls:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:30]:  # 피드에서 최대 30개 항목 요약
        # 제목 제외 조건 검사
        if should_exclude(entry.title, exclude_titles):
            print(f"Excluded: {entry.title}")
            continue  # 제외 조건에 해당하는 경우 건너뜀
        
        # 키워드 포함 여부 확인
        content = entry.title + " " + entry.summary
        if contains_keywords(content, keywords):
            summary = summarize_text(entry.summary)
            message = f"*{entry.title}*\n{summary}\n<{entry.link}>"
            send_to_slack("#paper_gpt", message)
