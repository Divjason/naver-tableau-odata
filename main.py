# import re
# import json
# import html
# import xml.etree.ElementTree as ET

# from pathlib import Path
# from fastapi import FastAPI, Request, HTTPException
# from fastapi.responses import Response

# app = FastAPI(title="Naver Blog OData API")

# DATA_FILE = Path(__file__).parent / "data" / "naver_blog.xml"

# # 1. XML 파싱
# def load_blogs():
#     if not DATA_FILE.exists():
#         raise HTTPException(503, "XML data file not found")

#     root = ET.parse(DATA_FILE).getroot()
#     blogs = []

#     for index, item in enumerate(
#         root.findall("./channel/item"), 1
#     ):
#         title = item.findtext("title", "")
#         title = re.sub(r"<[^>]+>", "", html.unescape(title))

#         blogs.append({
#             "ID": index,
#             "Title": title,
#             "BloggerName": item.findtext("bloggername", ""),
#             "PostDate": item.findtext("postdate", ""),
#             "Link": item.findtext("link", "")
#         })

#     return blogs


# def base_url(request):
#     return str(request.base_url).rstrip("/") + "/odata/"


# def odata_json(data):
#     return Response(
#         content=json.dumps(data, ensure_ascii=False),
#         media_type="application/json",
#         headers={"OData-Version": "4.0"}
#     )


# # 2. 기본 서버 상태
# @app.get("/")
# def home():
#     return {
#         "status": "running",
#         "service": "/odata/",
#         "metadata": "/odata/$metadata",
#         "data": "/odata/Blogs"
#     }


# # 3. OData 서비스 루트
# @app.get("/odata/")
# def service_root(request: Request):
#     return odata_json({
#         "@odata.context": base_url(request) + "$metadata",
#         "value": [
#             {
#                 "name": "Blogs",
#                 "kind": "EntitySet",
#                 "url": "Blogs"
#             }
#         ]
#     })


# # 4. OData 메타데이터
# @app.get("/odata/$metadata")
# def metadata():
#     xml = """<?xml version="1.0" encoding="utf-8"?>
# <edmx:Edmx Version="4.0"
#  xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
#   <edmx:DataServices>
#     <Schema Namespace="Naver"
#       xmlns="http://docs.oasis-open.org/odata/ns/edm">

#       <EntityType Name="Blog">
#         <Key>
#           <PropertyRef Name="ID"/>
#         </Key>
#         <Property Name="ID"
#           Type="Edm.Int32" Nullable="false"/>
#         <Property Name="Title" Type="Edm.String"/>
#         <Property Name="BloggerName" Type="Edm.String"/>
#         <Property Name="PostDate" Type="Edm.String"/>
#         <Property Name="Link" Type="Edm.String"/>
#       </EntityType>

#       <EntityContainer Name="Container">
#         <EntitySet Name="Blogs"
#           EntityType="Naver.Blog"/>
#       </EntityContainer>

#     </Schema>
#   </edmx:DataServices>
# </edmx:Edmx>"""

#     return Response(
#         content=xml,
#         media_type="application/xml",
#         headers={"OData-Version": "4.0"}
#     )


# # 5. OData 데이터 조회
# @app.get("/odata/Blogs")
# def get_blogs(request: Request):
#     blogs = load_blogs()
#     params = request.query_params

#     # Tableau 및 일반 OData 클라이언트의 기본 조회 옵션
#     try:
#         skip = int(params.get("$skip", "0"))
#         top = int(params.get("$top", str(len(blogs))))
#     except ValueError:
#         raise HTTPException(400, "Invalid pagination")

#     if skip < 0 or top < 0:
#         raise HTTPException(400, "Invalid pagination")

#     total = len(blogs)

#     # 기본 정렬
#     orderby = params.get("$orderby")
#     if orderby:
#         parts = orderby.split()
#         field = parts[0]
#         if field not in blogs[0] if blogs else False:
#             raise HTTPException(400, "Unknown field")
#         if len(parts) > 2 or (
#             len(parts) == 2 and parts[1] not in ("asc", "desc")
#         ):
#             raise HTTPException(400, "Invalid orderby")
#         if blogs:
#             blogs.sort(
#                 key=lambda x: x[field],
#                 reverse=len(parts) == 2 and parts[1] == "desc"
#             )

