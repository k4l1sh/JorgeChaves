import asyncio

async def count():
    for x in range(4):
        print(x)
        await asyncio.sleep(1)
        print(x)

async def main():
    await asyncio.gather(count())

if __name__ == "__main__":
    import time
    s = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")