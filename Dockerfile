# 使用官方 Python 3.9 映像
FROM python:3.9-slim

# 設置工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式程式碼
COPY . .

# 設置環境變數
ENV FLASK_ENV=production

# 暴露埠號
EXPOSE 8080

# 運行應用程式
CMD ["gunicorn", "-b", ":8080", "app:app"]