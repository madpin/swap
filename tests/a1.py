import asyncio

try:
    task = asyncio.get_current_task()
    print("asyncio.get_current_task() is available")
except AttributeError:
    print("asyncio.get_current_task() is NOT available")

print(f"asyncio version: {asyncio.__version__}")
