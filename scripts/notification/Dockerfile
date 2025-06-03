# 使用轻量级的Python镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用程序代码
COPY . .

# 暴露端口 (与docker-compose.yml中一致)
EXPOSE 8888

# 设置日志目录权限 (如果需要)
# RUN mkdir -p /app/logs && chown -R <user>:<group> /app/logs

# 运行应用
CMD ["python", "app.py"]