#     blogs = blogs[skip:skip + top]

#     result = {
#         "@odata.context": base_url(request) + "$metadata#Blogs",
#         "value": blogs
#     }

#     if params.get("$count", "").lower() == "true":
#         result["@odata.count"] = total

#     return odata_json(result)


# # 6. 전체 건수
# @app.get("/odata/Blogs/$count")
# def count_blogs():
#     return Response(
#         content=str(len(load_blogs())),
#         media_type="text/plain",
#         headers={"OData-Version": "4.0"}
#     )


# # 7. 단일 게시물 조회
# @app.get("/odata/Blogs({blog_id})")
# def get_blog(blog_id: int, request: Request):
#     blog = next(
#         (b for b in load_blogs() if b["ID"] == blog_id),
#         None
#     )

#     if blog is None:
#         raise HTTPException(404, "Blog not found")

#     return odata_json({
#         "@odata.context": base_url(request) + "$metadata#Blogs/$entity",
#         **blog
#     })


# ============================================================
# Naver Blog XML → FastAPI → OData API
# ============================================================
#
# [프로젝트 목적]
#
# 1. 네이버 검색 API로 수집한 XML 파일을 읽는다.
# 2. XML 데이터를 Python 딕셔너리 형태로 변환한다.
# 3. FastAPI를 이용하여 HTTP API 서버를 구현한다.
# 4. OData 형식의 메타데이터와 JSON 데이터를 제공한다.
# 5. Tableau 등 OData 클라이언트에서 조회할 수 있도록 한다.
#
# [전체 데이터 흐름]
#
# Naver API
#     ↓
# collect.py (데이터 수집)
#     ↓
# data/naver_blog.xml (XML 파일 저장)
#     ↓
# main.py (XML 파싱 및 API 구현)
#     ↓
# FastAPI + Uvicorn (HTTP 서버)
#     ↓
# /odata/Blogs (OData JSON 응답)
#     ↓
# Tableau (데이터 연결 및 시각화)
#
# ============================================================


# ============================================================
# STEP 01. 라이브러리 및 모듈 불러오기
# ============================================================


# ------------------------------------------------------------
# 1. re : Regular Expression (정규표현식)
# ------------------------------------------------------------
#
# Python 표준 라이브러리
# 별도 설치 불필요
#
# [역할]
# 문자열에서 특정 패턴을 검색하거나 제거한다.
#
# [사용 목적]
# 네이버 블로그 제목에 포함된 HTML 태그를 제거한다.
#
# 예:
# "<b>파이썬</b> 강의"
#         ↓
# "파이썬 강의"
#
# 주요 함수:
# re.sub(패턴, 대체문자열, 원본문자열)
#
import re


# ------------------------------------------------------------
# 2. json : JavaScript Object Notation
# ------------------------------------------------------------
#
# Python 표준 라이브러리
# 별도 설치 불필요
#
# [역할]
# Python 데이터를 JSON 문자열로 변환한다.
#
# [사용 목적]
# Python 딕셔너리를 HTTP 응답용 JSON으로 변환한다.
#
# 주요 함수:
# json.dumps() : Python → JSON 문자열
# json.loads() : JSON 문자열 → Python
#
import json


# ------------------------------------------------------------
# 3. html : HTML 처리 모듈
# ------------------------------------------------------------
#
# Python 표준 라이브러리
# 별도 설치 불필요
#
# [역할]
# HTML 특수문자 및 엔티티를 처리한다.
#
# 예:
# "&amp;" → "&"
# "&lt;"  → "<"
# "&gt;"  → ">"
#
# 주요 함수:
# html.unescape()
#
# [사용 목적]
# 네이버 API에서 반환한 제목의 HTML 엔티티를
# 사람이 읽을 수 있는 일반 문자로 변환한다.
#
import html


# ------------------------------------------------------------
# 4. xml.etree.ElementTree
# ------------------------------------------------------------
#
# Python 표준 라이브러리
# 별도 설치 불필요
#
# XML = Extensible Markup Language
#
# [역할]
# XML 문서를 읽고 계층 구조를 탐색한다.
#
# [사용 목적]
# 네이버 블로그 XML 파일에서
# title, bloggername, postdate, link 등을 추출한다.
#
# 주요 함수:
# ET.parse()  : XML 파일 읽기
# getroot()   : XML 최상위 요소 가져오기
# findall()   : 조건에 맞는 XML 요소 검색
# findtext()  : XML 요소의 텍스트 추출
#
# as ET:
# 긴 모듈 이름 대신 ET라는 별칭을 사용한다.
#
import xml.etree.ElementTree as ET


