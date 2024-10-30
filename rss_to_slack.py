import feedparser
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
import re
from datetime import datetime, timedelta

# 환경 변수에서 API 키 가져오기
openai.api_key = os.getenv("OPENAI_API_KEY")
slack_token = os.getenv("SLACK_BOT_TOKEN")

# 슬랙 클라이언트 초기화
client = WebClient(token=slack_token)

# 필터링할 키워드 목록 (OR 조건)
keywords = [
    "single cell atlas",
    "single cell",
    "multiomics",
    "foundation model",
    "whole-genome sequencing",
    "WGS",
    "proteogenomics",
    "single-cell RNA",
    "multiome",
    "CPTAC",
    "autism",
    "whole genome sequencing",
    "deep learning genomics",
    "oligogenic",
    "polygenic",
    "deep learning model"
]

# 제외할 제목 키워드 목록
exclude_titles = ["Author Correction", "Publisher Correction"]

# 어제 날짜 생성
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

# 키워드 필터링 함수 (OR 조건으로 검색)
def contains_keywords(text, keywords):
    pattern = '|'.join([re.escape(keyword) for keyword in keywords])
    return re.search(pattern, text, re.IGNORECASE)

# 제외 제목 필터링 함수
def should_exclude(title, exclude_titles):
    return any(excluded in title for excluded in exclude_titles)

# 텍스트 요약 함수
def summarize_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"Summarize this article: {text}"}],
        max_tokens=200
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
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=cancer_biology",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=bioinformatics",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=genetics",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=genomics",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=molecular_biology",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=neuroscience",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=synthetic_biology",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=systems_biology"
]

# 각 RSS 피드를 반복하여 조건에 맞는 경우만 요약 및 슬랙 전송
for feed_url in feed_urls:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:100]:
        # 어제 날짜의 항목인지 확인
        entry_date = entry.get("date", "")
        if entry_date != yesterday:
            print(f"Skipped (not yesterday's entry): {entry_date} - {entry.title}")
            continue

        # 제목 제외 조건 검사
        if should_exclude(entry.title, exclude_titles):
            print(f"Excluded: {entry.title}")
            continue

        # 키워드 포함 여부 확인
        content = entry.title + " " + entry.description
        if contains_keywords(content, keywords):
            summary = summarize_text(entry.description)
            message = f"*{entry.title}*\n{summary}\n<{entry.link}>"
            send_to_slack("#paper_gpt", message)
