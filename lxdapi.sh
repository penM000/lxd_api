PATH=~/.local/bin:$PATH
pip3 install aiofiles asyncio fastapi pylxd jinja2 aiofiles python-multipart aiohttp
uvicorn main:app --reload --host 0.0.0.0