# ------------------------------------------------------------
# 5. pathlib.Path
# ------------------------------------------------------------
#
# Python 표준 라이브러리
# 별도 설치 불필요
#
# [역할]
# 파일 및 폴더 경로를 객체 방식으로 관리한다.
#
# [사용 목적]
# Mac, Windows 등 운영체제에 관계없이
# XML 파일의 경로를 지정한다.
#
# 주요 기능:
# Path(__file__) : 현재 Python 파일의 경로
# .parent        : 상위 폴더
# .exists()      : 파일 존재 여부 확인
#
# / 연산자:
# Path 객체에서는 폴더와 파일 경로를 연결한다.
#
from pathlib import Path


# ------------------------------------------------------------
# 6. FastAPI
# ------------------------------------------------------------
#
# 외부 라이브러리
# 설치 명령어:
# pip install fastapi
#
# FastAPI:
# Python으로 HTTP API 서버를 구현하는 웹 프레임워크
#
# Request:
# 클라이언트가 서버에 보낸 HTTP 요청 정보를 담는 객체
#
# HTTPException:
# HTTP 오류 상태 코드와 메시지를 반환하기 위한 예외
#
# 예:
# HTTPException(404, "Not Found")
#
from fastapi import FastAPI, Request, HTTPException


# ------------------------------------------------------------
# 7. Response
# ------------------------------------------------------------
#
# FastAPI가 사용하는 Starlette 기반 응답 클래스
#
# [역할]
# HTTP 응답 본문, Content-Type, 헤더 등을 직접 설정한다.
#
# [사용 목적]
# OData 응답에 필요한 JSON, XML, 텍스트 및
# OData-Version 헤더를 명시적으로 제공한다.
#
from fastapi.responses import Response


# ============================================================
# STEP 02. FastAPI 애플리케이션 생성
# ============================================================


# FastAPI()는 웹 애플리케이션 객체를 생성한다.
#
# app:
# 이후 API 엔드포인트를 등록할 서버 객체
#
# title:
# Swagger UI에 표시되는 API 이름
#
# Swagger UI:
# FastAPI에서 자동 생성되는 API 테스트 및 문서 화면
#
# 확인 주소:
# http://127.0.0.1:8000/docs
#
app = FastAPI(
    title="Naver Blog OData API"
)


# ============================================================
# STEP 03. XML 데이터 파일 경로 설정
# ============================================================


# __file__:
# 현재 실행 중인 Python 소스 파일의 경로
#
# Path(__file__).parent:
# main.py가 위치한 폴더
#
# / "data":
# data 폴더로 이동
#
# / "naver_blog.xml":
# 해당 폴더의 XML 파일 지정
#
# 최종 경로 예:
# naver-tableau-odata/data/naver_blog.xml
#
# 현재 터미널의 작업 위치와 무관하게
# main.py를 기준으로 경로를 계산한다.
#
DATA_FILE = (
    Path(__file__).parent
    / "data"
    / "naver_blog.xml"
)


# ============================================================
# STEP 04. XML 데이터 파싱 함수
# ============================================================


