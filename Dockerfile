FROM python:3.11-slim

WORKDIR /app

COPY . .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 启动命令
CMD gunicorn agent_face_pro.wsgi --bind 0.0.0.0:$PORT