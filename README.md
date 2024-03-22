Foodgram - сайт по созданию различных рецептов.

Доступен по ссылке https://alalalalaqqqwww.servebeer.com/


Используемые технологии в бекенде:
Python
Django
Django REST framework
djoser
Docker
Nginx

Как запустить проект?

Склонировать проект на локальный компьютер:
```
git clone git@github.com:Vulkii/foodgram-project-react.git
```

Перейти в папку backend, создать виртуальное окружение и установить зависимости.
```
py -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

Создать файл .env по примеру .env.example

Создать докер-контейнеры и загрузить их на dockerhub.
```
cd ../frontend
docker build -t username/foodgram_frontend . 
cd ../backend
docker build -t username/foodgram_backend .
cd ../gateway
docker build -t username/foodgram_gateway .

docker push username/foodgram_frontend
docker push username/foodgram_backend
docker push username/foodgram_gateway
```

Скопировать файл docker-compose.production.yml, изменить в нем "p1lan" на username, используемый ранее.
Загрузить файл на сервер, настроить и запустить nginx, перейти в директорию с docker-compose.production.yml и выполнить команду

```
docker compose -f docker-compose.production.yml up
```

Автор:
Сухих Матвей