# 백엔드 Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pyyaml

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# 이미지 재빌드를 위해 Dockerfile 변경 사항이 반영되었는지 확인합니다.