# 파싱(Parsing):
# XML과 같은 구조화된 데이터를 분석하여
# 프로그램에서 사용할 수 있는 형태로 변환하는 작업
#
# 함수 이름:
# load_blogs
#
# 목적:
# XML → Python 딕셔너리 목록
#
def load_blogs():

    # --------------------------------------------------------
    # 1. XML 파일 존재 여부 확인
    # --------------------------------------------------------

    # exists():
    # 해당 경로에 파일이 존재하면 True
    # 존재하지 않으면 False
    #
    # not:
    # True와 False를 반대로 변경하는 논리 연산자
    #
    if not DATA_FILE.exists():

        # HTTPException:
        # API 요청에 대해 오류 응답을 발생시킨다.
        #
        # 503:
        # Service Unavailable
        # 현재 서비스가 요청을 처리할 수 없는 상태
        #
        raise HTTPException(
            status_code=503,
            detail="XML data file not found"
        )

    # --------------------------------------------------------
    # 2. XML 파일 읽기
    # --------------------------------------------------------

    # ET.parse():
    # XML 파일을 파싱하여 ElementTree 객체 생성
    #
    # getroot():
    # XML 문서의 최상위 요소 반환
    #
    root = ET.parse(DATA_FILE).getroot()

    # XML 데이터를 저장할 빈 리스트
    #
    # 최종적으로 다음과 같은 형태가 된다.
    #
    # [
    #     {"ID": 1, "Title": "..."},
    #     {"ID": 2, "Title": "..."}
    # ]
    #
    blogs = []

    # --------------------------------------------------------
    # 3. XML의 item 요소 반복 조회
    # --------------------------------------------------------

    # root.findall("./channel/item"):
    #
    # XML 구조에서 channel 아래의 item 요소를 모두 찾는다.
    #
    # XML 예:
    #
    # <rss>
    #   <channel>
    #     <item>
    #       <title>블로그 제목</title>
    #     </item>
    #   </channel>
    # </rss>
    #
    # "./channel/item":
    # 현재 루트 요소를 기준으로 channel/item 경로 탐색
    #
    # enumerate():
    # 반복 가능한 데이터에 순번을 부여한다.
    #
    # enumerate(데이터, 1):
    # 순번을 1부터 시작한다.
    #
    # index:
    # 게시물 순번
    #
    # item:
    # 현재 반복 중인 XML item 요소
    #
    for index, item in enumerate(
        root.findall("./channel/item"),
        1
    ):

        # ----------------------------------------------------
        # 4. 블로그 제목 추출
        # ----------------------------------------------------

        # findtext("title", ""):
        #
        # title 요소의 텍스트를 가져온다.
        # 요소가 없으면 빈 문자열을 반환한다.
        #
        title = item.findtext("title", "")

        # ----------------------------------------------------
        # 5. HTML 엔티티 및 태그 제거
        # ----------------------------------------------------

        # html.unescape(title):
        # HTML 엔티티를 일반 문자로 변환한다.
        #
        # re.sub():
        # 정규표현식에 일치하는 문자열을 대체한다.
        #
        # r"<[^>]+>":
        #
        # r""  : Raw String (원시 문자열)
        # <    : 여는 꺾쇠괄호
        # [^>] : >가 아닌 문자
        # +    : 앞의 패턴이 한 번 이상 반복
        # >    : 닫는 꺾쇠괄호
        #
        # 결과:
        # HTML 태그처럼 보이는 부분을 제거한다.
        #
        # 예:
        # "<b>파이썬</b> 강의"
        #          ↓
        # "파이썬 강의"
        #
        # 주의:
        # 정규표현식은 완전한 HTML 파서가 아니므로
        # 복잡하거나 잘못된 HTML에는 한계가 있다.
        #
        title = re.sub(
            r"<[^>]+>",
            "",
            html.unescape(title)
        )

        # ----------------------------------------------------
        # 6. XML 데이터를 딕셔너리로 변환
        # ----------------------------------------------------

        # append():
        # 리스트의 마지막에 새로운 요소를 추가한다.
        #
        # 딕셔너리:
        # Key : Value 형태로 데이터를 저장한다.
        #
        # ID:
        # OData에서 게시물을 구별하는 키
        #
        # 주의:
        # 이 ID는 XML 순서에 따라 생성되므로
        # 데이터를 다시 수집하면 같은 게시물의 ID가
        # 달라질 수 있다.
        #
        blogs.append({
            "ID": index,

            "Title": title,

            "BloggerName": item.findtext(
                "bloggername", ""
            ),

            "PostDate": item.findtext(
                "postdate", ""
            ),

            "Link": item.findtext(
                "link", ""
            )
        })

    # --------------------------------------------------------
    # 7. 파싱 결과 반환
    # --------------------------------------------------------

    # return:
    # 함수의 실행 결과를 호출한 위치로 전달한다.
    #
    return blogs


# ============================================================
# STEP 05. OData 기본 URL 생성 함수
# ============================================================


