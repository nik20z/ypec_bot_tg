
<h1 align="center">YPEC Bot</h1>

<p align="center">
<img src="https://img.shields.io/github/stars/nik20z/hltv_bot">
<img src="https://img.shields.io/github/issues/nik20z/hltv_bot">
<img src="https://img.shields.io/github/license/nik20z/hltv_bot">
</p>


## Описание

[Телеграм Бот](https://t.me/ypec_bot "ypec_bot") - это неофициальный бот колледжа [ЯПЭК](https://www.ypec.ru "ypec.ru"). Основная его функция - ежедневная рассылка расписания, а также отслеживание изменений в заменах в течение дня. 


## Порядок установки на VPS

```
sudo apt update
sudo apt install python3.8
sudo apt install python3-pip

sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -i -u postgres
  psql
    CREATE USER ypec WITH PASSWORD '123456789';
    CREATE DATABASE ypec_bot;
    \c ypec_bot
    CREATE EXTENSION pg_trgm;
    \q
  exit

pip3 install aiogram
pip3 install beautifulsoup4
pip3 install lxml
pip3 install psycopg2-binary
pip3 install requests

apt-get install systemd
systemctl daemon-reload
systemctl enable ypec_bot
systemctl start ypec_bot
systemctl status ypec_bot
```

<p align="center">
  <img src="https://user-images.githubusercontent.com/62090150/193757014-4e816ff4-e524-4d3d-a0f9-5d64701e9ec0.png">
</p>
