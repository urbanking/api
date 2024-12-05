import os
import pymysql
import time
from pymysql.err import OperationalError

# 데이터베이스 연결 설정
def get_connection():
    retries = 5
    while retries > 0:
        try:
            return pymysql.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                port=int(os.environ.get('DB_PORT', 3306)),
                user=os.environ.get('DB_USER', 'root'),
                password=os.environ.get('DB_PASSWORD', '1234'),
                database=os.environ.get('DB_NAME', 'crawling_db'),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        except OperationalError as e:
            print("데이터베이스에 연결할 수 없습니다. 5초 후에 재시도합니다...")
            retries -= 1
            time.sleep(5)
    raise Exception("여러 번 재시도 후에도 데이터베이스에 연결할 수 없습니다.")

# 테이블 생성 함수
def create_table():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            create_table_query = '''
            CREATE TABLE IF NOT EXISTS posts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                writer VARCHAR(255),
                title VARCHAR(255),
                content TEXT,
                tags VARCHAR(255),
                sympathy INT,
                post_url VARCHAR(255),
                ad_images TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            '''
            cursor.execute(create_table_query)
        conn.commit()
        print("Table created successfully!")
    finally:
        conn.close()

# 데이터베이스에 데이터 삽입 함수
def save_to_db(data_list):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            insert_query = '''
            INSERT INTO posts (writer, title, content, tags, sympathy, post_url, ad_images)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            '''
            data_values = [
                (
                    item['writer'],
                    item['title'],
                    item['content'],
                    item['tags'],
                    item['sympathy'],
                    item['post_url'],
                    item['ad_images']
                ) for item in data_list
            ]
            cursor.executemany(insert_query, data_values)
        conn.commit()
        print(f"{len(data_values)} rows inserted into the database.")
    finally:
        conn.close()

# 데이터베이스에서 모든 데이터 조회 함수
def fetch_all_data():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            select_query = 'SELECT * FROM posts;'
            cursor.execute(select_query)
            results = cursor.fetchall()
        return results
    finally:
        conn.close()
