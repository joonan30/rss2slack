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

# 이전에 전송한 링크를 저장할 파일 경로
sent_links_file = "sent_links.txt"

# 이전에 전송한 링크 로드
def load_sent_links():
    if os.path.exists(sent_links_file):
        with open(sent_links_file, "r") as file:
            return set(line.strip() for line in file)
    return set()

# 새로운 링크를 기록
def save_sent_link(link):
    with open(sent_links_file, "a") as file:
        file.write(link + "\n")

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
    # "https://www.nature.com/nature.rss",
    # "https://www.nature.com/nm.rss",
    # "http://www.nature.com/neuro/current_issue/rss/",
    # "http://www.nature.com/nrg/journal/vaop/ncurrent/rss.rdf",
    # "http://www.nature.com/nrn/current_issue/rss",
    # "https://www.science.org/action/showFeed?type=axatoc&feed=rss&jc=science",
    # "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=stm",
    # "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv",
    # "https://genomebiology.biomedcentral.com/articles/most-recent/rss.xml",
    # "https://genomemedicine.biomedcentral.com/articles/most-recent/rss.xml",
    # "https://www.nature.com/natmachintell.rss",
    # "https://jamanetwork.com/rss/site_3/onlineFirst_67.xml",
    # "https://jamanetwork.com/rss/site_214/187.xml",
    # "https://jamanetwork.com/rss/site_14/onlineFirst_70.xml",
    # "https://jamanetwork.com/rss/site_16/onlineFirst_72.xml",
    # "https://www.cell.com/cell/inpress.rss",
    # "https://www.cell.com/cell-reports/inpress.rss",
    # "http://www.cell.com/ajhg/inpress.rss",
    # "https://www.embopress.org/feed/17444292/most-recent",
    # "https://www.nature.com/mp.rss",
    # "http://www.nature.com/nbt/current_issue/rss/",
    # "https://www.cell.com/neuron/inpress.rss",
    # "http://www.nature.com/ng/current_issue/rss/",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=cancer_biology",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=bioinformatics",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=genetics",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=genomics",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=molecular_biology",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=neuroscience",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=synthetic_biology",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=bioinformatics",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=cancer_biology",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=developmental_biology",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=genetics",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=genomics",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=molecular_biology",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=neuroscience",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=systems_biology",
    "http://hwmaint.biorxiv.highwire.org/cgi/collection/rss?coll_alias=synthetic_biology"
]

# 이전에 전송한 링크 로드
sent_links = load_sent_links()

# 각 RSS 피드를 반복하여 조건에 맞는 경우만 요약 및 슬랙 전송
for feed_url in feed_urls:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:100]:  # 피드에서 최대 5개 항목 요약
        # 이전에 전송한 링크 제외
        if entry.link in sent_links:
            print(f"Already sent: {entry.link}")
            continue
        
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
            
            # 전송한 링크를 파일에 기록하고 집합에도 추가
            save_sent_link(entry.link)
            sent_links.add(entry.link)
