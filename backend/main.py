from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import threading
from database import save_to_db, create_table, fetch_all_data
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요한 경우 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터 로드
data = pd.read_csv('data.csv')
data = data.fillna('')  # NaN 값을 빈 문자열로 대체

# 현재 인덱스를 추적하기 위한 변수
current_index = {'index': 0}
lock = threading.Lock()

# 응답 모델
class DataResponse(BaseModel):
    id: int
    writer: str
    title: str
    content: str
    tags: str
    sympathy: int
    post_url: str
    ad_images: str

# 서버 시작 시 테이블 생성
@app.on_event("startup")
def startup_event():
    create_table()

# 요청 처리 엔드포인트 (POST)
@app.post("/process_data", response_model=DataResponse)
def process_data():
    with lock:
        index = current_index['index']

        if index >= len(data):
            # 데이터의 끝에 도달하면 인덱스를 0으로 재설정
            current_index['index'] = 0
            index = 0

        row = data.iloc[index]
        current_index['index'] += 1

    # 데이터베이스에 저장할 데이터 구성
    record = {
        'writer': str(row.get('writer', '')),
        'title': str(row.get('title', '')),
        'content': str(row.get('content', '')),
        'tags': str(row.get('tags', '')),
        'sympathy': int(row.get('sympathy', 0)),
        'post_url': str(row.get('post_url', '')),
        'ad_images': str(row.get('ad_images', ''))
    }

    # 데이터베이스에 저장
    save_to_db([record])

    # 응답 데이터 구성
    response_data = DataResponse(
        id=index,
        writer=record['writer'],
        title=record['title'],
        content=record['content'],
        tags=record['tags'],
        sympathy=record['sympathy'],
        post_url=record['post_url'],
        ad_images=record['ad_images']
    )

    return response_data

# 데이터 조회 엔드포인트 (GET)
@app.get("/data", response_model=list[DataResponse])
def get_all_data():
    results = fetch_all_data()
    return results
