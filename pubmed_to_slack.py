import feedparser
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
from datetime import datetime, timedelta

# 환경 변수에서 API 키 가져오기
openai.api_key = os.getenv("OPENAI_API_KEY")
slack_token = os.getenv("SLACK_BOT_TOKEN")

# 슬랙 클라이언트 초기화
client = WebClient(token=slack_token)

# 논문이 발행된 저널 목록
desired_journals = [
    "Nature", "Nature Neuroscience", "Nature neuroscience", "Nature Genetics", "Nature genetics",
    "Nature Medicine", "Nature medicine", "Nature Human Behaviour", "Nature human behaviour",
    "Nature Methods", "Nature methods", "Nature Communications", "Nature communications",
    "Cell", "Cell Genomics", "Cell genomics", "Science",
    "Neuron", "Molecular Psychiatry", "Molecular psychiatry",
    "Clinical and Translational Medicine", "Clinical and translational medicine",
    "Bioinformatics", "Nucleic Acids Research", "Nucleic acids research",
    "American Journal of Human Genetics", "American journal of human genetics",
    "Genome Medicine", "Genome medicine", "Genome Biology", "Genome biology",
    "Molecular Systems Biology", "Molecular systems biology",
    "Biological Psychiatry", "Biological psychiatry",
    "Experimental & Molecular Medicine", "Experimental & molecular medicine",
    "eLife", "Genome Research", "Genome research"
]


# Case variations for filtering
desired_journals += [j.lower() for j in desired_journals] + [j.title() for j in desired_journals]

# 저널 이름 필터링 함수
def is_desired_journal(journal):
    return journal.lower() in [j.lower() for j in desired_journals]

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

# Generate the fc parameter for "one day before today" in the required format (YYYYMMDD000000)
one_day_before_today = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d000000")

# PubMed RSS URL with dynamically generated `fc` parameter
pubmed_feed_url = f"https://pubmed.ncbi.nlm.nih.gov/rss/search/1L5AT7N6rGvNm3bNUYYgVpD9oT1Tnt8pGPHbVFDktkUWfV853n/?limit=100&utm_campaign=pubmed-2&fc={one_day_before_today}"

# PubMed RSS 피드 파싱 및 처리
feed = feedparser.parse(pubmed_feed_url)
for entry in feed.entries:
    # 저널 필터링: 지정한 저널 목록에 포함되지 않으면 제외
    journal = entry.get("dc:source", "")
    if not is_desired_journal(journal):
        print(f"Excluded (not desired journal): {journal} - {entry.title}")
        continue

    # 초록을 요약 텍스트로 사용
    abstract = entry.get("description", entry.get("content:encoded", ""))
    summary_text = abstract if abstract else entry.get("summary", "")
    summary = summarize_text(summary_text)
    
    # 슬랙으로 메시지 전송
    message = f"*{entry.title}*\n{summary}\n<{entry.link}>"
    send_to_slack("#paper_gpt", message)
