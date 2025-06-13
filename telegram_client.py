from telethon import TelegramClient

# Твои данные
api_id = 26131454
api_hash = '800e8b63eaa842f1e5ab3c5a811dd3c9'

# Создаём клиент — название сессии можешь поменять
client = TelegramClient('session_jerry', api_id, api_hash)

async def main():
    me = await client.get_me()
    print(f'Успешно подключено как: {me.first_name} (ID: {me.id})')

# Запуск клиента
with client:
    client.loop.run_until_complete(main())
