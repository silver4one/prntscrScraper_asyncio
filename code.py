import asyncio, aiohttp, aiofiles, aiosqlite
import random
import string
import os, sys

VALID_PATH = "Valid"
MAX_CLIENTS = 25

async def insert_db(db, picture):
    await db.execute(f"INSERT INTO Generate VALUES (NULL,'{picture}')")

async def insert_invalid(db, picture):
    await db.execute(f"INSERT INTO Invalid VALUES (NULL,'{picture}')")

async def insert_valid(db, picture):
    await db.execute(f"INSERT INTO Valid VALUES (NULL,'{picture}')")

async def is_exist(db, picture):
    async with db.execute(f"SELECT picture FROM Generate WHERE picture='{picture}'") as cursor:
        if await cursor.fetchone():
            return True
    return False

async def fetch_async(session, db):
    while True:
        amount = int(''.join(random.choice('5' + '6' + '7') for _ in range(1)))
        name = ''
        if amount == 7:
            picture1 = str(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(3)))
            picture2 = str(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(3)))
            picture3 = str(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(1)))

            name = picture1 + picture2 + picture3
        if amount == 6:
            picture1 = str(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(3)))
            picture2 = str(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(3)))

            name = picture1 + picture2
        if amount == 5:
            name = str(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(5)))

        printsc = "http://i.imgur.com/" + "" + name + ".jpg"
        if await is_exist(db, name):
            continue

        await insert_db(db, name)

        async with session.get(printsc) as response:
            if not response.status == 200 or response.content_length in [0, 503, 4939, 4940, 4941, 12003, 5556]:
                response.close()
                print("[-] Invalid: " + name)
                await insert_invalid(db, name)
                continue

            async with aiofiles.open(os.path.join(VALID_PATH, name) + ".jpg", 'wb') as f:
                async for data in response.content.iter_any():
                    await f.write(data)

            print("[+] Valid: " + printsc)
            await insert_valid(db, name)
        response.close()
        await db.commit()

async def asynchronous():
    async with aiosqlite.connect('imgur.db') as db:
        await db.execute('PRAGMA synchronous = 0')
        await db.execute('PRAGMA journal_mode = OFF')
        await db.execute('CREATE TABLE if not exists Generate (id INTEGER PRIMARY KEY AUTOINCREMENT, picture)')
        await db.execute('CREATE TABLE if not exists Valid (id INTEGER PRIMARY KEY AUTOINCREMENT, picture)')
        await db.execute('CREATE TABLE if not exists Invalid (id INTEGER PRIMARY KEY AUTOINCREMENT, picture)')

        while True:
            async with aiohttp.ClientSession() as session:
                tasks = [asyncio.ensure_future(fetch_async(session, db)) for _ in range(1, MAX_CLIENTS + 1)]
                await asyncio.gather(*tasks)
                print("Reload...")
                await asyncio.sleep(10000)
                await session.close()


if __name__ == "__main__":
    #if len(sys.argv) < 2:
    #    sys.exit("\033[37mUsage: python " + sys.argv[0] + " (Number of threads)")

    #MAX_CLIENTS = int(sys.argv[1])

    print("Starting threads #" + str(MAX_CLIENTS))

    if not os.path.exists(VALID_PATH):
        os.makedirs(VALID_PATH)

    print(f'{MAX_CLIENTS} asynchronous threads running:')
    ioloop = asyncio.get_event_loop()
    ioloop.run_until_complete(asynchronous())
    ioloop.close()