# OData:
# Open Data Protocol
#
# HTTP를 기반으로 데이터를 조회하고 교환하기 위한
# 표준 프로토콜
#
# OData 서비스는 메타데이터와 데이터 조회 주소를 제공한다.
#
def base_url(request: Request):

    # request.base_url:
    # 현재 요청의 기본 URL
    #
    # 예:
    # http://127.0.0.1:8000/
    #
    # str():
    # URL 객체를 문자열로 변환
    #
    # rstrip("/"):
    # 문자열 오른쪽 끝에 있는 / 제거
    #
    # + "/odata/":
    # OData 서비스 경로 추가
    #
    # 최종 결과:
    # http://127.0.0.1:8000/odata/
    #
    return (
        str(request.base_url).rstrip("/")
        + "/odata/"
    )


# ============================================================
# STEP 06. OData JSON 응답 생성 함수
# ============================================================


# 목적:
# 모든 OData JSON 응답에 공통으로 사용되는
# Content-Type 및 OData-Version 헤더를 설정한다.
#
def odata_json(data):

    # json.dumps():
    # Python 딕셔너리를 JSON 문자열로 변환
    #
    # ensure_ascii=False:
    # 한글을 유니코드 이스케이프 문자열로 바꾸지 않고
    # 그대로 출력한다.
    #
    # 예:
    # {"Title": "파이썬"}
    #
    # media_type:
    # HTTP 응답의 콘텐츠 유형
    #
    # application/json:
    # JSON 형식의 데이터라는 의미
    #
    # headers:
    # HTTP 응답에 추가할 헤더
    #
    # OData-Version: 4.0
    # OData 프로토콜 버전 표시
    #
    return Response(
        content=json.dumps(
            data,
            ensure_ascii=False
        ),
        media_type="application/json",
        headers={
            "OData-Version": "4.0"
        }
    )


# ============================================================
# STEP 07. 기본 서버 상태 확인 API
# ============================================================


# @app.get("/"):
#
# 데코레이터(Decorator):
# 함수를 특정 HTTP 요청 경로에 연결하는 문법
#
# GET:
# 서버에서 데이터를 조회할 때 사용하는 HTTP 메서드
#
# "/":
# 웹 서버의 최상위 경로
#
# 접속:
# http://127.0.0.1:8000/
#
@app.get("/")
def home():

    # FastAPI는 일반 딕셔너리를
    # 자동으로 JSON 응답으로 변환한다.
    #
    return {
        "status": "running",

        "service": "/odata/",

        "metadata": "/odata/$metadata",

        "data": "/odata/Blogs"
    }


# ============================================================
# STEP 08. OData 서비스 루트 구현
# ============================================================


# 서비스 루트(Service Root):
# OData 서버가 제공하는 데이터 집합을 안내하는 주소
#
# 접속:
# http://127.0.0.1:8000/odata/
#
@app.get("/odata/")
def service_root(request: Request):

    # @odata.context:
    # OData 응답이 어떤 메타데이터를 기준으로
    # 구성되었는지 나타낸다.
    #
    # $metadata:
    # 데이터 모델 구조를 설명하는 OData 메타데이터
    #
    # value:
    # 서비스에서 제공하는 EntitySet 목록
    #
    # EntitySet:
    # 동일한 EntityType을 가진 엔터티들의 집합
    #
    # Blogs:
    # 블로그 게시물 데이터 집합의 이름
    #
    return odata_json({
        "@odata.context": (
            base_url(request) + "$metadata"
        ),

        "value": [
            {
                "name": "Blogs",
                "kind": "EntitySet",
                "url": "Blogs"
            }
        ]
    })


# ============================================================
# STEP 09. OData 메타데이터 구현
# ============================================================


