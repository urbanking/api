import logging  # 추가: 로깅 모듈 임포트
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request  # 변경: Request 추가
from pydantic import BaseModel
from typing import List, Optional  # 추가: Optional 임포트
from fastapi.middleware.cors import CORSMiddleware
import os
from concurrent.futures import ThreadPoolExecutor
import yaml
from asyncio import Queue  # 변경: asyncio.Queue 사용
from contextlib import asynccontextmanager  # 추가: asynccontextmanager 임포트

from database import save_to_db, create_table, fetch_all_data
from crawler import Crawler
# from predict import train_model  # 제거: predict.py 관련 임포트

# 백그라운드 태스크 관리
crawl_task: Optional[asyncio.Task] = None  # 추가: 크롤러 태스크 변수 선언

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 초기화 작업
    create_table()
    logging.info("테이블이 생성되거나 존재함이 확인되었습니다.")
    
    # 백그라운드 작업 시작
    logging.info("백그라운드 작업을 시작합니다.")
    global crawl_task  # 추가: 전역 크롤러 태스크 사용
    task1 = asyncio.create_task(crawl_worker(1))
    logging.info("crawl_worker 작업이 시작되었습니다.")
    task2 = asyncio.create_task(save())
    logging.info("save 작업이 시작되었습니다.")
    
    try:
        yield
    finally:
        # 작업 취소 등 정리 작업 수행
        logging.info("백그라운드 작업을 취소합니다.")
        if crawl_task:
            crawl_task.cancel()  # 추가: 크롤러 태스크 취소
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
import json  # 상태 저장을 위한 json
import os
import logging  # 로깅 모듈 추가

STATE_FILE = "crawl_state.json"  # 상태 파일 경로
DEFAULT_START_INDEX = 0  # 기본 시작 인덱스, 필요한 경우 90으로 설정 가능


# 상태 저장 함수
def save_crawl_state(start_index: int):
    with open(STATE_FILE, "w") as file:
        json.dump({"start_index": start_index}, file)
    logging.info(f"크롤링 상태 저장됨: start_index={start_index}")


# 상태 로드 함수
def load_crawl_state(default_index: int = DEFAULT_START_INDEX) -> int:
    """
    상태를 로드하며, 상태 파일이 없으면 기본값을 반환합니다.
    기본값은 DEFAULT_START_INDEX 또는 호출 시 설정한 값으로 설정됩니다.
    """
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as file:
            state = json.load(file)
            return state.get("start_index", default_index)
    return default_index  # 파일이 없을 경우 기본값 반환


# 비동기 크롤러 작업
async def crawl_worker(worker_id: int = 1, limit: Optional[int] = 170):
    logging.info(f"crawl_worker {worker_id} 시작")
    crawler = Crawler()

    # 이전 상태에서 시작
    start_index = load_crawl_state(default_index=0)  # 기본값을 90으로 설정
    logging.info(f"이전 크롤링 상태에서 시작: start_index={start_index}, limit={limit}")

    try:
        limit = limit or num_crawlers * 170  # 수정: limit 기본값 설정
        limited_queries = queries[start_index:start_index + limit]  # 제한된 query 목록
        logging.info(f"Worker {worker_id}: 크롤링할 query 목록 - {limited_queries}")

        for query_index, query in enumerate(limited_queries, start=start_index):
            urls = crawler.fetch_urls_from_api(query, max_posts)
            logging.info(f"Worker {worker_id}: {len(urls)}개의 URL을 수집했습니다.")

            for url in urls:
                retries = 3  # 최대 재시도 횟수
                while retries > 0:
                    try:
                        logging.info(f"Worker {worker_id}: {url} 크롤링 시작")
                        data = await asyncio.get_event_loop().run_in_executor(
                            executor, crawler.crawl_blog_content, url
                        )
                        if data and data['title'] != 'error':  # "error" 데이터 필터링
                            # restaurant_name 추가
                            data['restaurant_name'] = query
                            await data_queue.put(data)
                            logging.info(f"Worker {worker_id}: 데이터 큐에 추가됨 - {url}")
                            logging.info(f"현재 큐에 {data_queue.qsize()}개가 있습니다.")
                            logging.info(f"크롤링된 제목: {data['title']}")
                        else:
                            logging.warning(f"Worker {worker_id}: URL 크롤링 실패 - {url}")
                        break  # 성공적으로 크롤링하면 재시도 종료
                    except Exception as e:
                        logging.error(f"Worker {worker_id}: URL 크롤링 중 오류 발생 - {url}: {e}")
                        retries -= 1
                        if retries > 0:
                            logging.info(f"Worker {worker_id}: WebDriver 재시도 중...")
                            crawler.reset_driver()  # WebDriver 재생성
                        else:
                            logging.warning(f"Worker {worker_id}: {url} 크롤링 재시도 횟수 초과")

            # 현재 인덱스 상태 저장
            save_crawl_state(query_index + 1)  # 다음 query 시작 위치 저장

        logging.info(f"Worker {worker_id}: 모든 query에 대해 크롤링이 완료되었습니다.")

    except Exception as e:
        logging.error(f"Worker {worker_id}: 크롤링 중 오류 발생 - {e}")


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
                if data_list:
                    # restaurant_name은 batch 내 첫 번째 데이터의 값으로 사용
                    restaurant_name = data_list[0].get('restaurant_name', None)
                    if restaurant_name:
                        await asyncio.get_event_loop().run_in_executor(
                            None, save_to_db, data_list, restaurant_name
                        )  # 비동기로 save_to_db 실행
                        logging.info("5개의 데이터를 데이터베이스에 저장했습니다.")
                        logging.info(f"현재 큐에 {data_queue.qsize()}개가 있습니다.")
                    else:
                        logging.warning("restaurant_name이 누락된 데이터가 발견되었습니다.")
            else:
                await asyncio.sleep(1)  # 큐에 5개 미만이면 1초 대기
        except Exception as e:
            logging.error(f"데이터 저장 중 오류 발생: {e}")

# 크롤러 시작 엔드포인트 추가
@app.post("/start-crawler")
async def start_crawler():
    global crawl_task
    if crawl_task and not crawl_task.done():
        raise HTTPException(status_code=400, detail="크롤러가 이미 실행 중입니다.")
    crawl_task = asyncio.create_task(crawl_worker())
    return {"message": "크롤러가 시작되었습니다."}

# 크롤러 중지 엔드포인트 추가
@app.post("/stop-crawler")
async def stop_crawler():
    global crawl_task
    if crawl_task and not crawl_task.done():
        crawl_task.cancel()
        return {"message": "크롤러가 중지되었습니다."}
    else:
        raise HTTPException(status_code=400, detail="실행 중인 크롤러가 없습니다.")

# __main__ 부분은 Docker에서 실행되므로 제거하거나 필요에 따라 유지
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)