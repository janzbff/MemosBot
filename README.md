# MemosBot
利用Telegram Bot作为Memos的前端。
# Bot
[MemosBot](https://t.me/memos_self_bot)

# Docker 部署
## image构建
```
$ cd MemosBot
$ docker build -t memosbot:v1 .
```
## polling模式
```
$ docker run -d -e API_TOKEN=<api_token> -v <db_path>:/MemosBot/db/ --name memosbot janzbff/memosbot:latest   
```
## webhook模式，需要有ssl证书，或者反代
```
$ docker run -d -e API_TOKEN=<api_token> \
                -e MODE=webhook \
                -e WEBHOOK_HOST=<webhook host> \
                -e WEBHOOK_LISTEN="0.0.0.0" \
                -p 8443:8443 janzbff/memosbot:latest
```
## docker-compose.yml
```
version: '3'
services:
  memos:
    image: janzbff/memosbot:latest
    ports:
      - "8443:8443"
    environment:
      - API_TOKEN=<token>
      # - MODE=webhook
      # - WEBHOOK_HOST=<webhook_host>
      # - WEBHOOK_LISTEN=0.0.0.0
    restart: always
    volumes:
      - <db_path>:/memos/db/
      - <logs_path>:/memos/logs/
```
# 本机部署
## 克隆代码并配置虚拟环境和安装依赖
```bash
$ git clone https://github.com/janzbff/MemosBot.git
$ cd MemosBot
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
```

## 配置`.env`文件
```bash
$ vim .env
```
### env文件示例
```
#'563623xxxx:AAGg6Fg_sEm1u5sZ1Twg-lhhm2K-xxxxxg'
API_TOKEN="" 

# webhook or polling 
# webhook require ssl
MODE="polling"

#'https://bot.tg.com'
WEBHOOK_HOST="https://tgbot.xxx.com"

#8443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_PORT="8443"

#'127.0.0.1'  # In some VPS you may need to put here the IP addr
WEBHOOK_LISTEN="127.0.0.1"    
```

## 后台运行
**建议用screen后台，或者写systemd service**
```bash
$ screen -R memos
$ python3 app.py
```

# Bot使用
[简单使用教程](https://blog.529213.xyz/article/memos-bot)