# 메타데이터(Metadata):
# 데이터를 설명하는 데이터
#
# 예:
# 컬럼 이름, 데이터 타입, 기본키, 엔터티 구조 등
#
# OData V4 메타데이터는 XML 기반 CSDL 형식으로
# 표현할 수 있다.
#
# CSDL:
# Common Schema Definition Language
#
# 접속:
# http://127.0.0.1:8000/odata/$metadata
#
@app.get("/odata/$metadata")
def metadata():

    # 삼중 따옴표:
    # 여러 줄의 문자열을 작성할 때 사용한다.
    #
    # XML 구조:
    #
    # Edmx
    #  └─ DataServices
    #      └─ Schema
    #          ├─ EntityType
    #          │   ├─ Key
    #          │   └─ Property
    #          └─ EntityContainer
    #              └─ EntitySet
    #
    xml = """<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx Version="4.0"
 xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
  <edmx:DataServices>
    <Schema Namespace="Naver"
      xmlns="http://docs.oasis-open.org/odata/ns/edm">

      <!--
        EntityType:
        하나의 블로그 게시물이 갖는 데이터 구조
      -->
      <EntityType Name="Blog">

        <!--
          Key:
          게시물을 고유하게 식별하는 기본키
        -->
        <Key>
          <PropertyRef Name="ID"/>
        </Key>

        <!--
          Property:
          각 데이터 필드의 이름과 타입
          
          Edm.Int32:
          32비트 정수
          
          Edm.String:
          문자열
          
          Nullable="false":
          NULL을 허용하지 않음
        -->
        <Property Name="ID"
          Type="Edm.Int32" Nullable="false"/>

        <Property Name="Title"
          Type="Edm.String"/>

        <Property Name="BloggerName"
          Type="Edm.String"/>

        <Property Name="PostDate"
          Type="Edm.String"/>

        <Property Name="Link"
          Type="Edm.String"/>

      </EntityType>

      <!--
        EntityContainer:
        OData 데이터 집합을 관리하는 컨테이너
      -->
      <EntityContainer Name="Container">

        <!--
          EntitySet:
          Blog 엔터티들의 집합
          
          Name="Blogs":
          API에서 사용할 데이터 집합 이름
          
          EntityType="Naver.Blog":
          Naver 네임스페이스의 Blog 타입 참조
        -->
        <EntitySet Name="Blogs"
          EntityType="Naver.Blog"/>

      </EntityContainer>

    </Schema>
  </edmx:DataServices>
</edmx:Edmx>"""

    # XML 메타데이터를 HTTP 응답으로 반환
    #
    return Response(
        content=xml,
        media_type="application/xml",
        headers={
            "OData-Version": "4.0"
        }
    )


# ============================================================
# STEP 10. OData 데이터 조회 API
# ============================================================


