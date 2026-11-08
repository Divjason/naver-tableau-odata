
import os
import requests
import xml.etree.ElementTree as ET

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 1. API 주소
URL = "https://naverapihub.apigw.ntruss.com/search/v1/blog"

# 2. 인증 정보
headers = {
    "X-NCP-APIGW-API-KEY-ID": os.getenv("X-NCP-APIGW-API-KEY-ID"),
    "X-NCP-APIGW-API-KEY": os.getenv("X-NCP-APIGW-API-KEY")
}

if not all(headers.values()):
    raise ValueError("NCP API 인증키를 확인하세요.")

# 3. 검색 조건
params = {
    "query": "인공지능",
    "display": 100,
    "start": 1,
    "sort": "date",
    "format": "xml"
}

# 4. API 요청
response = requests.get(
    URL,
    headers=headers,
    params=params,
    timeout=20
)

response.raise_for_status()

# 5. XML 유효성 확인
root = ET.fromstring(response.content)

# 6. XML 파일 저장
path = Path("data/naver_blog.xml")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_bytes(response.content)

# 7. 결과 확인
items = root.findall("./channel/item")

print("HTTP 상태:", response.status_code)
print("수집 건수:", len(items))
print("저장 위치:", path.resolve())

for item in items[:3]:
    print({
        "title": item.findtext("title"),
        "bloggername": item.findtext("bloggername"),
        "postdate": item.findtext("postdate")
    })
