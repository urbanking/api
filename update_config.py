import pandas as pd
import yaml

# list.csv 파일과 config.yaml 파일 경로
list_csv_path = "list.csv"  # list.csv 경로
config_yaml_path = "backend/config.yaml"  # config.yaml 경로

# list.csv에서 Title2 열만 읽어오기
try:
    df = pd.read_csv(list_csv_path)
    title_list = df['Title2'].dropna().tolist()  # Title2 열에서 값 가져오기 (NaN 제거)
except FileNotFoundError:
    print(f"Error: '{list_csv_path}' 파일이 없습니다.")
    exit()

# Title2 값에 "신촌"이 없으면 "신촌" 추가
processed_titles = []
for title in title_list:
    if "신촌" not in title:
        processed_titles.append(f"{title} 신촌")
    else:
        processed_titles.append(title)

# config.yaml 읽기
try:
    with open(config_yaml_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
except FileNotFoundError:
    print(f"Error: '{config_yaml_path}' 파일이 없습니다.")
    exit()

# query 값을 Title2 리스트로 업데이트
config["query"] = processed_titles

# 업데이트된 config.yaml 저장
with open(config_yaml_path, "w", encoding="utf-8") as file:
    yaml.dump(config, file, allow_unicode=True, default_flow_style=False)

print(f"'{config_yaml_path}' 파일이 성공적으로 업데이트되었습니다!")
