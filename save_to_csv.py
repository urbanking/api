import pandas as pd
import logging
from sqlalchemy import create_engine

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# SQLAlchemy 엔진 생성 함수
def get_engine():
    try:
        engine = create_engine(
            "mysql+pymysql://root:1234@localhost:3307/crawling_db",  # SQLAlchemy 연결 문자열
            echo=False
        )
        logging.info("SQLAlchemy 엔진이 생성되었습니다.")
        return engine
    except Exception as e:
        logging.error(f"SQLAlchemy 엔진 생성 실패: {e}")
        raise

# MySQL 데이터를 CSV로 저장하는 함수
def save_table_to_csv(table_name, csv_file_name):
    engine = get_engine()
    try:
        # 데이터 가져오기
        query = f"SELECT * FROM {table_name};"
        df = pd.read_sql(query, engine)  # SQLAlchemy 엔진으로 데이터 읽기

        # CSV 파일로 저장
        df.to_csv(csv_file_name, index=False, encoding='utf-8-sig')  # utf-8-sig로 저장
        logging.info(f"테이블 '{table_name}' 데이터를 '{csv_file_name}'로 저장했습니다.")
    except Exception as e:
        logging.error(f"CSV 저장 중 오류 발생: {e}")

# 스크립트 실행
if __name__ == "__main__":
    TABLE_NAME = "cr_data30"         # 저장할 테이블 이름
    CSV_FILE_NAME = "cr_data30.csv"  # 저장할 CSV 파일 이름
    save_table_to_csv(TABLE_NAME, CSV_FILE_NAME)
