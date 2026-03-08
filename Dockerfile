# 1. 파이썬 환경 설정
FROM python:3.9-slim

# 2. 크롬 브라우저와 필요한 부품들 강제 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 3. 작업 폴더 설정
WORKDIR /app

# 4. 부품 목록(requirements.txt) 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 모든 코드 복사
COPY . .

# 6. 서버 실행 (포트 10000 자동 맞춤)
CMD ["python", "app.py"]
