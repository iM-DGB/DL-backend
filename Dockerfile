FROM python:3.13-slim

# 작업 디렉토리 설정
WORKDIR /app

# Poetry 설치 (캐시 없이 깔끔하게)
RUN pip install --no-cache-dir poetry

# 의존성 파일들 복사 (poetry.lock이 없으면 pyproject.toml만 복사)
COPY pyproject.toml poetry.lock* /app/

# Poetry 설정 변경 후 의존성 설치
RUN poetry config virtualenvs.create false \
    && poetry install --no-root

# 프로젝트 코드 전체 복사
COPY . /app

CMD ["python", "main.py"]
