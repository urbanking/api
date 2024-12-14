# 백엔드 Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 시스템 업데이트 및 필요한 패키지 설치
RUN apt-get update && \
    apt-get install -y wget unzip firefox-esr && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Geckodriver 설치
RUN GECKODRIVER_VERSION=0.33.0 && \
    wget https://github.com/mozilla/geckodriver/releases/download/v$GECKODRIVER_VERSION/geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz && \
    tar -xzf geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz -C /usr/local/bin/ && \
    rm geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz && \
    chmod +x /usr/local/bin/geckodriver  # 추가: geckodriver 실행 권한 부여

ENV FIREFOX_BIN=/usr/bin/firefox
ENV GECKODRIVER=/usr/local/bin/geckodriver

# webdriver-manager 제거로 인한 추가 패키지 설치 불필요

# config.yaml 복사하지 않음
# COPY . .  # 제거

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
