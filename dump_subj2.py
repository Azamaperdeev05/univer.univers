
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

    # The user screenshot shows: /student_register?studentID=178640&year=2025&term=2
    # Then there is a popup with grades by date. Where does Platonus get this data? Let's check API.
    url = f"{PLATONUS_URL}/rest/api/person/personSubj?studentIdx={person_id}&yearIdx=2025&semesterIdx=2"
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url, headers=headers) as resp:
            text = await resp.text()
            with open("platonus_api_test.json", "w", encoding="utf-8") as f:
                f.write(text)
            print("Detail Dumped")

if __name__ == "__main__":
    asyncio.run(main())

