import os
import pymysql
import time
import logging  # 추가: 로깅 모듈 임포트
from pymysql.err import OperationalError

# 로깅 설정 추가
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# 데이터베이스 연결 설정
def get_connection():
    retries = 5
    while retries > 0:
        try:
            connection = pymysql.connect(
                host=os.environ.get('DB_HOST', 'db'),
                port=int(os.environ.get('DB_PORT', 3306)),
                user=os.environ.get('DB_USER', 'root'),
                password=os.environ.get('DB_PASSWORD', '1234'),
                database=os.environ.get('DB_NAME', 'crawling_db'),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            logging.info("데이터베이스에 정상적으로 연결되었습니다.")
            return connection
        except OperationalError as e:
            logging.error("데이터베이스에 연결할 수 없습니다. 5초 후에 재시도합니다...")
            retries -= 1
            time.sleep(5)
    logging.critical("여러 번 재시도 후에도 데이터베이스에 연결할 수 없습니다.")
    raise Exception("여러 번 재시도 후에도 데이터베이스에 연결할 수 없습니다.")

def create_table():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            create_table_query = '''
            CREATE TABLE IF NOT EXISTS cr_data30 (
                restaurant_name VARCHAR(255),
                id INT AUTO_INCREMENT PRIMARY KEY,
                writer VARCHAR(255),
                date VARCHAR(255),
                title VARCHAR(255),
                content TEXT,
                tags VARCHAR(255),
                sympathy INT,
                post_url VARCHAR(255) UNIQUE,
                ad_images TEXT,
                광고 VARCHAR(255)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            '''
            cursor.execute(create_table_query)
            logging.info("테이블이 생성되었거나 이미 존재합니다.")
        conn.commit()
    except Exception as e:
        logging.error(f"테이블 생성 중 오류 발생: {e}")
    finally:
        conn.close()


def save_to_db(data_list, restaurant_name):
    conn = get_connection()
    MAX_TAG_LENGTH = 255  # 태그 최대 길이 제한

    try:
        with conn.cursor() as cursor:
            insert_query = '''
            INSERT INTO cr_data30 (restaurant_name, writer, date, title, content, tags, sympathy, post_url, ad_images, 광고)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                restaurant_name = VALUES(restaurant_name),
                writer = VALUES(writer),
                date = VALUES(date),
                title = VALUES(title),
                content = VALUES(content),
                tags = VALUES(tags),
                sympathy = VALUES(sympathy),
                ad_images = VALUES(ad_images),
                광고 = VALUES(광고);
            '''

            # 태그 길이 제한 및 데이터 확인
            data_values = [
                (
                    restaurant_name,
                    item.get('writer', 'unknown'),
                    item.get('date', 'unknown'),
                    item.get('title', 'unknown'),
                    item.get('content', 'unknown'),
                    item.get('tags')[:MAX_TAG_LENGTH] if item.get('tags') and len(item['tags']) > MAX_TAG_LENGTH else (item.get('tags') or ""),
                    item.get('sympathy', 0),
                    item.get('post_url', 'unknown'),
                    item.get('ad_images', ''),
                    item.get('광고', 'X')
                )
                for item in data_list
            ]

            logging.info(f"Data to be saved: {data_values}")
            cursor.executemany(insert_query, data_values)

        conn.commit()
        logging.info(f"{len(data_values)} rows inserted/updated in the database.")
    except Exception as e:
        logging.error(f"데이터베이스 저장 중 오류 발생: {e}")
    finally:
        conn.close()




# 데이터베이스에서 모든 데이터 조회 함수
def fetch_all_data():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            select_query = 'SELECT * FROM cr_data30;'
            cursor.execute(select_query)
            results = cursor.fetchall()
        return results
    finally:
        conn.close()