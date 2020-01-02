# Автобусы онлайн

Веб-приложение показывает передвижение автобусов на карте Москвы.

## Гифка

![preview](screenshots/buses.gif)

## Как это работает

Приложение состоит их трех сервисов:
- веб-интерфейс
- вебсокет-сервер (бекэнд)
- эмулятор данных о координатах автобусов

Веб-интерфейс присоединяется к бекэнду по вебсокету, отправляет в него
данные о текущих границах карты, получает данные об автобусах, попадающих
в эти границы.

Эмулятор также отправляет данные в бекэнд через веб-сокеты.

## Как запустить

Приложение запускается в docker-compose, веб-интерфейс доступен по адресу
http://127.0.0.1:3000/

```bash
make run
make stop
```

Можно запустить сервисы прямо на хосте, но вы не хотите этого делать

```bash
cd bus-tracker-backend
poetry install

make tests

poetry run emulator --help  # посмотреть какие крутилки есть у сервисов
poetry run bus-tracker --help
poetry run emulator  # можно запустить этот процесс в бекграунде
                     # с помощью 2>&1 & или использовать два терминала
poetry run bus-tracker
```

Чтобы получить веб-интерфейс можно просто открыть html файл в браузере,
он лежит в папке `bus-tracker-frontend/static`

## Тесты

Вместо скриптов, которые должны отправлять в сервис испорченные данные,
написаны тесты. Функционал веб-сокет сервера (бекэнда), покрыт полностью.

## Факультатив :)

Производительность реализованного "эмулятора" мне показалась неприлично низкой,
поэтому в докере он запускается в `pypy`, но даже там ворочается не очень охотно.

Из любопытства я переписал его сначала на Го, потом на нативный `asyncio`.
Имплементацию на Го ~~возможно запушу позже, потому что писалось быстро и грязно~~
можно найти [здесь](https://github.com/nobbynobbs/async-python-7-but-golang),
а реализацию с нативным `asyncio` в соседней ветке.

`asyncio` реализация работает заметно быстрее чем `trio`,
причем без `pypy` и даже если запускать в обычном лупе, а не в `uvloop`.
Никаких объективных замеров я не делал, но это видно невооруженным глазом.

Пока напрашивается вывод, что концептуально `trio` очень красивый,
на нем приятно писать, а эссе в блоге Натаниэля Смита очень интересно читать,
но в конкретном случае с тысячами спящих корутин, производительность
эвент-лупа `trio` оставляет желать лучшего.

Еще заметил, что имплементация `nursery` в `aionursery` кривая,
в том смысле, что она предоставляет интерфейс, отличающийся от `nursery` в `trio`.
В частности `start_soon` в `aionursery` принимает корутину,
а нативные `nursery` - асинхронную функцию с параметрами.

И это различие важно, потому что:

> ... there is one subtlety here that pushes Trio towards different conventions
> than asyncio or some other libraries: it means that `start_soon` has to take
> a function, not a coroutine object or a Future. (You can call a function
> multiple times, but there's no way to restart a coroutine object or a Future.)
> I think this is the better convention anyway for a number of reasons
> (especially since Trio doesn't even have Futures!), but still, worth mentioning
>
> [Notes on structured concurrency, or: Go statement considered harmful](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/#you-can-define-new-types-that-quack-like-a-nursery)

## Цели проекта

Код написан в учебных целях — это урок в курсе по Python
и веб-разработке на сайте [Devman](https://dvmn.org).
