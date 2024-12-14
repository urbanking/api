import logging  # 추가: 로깅 모듈 임포트
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request  # 변경: Request 추가
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import os
from concurrent.futures import ThreadPoolExecutor
import yaml
from asyncio import Queue  # 변경: asyncio.Queue 사용
from contextlib import asynccontextmanager  # 추가: asynccontextmanager 임포트

from database import save_to_db, create_table, fetch_all_data
from crawler import Crawler
# from predict import train_model  # 제거: predict.py 관련 임포트

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 초기화 작업
    create_table()
    logging.info("테이블이 생성되거나 존재함이 확인되었습니다.")
    
    # 백그라운드 작업 시작
    logging.info("백그라운드 작업을 시작합니다.")
    task1 = asyncio.create_task(crawl_worker(1))
    logging.info("crawl_worker 작업이 시작되었습니다.")
    task2 = asyncio.create_task(save())
    logging.info("save 작업이 시작되었습니다.")
    
    try:
        yield
    finally:
        # 작업 취소 등 정리 작업 수행
        logging.info("백그라운드 작업을 취소합니다.")
        task1.cancel()
        task2.cancel()
        try:
            crawler = Crawler()
            crawler.driver.quit()
            logging.info("브라우저 인스턴스가 정상적으로 종료되었습니다.")
        except Exception as e:
            logging.error(f"브라우저 종료 중 오류 발생: {e}")

# FastAPI 인스턴스 생성 시 lifespan 컨텍스트 전달
app = FastAPI(lifespan=lifespan)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요한 경우 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 응답 모델
class DataResponse(BaseModel):
    id: int
    writer: str
    date: str
    title: str
    content: str
    tags: str
    sympathy: int
    post_url: str
    ad_images: str
    광고: str

class DataRequest(BaseModel):
    writer: str
    date: str
    title: str
    content: str
    tags: str
    sympathy: int
    post_url: str
    ad_images: str
    광고: str

executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=5)  # 병렬 작업을 위한 스레드 풀 생성

# 데이터 조회 엔드포인트 (GET)
@app.get("/data", response_model=List[DataResponse])
def get_all_data() -> List[DataResponse]:
    results = fetch_all_data()
    return results

# 데이터 삽입 엔드포인트 (POST)
@app.post("/data", response_model=DataResponse)
def add_data(data: DataRequest):
    try:
        save_to_db([data.dict()])
        return data
    except Exception as e:
        logging.error(f"데이터 삽입 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="데이터 삽입 중 오류 발생")

# config.yaml에서 설정 로드
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')  # 수정된 경로
with open(config_path, 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)
queries = config['query']  # 변경: query를 리스트로 로드
max_posts = config['max_posts']
num_crawlers = config.get('num_crawlers', 1)  # 변경: 크롤러 수를 1로 설정

# asyncio 큐 생성
data_queue = Queue()

# 로깅 설정 추가
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# 비동기 함수로 정의
async def crawl_worker(worker_id: int):
    logging.info(f"crawl_worker {worker_id} 시작")
    crawler = Crawler()
    while True:
        try:
            for query in queries:  # 변경: 각 query에 대해 순차적으로 처리
                urls = crawler.fetch_urls_from_api(query, max_posts)
                logging.info(f"Worker {worker_id}: {len(urls)}개의 URL을 수집했습니다.")
                for url in urls:
                    # 동기 함수 비동기로 실행
                    logging.info(f"Worker {worker_id}: {url} 크롤링 시작")
                    data = await asyncio.get_event_loop().run_in_executor(executor, crawler.crawl_blog_content, url)
                    if data:
                        await data_queue.put(data)  # asyncio.Queue 사용
                        logging.info(f"Worker {worker_id}: 데이터 큐에 추가됨 - {url}")
                        logging.info(f"현재 큐에 {data_queue.qsize()}개가 있습니다.")  # 추가: 현재 큐 사이즈 로그
                        logging.info(f"크롤링된 제목: {data['title']}")  # 추가: 크롤링된 제목 출력
                logging.info(f"Worker {worker_id}: 크롤링 완료. 60초 후 다음 크롤링 시작.")
        except Exception as e:
            logging.error(f"Worker {worker_id}: 크롤링 중 오류 발생 - {e}")
        await asyncio.sleep(60)  # 60초 대기 후 다음 크롤링 반복

# 비동기 함수로 정의
async def save():
    logging.info("save 작업 시작")
    while True:
        try:
            if data_queue.qsize() >= 5:
                data_list = []
                for _ in range(5):
                    data = await data_queue.get()
                    if data:
                        data_list.append(data)
                await asyncio.get_event_loop().run_in_executor(None, save_to_db, data_list)  # 비동기로 save_to_db 실행
                logging.info("5개의 데이터를 데이터베이스에 저장했습니다.")
                logging.info(f"현재 큐에 {data_queue.qsize()}개가 있습니다.")  # 추가: 현재 큐 사이즈 로그
            else:
                await asyncio.sleep(1)  # 큐에 5개 미만이면 1초 대기
        except Exception as e:
            logging.error(f"데이터 저장 중 오류 발생: {e}")

# __main__ 부분은 Docker에서 실행되므로 제거하거나 필요에 따라 유지
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
