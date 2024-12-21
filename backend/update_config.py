
import yaml
import os
import logging

def load_config(config_path: str = 'backend/config.yaml') -> dict:
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        logging.info("설정 파일이 정상적으로 로드되었습니다.")
        return config
    except Exception as e:
        logging.error(f"설정 파일 로드 실패: {e}")
        raise e

def update_config(new_config: dict, config_path: str = 'backend/config.yaml'):
    try:
        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.safe_dump(new_config, file, allow_unicode=True)
        logging.info("설정 파일이 성공적으로 업데이트되었습니다.")
    except Exception as e:
        logging.error(f"설정 파일 업데이트 실패: {e}")
        raise e