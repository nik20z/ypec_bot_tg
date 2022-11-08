
<h1 align="center">YPEC Bot</h1>

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&pause=1000&width=435&lines=Telegram+bot+%D0%BA%D0%BE%D0%BB%D0%BB%D0%B5%D0%B4%D0%B6%D0%B0+%D0%AF%D0%9F%D0%AD%D0%9A" alt="Typing SVG" /></a>

<p align="center">
  <img src="https://img.shields.io/github/stars/nik20z/hltv_bot">
  <img src="https://img.shields.io/github/issues/nik20z/hltv_bot">
  <img src="https://img.shields.io/github/license/nik20z/hltv_bot">
</p>

[![https://telegram.me/ypec_bot](https://img.shields.io/badge/💬%20Telegram-Channel-blue.svg?style=flat-square)](https://telegram.me/ypec_bot)

![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)

## Описание
Ежедневная рассылка готового расписания (соединение основного расписания с заменами, которые появляются каждый день), а также отслеживание изменений в заменах в течение дня с последующим оповещением пользователей

## Будущие апдейты

- [ ] Написание парсера логов и добавление функции, собирающей статистику
- [ ] Создание анти-спам системы, которая будет блокировать спамеров
- [ ] Улучшение алгоритма обработки названий предметов (поиск похожих названий и их объединение)
- [ ] Интеграция с vk (пока на простом уровне, подразумевающем настройку в telegram). Пользователь vk будет получать то же расписание по рассылке, что и в telegram 


## Порядок установки на VPS

```
sudo adduser ypec

sudo apt update
sudo apt upgrade
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

pip3 install aiohttp
pip3 install aiogram
pip3 install beautifulsoup4
pip3 install loguru
pip3 install lxml
pip3 install nest-asyncio
pip3 install psycopg2-binary
pip3 install requests
pip3 install transliterate

cd /home/ypec
git clone https://github.com/nik20z/ypec_bot.git
```

Перед созданием службы, перезапускающей скрипт, необходимо в папку /etc/systemd/system поместить файл ypec_bot.service
```
apt-get install systemd
systemctl daemon-reload
systemctl enable ypec_bot
systemctl start ypec_bot
systemctl status ypec_bot

```

Если возникают проблемы с установкой python
```
sudo apt-get install libpq-dev
sudo apt-get install python-dev
```

Если возникают проблемы с локалью (база данных не воспринимает русский язык), то настраиваем через пакет:
```
dpkg-reconfigure locales
apt-get install language-pack-ru
```

<p align="center">
  <img src="https://user-images.githubusercontent.com/62090150/193757014-4e816ff4-e524-4d3d-a0f9-5d64701e9ec0.png">
</p>

