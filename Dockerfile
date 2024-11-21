# 단계 1: 프론트엔드 빌드
FROM node:16 AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# 단계 2: 백엔드 설정
FROM python:3.9
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ ./backend

# 프론트엔드 빌드 결과물을 백엔드 정적 파일로 복사
COPY --from=frontend-build /app/frontend/build ./backend/frontend/build

# 환경 변수 설정 (필요한 경우)
ENV MINECRAFT_SERVER_HOST=${MINECRAFT_SERVER_HOST}
ENV MINECRAFT_SERVER_PORT=${MINECRAFT_SERVER_PORT}
ENV PORT=5000

EXPOSE 5000

# 앱 실행
CMD ["gunicorn", "--chdir", "backend", "app:app", "--bind", "0.0.0.0:5000"]


