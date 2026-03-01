
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

    # The query string uses subjectID, studyGroupId, ticketInfoType
    # Taking them from the previous dump for IT-жобалар менеджменті
    subjectID = 5572
    studyGroupId = 21694
    ticketInfoType = 0
    queryID = 131630

    url = f"{PLATONUS_URL}/rest/api/schedules/schedule_current_score?subjectID={subjectID}&studyGroupId={studyGroupId}&ticketInfoType={ticketInfoType}"
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            with open("platonus_detail.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Detail Dumped")

if __name__ == "__main__":
    asyncio.run(main())

