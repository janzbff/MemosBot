# 最好用3.10以上的版本,3.9版本的shelve模块有不一致的情况
FROM python:3.10-slim-buster

# 设置工作路径
WORKDIR /memos

# 复制
COPY . .

# 安装软件包
RUN pip install --no-cache-dir -r requirements.txt

# 放行端口
EXPOSE 8443

# 启动
CMD ["python", "app.py"]