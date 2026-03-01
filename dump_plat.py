
import asyncio
import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))

from core.functions.platonus import platonus_login, platonus_get_person_id, _decode_pt, PLATONUS_HEADERS, PLATONUS_URL
import aiohttp

async def main():
    pt = await platonus_login("Пердеев_Азамат", "Azamat05.")
    person_id = await platonus_get_person_id(pt)
    data = _decode_pt(pt)
    headers = {**PLATONUS_HEADERS, "token": data.get("t", ""), "sid": data.get("s", "")}
    cookies = data.get("c", {})
    cookies["plt_sid"] = data.get("s", "")

    url = f"{PLATONUS_URL}/journal/2025/2/{person_id}"
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url, headers=headers) as resp:
            subjects = await resp.json()
            with open("platonus_dump.json", "w", encoding="utf-8") as f:
                json.dump(subjects, f, ensure_ascii=False, indent=2)
            print("Dumped")

if __name__ == "__main__":
    asyncio.run(main())