# 접속:
# http://127.0.0.1:8000/odata/Blogs
#
# 지원하는 주요 쿼리 옵션:
#
# $skip    : 앞에서 몇 개를 건너뛸지
# $top     : 최대 몇 개를 가져올지
# $orderby : 어떤 필드로 정렬할지
# $count   : 전체 데이터 개수를 포함할지
#
# 예:
# /odata/Blogs?$top=5
#
# /odata/Blogs?$skip=5&$top=5
#
# /odata/Blogs?$orderby=ID desc
#
# /odata/Blogs?$count=true
#
@app.get("/odata/Blogs")
def get_blogs(request: Request):

    # --------------------------------------------------------
    # 1. XML 데이터 불러오기
    # --------------------------------------------------------

    blogs = load_blogs()

    # --------------------------------------------------------
    # 2. URL 쿼리 파라미터 가져오기
    # --------------------------------------------------------

    # request.query_params:
    # URL의 ? 뒤에 있는 쿼리 파라미터를 가져온다.
    #
    # 예:
    # /odata/Blogs?$top=5&$skip=2
    #
    # $top  = 5
    # $skip = 2
    #
    params = request.query_params

    # --------------------------------------------------------
    # 3. 페이지네이션 설정
    # --------------------------------------------------------

    # Pagination:
    # 전체 데이터를 여러 구간으로 나누어 조회하는 방식
    #
    # $skip:
    # 앞에서 건너뛸 데이터 개수
    #
    # $top:
    # 반환할 최대 데이터 개수
    #
    # params.get(키, 기본값):
    # 쿼리 파라미터가 없으면 기본값 사용
    #
    # int():
    # 문자열을 정수로 변환
    #
    # try / except:
    # 실행 중 발생할 수 있는 오류를 처리한다.
    #
    try:
        skip = int(
            params.get("$skip", "0")
        )

        top = int(
            params.get("$top", str(len(blogs)))
        )

    except ValueError:

        # 숫자로 변환할 수 없는 값이 전달되면
        # HTTP 400 오류 반환
        #
        # 400:
        # Bad Request
        #
        raise HTTPException(
            status_code=400,
            detail="Invalid pagination"
        )

    # 음수 값은 허용하지 않는다.
    #
    if skip < 0 or top < 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid pagination"
        )

    # --------------------------------------------------------
    # 4. 전체 데이터 개수 저장
    # --------------------------------------------------------

    # len():
    # 리스트에 들어 있는 요소 개수 반환
    #
    # 페이지네이션 이전의 전체 개수를 저장한다.
    #
    total = len(blogs)

    # --------------------------------------------------------
    # 5. 정렬 옵션 가져오기
    # --------------------------------------------------------

    # $orderby:
    # OData에서 데이터 정렬에 사용하는 쿼리 옵션
    #
    # 예:
    # ?$orderby=ID desc
    #
    # asc  : 오름차순
    # desc : 내림차순
    #
    orderby = params.get("$orderby")

    # 정렬 옵션이 전달된 경우에만 실행
    #
    if orderby:

        # split():
        # 공백을 기준으로 문자열 분리
        #
        # 예:
        # "ID desc".split()
        #          ↓
        # ["ID", "desc"]
        #
        parts = orderby.split()

        # ----------------------------------------------------
        # 6. 정렬 구문 검증
        # ----------------------------------------------------

        # 허용할 필드 이름을 명시적으로 정의한다.
        #
        # 원래 코드에서는 blogs[0]을 기준으로
        # 필드 존재 여부를 검사했지만,
        # 데이터가 없는 경우 검증이 불명확해질 수 있다.
        #
        allowed_fields = {
            "ID",
            "Title",
            "BloggerName",
            "PostDate",
            "Link"
        }

        # 형식이 잘못된 경우 오류 반환
        #
        # 허용:
        # ID
        # ID asc
        # ID desc
        #
        # 허용하지 않음:
        # ID descending
        # ID desc extra
        #
        if len(parts) not in (1, 2):
            raise HTTPException(
                status_code=400,
                detail="Invalid orderby"
            )

        # 첫 번째 값:
        # 정렬할 필드 이름
        #
        field = parts[0]

        if field not in allowed_fields:
            raise HTTPException(
                status_code=400,
                detail="Unknown field"
            )

        # 두 번째 값:
        # 정렬 방향
        #
        # 지정하지 않으면 asc를 기본값으로 사용한다.
        #
        direction = (
            parts[1]
            if len(parts) == 2
            else "asc"
        )

        if direction not in ("asc", "desc"):
            raise HTTPException(
                status_code=400,
                detail="Invalid orderby"
            )

        # ----------------------------------------------------
        # 7. 데이터 정렬
        # ----------------------------------------------------

        # sort():
        # 리스트 자체의 순서를 변경한다.
        #
        # key:
        # 어떤 값을 기준으로 정렬할지 지정
        #
        # lambda:
        # 이름 없이 간단한 함수를 작성하는 문법
        #
        # lambda x: x[field]
        #
        # 각 딕셔너리에서 지정한 필드 값을 가져온다.
        #
        # 예:
        # field = "ID"
        #
        # lambda x: x["ID"]
        #
        # reverse=True:
        # 내림차순 정렬
        #
        # reverse=False:
        # 오름차순 정렬
        #
        blogs.sort(
            key=lambda x: x[field],
            reverse=(direction == "desc")
        )

    # --------------------------------------------------------
    # 8. 페이지네이션 적용
    # --------------------------------------------------------

    # 리스트 슬라이싱:
    # 리스트[시작위치:종료위치]
    #
    # 예:
    # blogs[5:10]
    #
    # 인덱스 5부터 9까지 추출
    # 즉, 앞의 5개를 건너뛰고 최대 5개 반환
    #
    blogs = blogs[skip:skip + top]

    # --------------------------------------------------------
    # 9. OData 응답 데이터 구성
    # --------------------------------------------------------

    # @odata.context:
    # 응답 데이터와 메타데이터의 연결 정보
    #
    # $metadata#Blogs:
    # Blogs EntitySet의 메타데이터를 참조한다는 의미
    #
    # value:
    # 실제 블로그 게시물 목록
    #
    result = {
        "@odata.context": (
            base_url(request) + "$metadata#Blogs"
        ),

        "value": blogs
    }

    # --------------------------------------------------------
    # 10. 전체 건수 옵션 처리
    # --------------------------------------------------------

    # $count=true:
    # 응답에 전체 데이터 개수를 포함한다.
    #
    # lower():
    # 문자열을 소문자로 변환
    #
    # 예:
    # "TRUE".lower() → "true"
    #
    if params.get("$count", "").lower() == "true":

        # @odata.count:
        # OData 응답에서 전체 데이터 개수를 나타낸다.
        #
        # 페이지네이션 이전에 저장한 total을 사용한다.
        #
        result["@odata.count"] = total

    # --------------------------------------------------------
    # 11. JSON 응답 반환
    # --------------------------------------------------------

    return odata_json(result)


