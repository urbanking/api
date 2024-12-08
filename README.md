predict.py train_model.py는 더미 모델이니까 크게 안신경써도됨//프론트도 나중에 만들어질거 대비해서 그냥 아무거나 넣어둠.


##<프로젝트 개요>
이 프로젝트는 FastAPI를 사용하여 웹 크롤링, 데이터 저장 및 API 제공을 수행하는 파이프라인을 구성합니다. 주요 구성 요소와 그 역할은 다음과 같습니다:

#주요 구성 요소
FastAPI 서버 (main.py)

FastAPI를 사용하여 웹 서버를 실행합니다.
lifespan 이벤트 핸들러를 통해 서버 시작 시 데이터베이스 테이블을 생성하고, 백그라운드 작업(크롤링 및 데이터 저장)을 시작합니다.
/data 엔드포인트를 통해 데이터 조회(GET) 및 삽입(POST) 기능을 제공합니다.
크롤러 (crawler.py)

Crawler 클래스는 네이버 API를 사용하여 블로그 게시물 URL을 수집하고, 각 URL에서 블로그 내용을 크롤링하여 데이터를 수집합니다.
데이터베이스 (database.py)

MySQL 데이터베이스와의 연결을 관리하고, 데이터베이스 테이블을 생성하며, 크롤링된 데이터를 데이터베이스에 저장하고 조회합니다.
백그라운드 작업 (main.py)

crawl_worker 함수는 주기적으로 크롤링 작업을 수행합니다.
save 함수는 큐에 쌓인 데이터를 주기적으로 데이터베이스에 저장합니다.
Docker 설정 (docker-compose.yml, Dockerfile)

docker-compose.yml 파일은 MySQL 데이터베이스, FastAPI 백엔드, 프론트엔드, Adminer를 포함한 여러 Docker 컨테이너를 정의합니다.
Dockerfile은 FastAPI 백엔드 애플리케이션을 위한 Docker 이미지를 빌드합니다.
설정 파일 (config.yaml)

크롤링할 쿼리 목록과 최대 게시물 수, 크롤러 수를 정의합니다.
파이프라인 흐름
서버 시작

FastAPI 서버가 시작되면 lifespan 이벤트 핸들러가 호출됩니다.
데이터베이스 테이블을 생성하고, 크롤링 및 데이터 저장 작업을 백그라운드에서 실행합니다.
크롤링 작업

crawl_worker 함수는 주기적으로 네이버 API를 통해 블로그 게시물 URL을 수집합니다.
각 URL에 대해 crawl_blog_content 메서드를 호출하여 블로그 내용을 크롤링하고, 수집된 데이터를 큐에 추가합니다.
데이터 저장

save 함수는 큐에 쌓인 데이터를 주기적으로 데이터베이스에 저장합니다.
API 제공

/data 엔드포인트를 통해 데이터베이스에 저장된 데이터를 조회하거나 새로운 데이터를 삽입할 수 있습니다.
Docker 설정
docker-compose.yml

MySQL 데이터베이스, FastAPI 백엔드, 프론트엔드, Adminer를 포함한 여러 서비스를 정의합니다.
각 서비스는 필요한 환경 변수와 포트를 설정합니다.
Dockerfile

FastAPI 백엔드 애플리케이션을 위한 Docker 이미지를 빌드합니다.
필요한 패키지를 설치하고, 애플리케이션 코드를 복사한 후, Uvicorn을 사용하여 서버를 실행합니다.
설정 파일
config.yaml
크롤링할 쿼리 목록, 최대 게시물 수, 크롤러 수를 정의합니다.
예시:
이 구조는 웹 크롤링, 데이터 저장 및 API 제공을 효율적으로 처리하기 위해 비동기 작업과 큐를 활용하여 구성되었습니다. Docker를 사용하여 애플리케이션을 컨테이너화하여 쉽게 배포하고 관리할 수 있습니다.
