import base64
import json
import aiohttp
from typing import Dict, List, Optional

PLATONUS_URL = "https://platonus.kstu.kz"
PLATONUS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}


def _encode_pt(auth_token: str, sid: str, cookies: dict) -> str:
    data = {"t": auth_token, "s": sid, "c": cookies}
    return base64.b64encode(json.dumps(data).encode()).decode()


def _decode_pt(pt_cookie: str) -> dict:
    try:
        decoded = base64.b64decode(pt_cookie.encode()).decode()
        return json.loads(decoded)
    except:
        if "|" in pt_cookie:
            t, s = pt_cookie.split("|", 1)
            return {"t": t, "s": s, "c": {}}
        return {}


async def platonus_login(username, password):
    login_url = f"{PLATONUS_URL}/rest/api/login"
    login_data = {
        "login": username,
        "password": password,
        "iin": None,
        "icNumber": None,
        "authForDeductedStudentsAndGraduates": False,
    }
    # language 2 corresponds to Russian in Platonus, 1 to Kazakh
    headers = {**PLATONUS_HEADERS, "language": "2"}

    async with aiohttp.ClientSession() as session:
        async with session.post(login_url, json=login_data, headers=headers) as resp:
            if resp.status != 200:
                return None

            data = await resp.json()
            if data.get("login_status") != "success":
                return None

            auth_token = data.get("auth_token")
            sid = data.get("sid")

            extra_cookies = {
                name: morsel.value
                for name, morsel in resp.cookies.items()
                if name != "plt_sid"
            }

            return _encode_pt(auth_token, sid, extra_cookies)


async def platonus_get_person_id(pt_cookie: str):
    data = _decode_pt(pt_cookie)
    headers = {**PLATONUS_HEADERS, "token": data.get("t", ""), "sid": data.get("s", "")}
    cookies = data.get("c", {})
    cookies["plt_sid"] = data.get("s", "")

    url = f"{PLATONUS_URL}/rest/api/person/personID"
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                res = await resp.json()
                return res.get("personID")
    return None


async def platonus_get_student_info(pt_cookie: str):
    data = _decode_pt(pt_cookie)
    headers = {**PLATONUS_HEADERS, "token": data.get("t", ""), "sid": data.get("s", "")}
    cookies = data.get("c", {})
    cookies["plt_sid"] = data.get("s", "")

    url = f"{PLATONUS_URL}/rest/api/person/personName"
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                res = await resp.json()
                return res  # Should return dict with name/surname
    return None


def transform_marks(marks: List[Dict]) -> List:
    def parse_mark(val):
        if (
            not val
            or str(val).strip() == "-"
            or "жіберілмеген" in str(val).lower()
            or "не допущен" in str(val).lower()
        ):
            return 0.0
        try:
            return float(str(val).replace(",", "."))
        except:
            return 0.0

    # Platonus returns a list of exams, let's convert to a map for easier lookup
    # and handle both space and no-space variants in both languages
    m = {}
    for item in marks:
        if isinstance(item, dict) and "name" in item:
            m[item["name"].strip().replace(" ", "")] = item.get("mark")

    # Kazakh keys: АБ 1, АБ 2, Емт.
    # Russian keys: РК 1, РК 2, Экз.
    ab1_val = m.get("АБ1") or m.get("РК1") or m.get("Аттестация1") or 0.0
    ab2_val = m.get("АБ2") or m.get("РК2") or m.get("Аттестация2") or 0.0
    exam_val = (
        m.get("Емт.")
        or m.get("Экз.")
        or m.get("Итоговыйэкзамен")
        or m.get("Итог.экз.")
        or 0.0
    )

    # If not found in stripped map, try original names if any
    if not ab1_val:
        for item in marks:
            if isinstance(item, dict) and "name" in item:
                n = item["name"].strip()
                if n in ["АБ 1", "РК 1", "Аттестация 1"]:
                    ab1_val = item.get("mark")
                    break

    if not ab2_val:
        for item in marks:
            if isinstance(item, dict) and "name" in item:
                n = item["name"].strip()
                if n in ["АБ 2", "РК 2", "Аттестация 2"]:
                    ab2_val = item.get("mark")
                    break

    if not exam_val:
        for item in marks:
            if isinstance(item, dict) and "name" in item:
                n = item["name"].strip()
                if n in ["Емт.", "Экз.", "Итоговый экзамен", "Итог. экз."]:
                    exam_val = item.get("mark")
                    break

    ab1 = parse_mark(ab1_val)
    ab2 = parse_mark(ab2_val)
    exam = parse_mark(exam_val)

    # Note: Platonus marks can be 0.0 if not yet graded.
    # We treat it as "active" if it's 0.0
    return [
        ["АБ1", ab1, ab1 == 0],
        ["АБ2", ab2, ab2 == 0 and ab1 > 0],
        ["АА", exam, exam == 0 and ab2 > 0],
    ]


async def platonus_get_attestation(pt_cookie: str, year: int, semester: int):
    person_id = await platonus_get_person_id(pt_cookie)
    if not person_id:
        return []

    data = _decode_pt(pt_cookie)
    headers = {**PLATONUS_HEADERS, "token": data.get("t", ""), "sid": data.get("s", "")}
    cookies = data.get("c", {})
    cookies["plt_sid"] = data.get("s", "")

    url = f"{PLATONUS_URL}/journal/{year}/{semester}/{person_id}"
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                print(f"Platonus journal failed: {resp.status}")
                return []

            subjects = await resp.json()
            result = []
            for s in subjects:
                # Platonus journal returns a list of disciplines
                # each with a list of "exams" which are actually the marks
                exams = s.get("exams", [])
                transformed = transform_marks(exams)

                result.append(
                    {
                        "subject": s.get("subjectName", "").split("(")[0].strip(),
                        "attestation": transformed,
                        "attendance": [],
                        "sum": ["Барлығы", 0, False],
                    }
                )
            return result