# ============================================================
# STEP 11. 전체 게시물 건수 조회
# ============================================================


# OData의 $count 경로:
# EntitySet에 포함된 데이터 개수를 반환한다.
#
# 접속:
# http://127.0.0.1:8000/odata/Blogs/$count
#
# 예:
# 100
#
@app.get("/odata/Blogs/$count")
def count_blogs():

    # load_blogs():
    # XML 데이터를 리스트로 변환
    #
    # len():
    # 전체 게시물 개수 계산
    #
    # str():
    # 숫자를 문자열로 변환
    #
    return Response(
        content=str(len(load_blogs())),

        # 개수만 일반 텍스트로 반환
        media_type="text/plain",

        headers={
            "OData-Version": "4.0"
        }
    )


# ============================================================
# STEP 12. 단일 게시물 조회
# ============================================================


# 특정 ID를 가진 게시물 하나를 조회한다.
#
# 접속 예:
# http://127.0.0.1:8000/odata/Blogs(1)
#
# OData에서 괄호 안의 값은 엔터티의 키를 의미한다.
#
# {blog_id}:
# FastAPI 경로 매개변수(Path Parameter)
#
# blog_id: int
# 전달받은 값을 정수로 검증 및 변환한다.
#
@app.get("/odata/Blogs({blog_id})")
def get_blog(blog_id: int, request: Request):

    # --------------------------------------------------------
    # 1. ID가 일치하는 게시물 검색
    # --------------------------------------------------------

    # next():
    # 반복 가능한 데이터에서 첫 번째 값을 가져온다.
    #
    # 제너레이터 표현식:
    #
    # (b for b in load_blogs() if b["ID"] == blog_id)
    #
    # 의미:
    # 모든 블로그를 순회하면서
    # ID가 blog_id와 일치하는 게시물을 찾는다.
    #
    # None:
    # 일치하는 게시물이 없을 때 반환할 기본값
    #
    blog = next(
        (
            b
            for b in load_blogs()
            if b["ID"] == blog_id
        ),
        None
    )

    # --------------------------------------------------------
    # 2. 게시물이 없을 때 오류 처리
    # --------------------------------------------------------

    # is None:
    # 값이 None 객체인지 확인
    #
    # 404:
    # Not Found
    #
    if blog is None:
        raise HTTPException(
            status_code=404,
            detail="Blog not found"
        )

    # --------------------------------------------------------
    # 3. 단일 엔터티 OData 응답 생성
    # --------------------------------------------------------

    # $metadata#Blogs/$entity:
    # Blogs EntitySet의 단일 엔터티라는 의미
    #
    # **blog:
    # 딕셔너리 언패킹(Dictionary Unpacking)
    #
    # 예:
    # blog = {"ID": 1, "Title": "Python"}
    #
    # {
    #     "@odata.context": "...",
    #     **blog
    # }
    #
    # 결과:
    # {
    #     "@odata.context": "...",
    #     "ID": 1,
    #     "Title": "Python"
    # }
    #
    return odata_json({
        "@odata.context": (
            base_url(request)
            + "$metadata#Blogs/$entity"
        ),

        **blog
    })


# ============================================================
# 서버 실행 명령어
# ============================================================
#
# 터미널에서 실행:
#
# uvicorn main:app --reload
#
# main:
# main.py 파일 이름
#
# app:
# FastAPI 애플리케이션 객체 이름
#
# --reload:
# Python 코드 변경 시 서버 자동 재시작
#
# 기본 서버 주소:
# http://127.0.0.1:8000
#
# API 테스트:
# http://127.0.0.1:8000/docs
#
# ============================================================
