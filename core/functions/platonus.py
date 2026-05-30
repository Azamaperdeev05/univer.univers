import base64
import json
import aiohttp
from typing import Dict, List, Optional

PLATONUS_URL = "https://platonus.kstu.kz"
PLATONUS_TIMEOUT = aiohttp.ClientTimeout(total=15)
PLATONUS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}

_AUTH_FAIL_STATUSES = (401, 403)


def _encode_pt(auth_token: str, sid: str, cookies: dict) -> str:
    data = {"t": auth_token, "s": sid, "c": cookies}
    return base64.b64encode(json.dumps(data).encode()).decode()


def _decode_pt(pt_cookie: str) -> dict:
    try:
        decoded = base64.b64decode(pt_cookie.encode()).decode()
        return json.loads(decoded)
    except Exception:
        if "|" in pt_cookie:
            t, s = pt_cookie.split("|", 1)
            return {"t": t, "s": s, "c": {}}
        return {}


def _pt_headers_and_cookies(pt_cookie: str):
    """Return (headers, cookies) ready for Platonus API calls."""
    data = _decode_pt(pt_cookie)
    headers = {**PLATONUS_HEADERS, "token": data.get("t", ""), "sid": data.get("s", "")}
    cookies = data.get("c", {})
    cookies["plt_sid"] = data.get("s", "")
    return headers, cookies


async def platonus_login(username: str, password: str) -> Optional[str]:
    login_url = f"{PLATONUS_URL}/rest/api/login"
    login_data = {
        "login": username,
        "password": password,
        "iin": None,
        "icNumber": None,
        "authForDeductedStudentsAndGraduates": False,
    }
    headers = {**PLATONUS_HEADERS, "language": "2"}  # 2=Russian, 1=Kazakh

    try:
        async with aiohttp.ClientSession(timeout=PLATONUS_TIMEOUT) as session:
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
    except Exception:
        return None


async def platonus_get_person_id(pt_cookie: str) -> Optional[int]:
    headers, cookies = _pt_headers_and_cookies(pt_cookie)
    url = f"{PLATONUS_URL}/rest/api/person/personID"
    try:
        async with aiohttp.ClientSession(cookies=cookies, timeout=PLATONUS_TIMEOUT) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    res = await resp.json()
                    return res.get("personID")
    except Exception:
        pass
    return None


async def platonus_get_student_info(pt_cookie: str) -> Optional[dict]:
    headers, cookies = _pt_headers_and_cookies(pt_cookie)
    url = f"{PLATONUS_URL}/rest/api/person/personName"
    try:
        async with aiohttp.ClientSession(cookies=cookies, timeout=PLATONUS_TIMEOUT) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception:
        pass
    return None


def transform_marks(marks: List[Dict], center_mark: str = None) -> List:
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
        except Exception:
            return 0.0

    m = {}
    for item in marks:
        if isinstance(item, dict) and "name" in item:
            m[item["name"].strip().replace(" ", "")] = item.get("mark")

    # Kazakh keys: АБ 1, АБ 2, Емт.  |  Russian keys: РК 1, РК 2, Экз.
    ab1_val = m.get("АБ1") or m.get("РК1") or m.get("Аттестация1") or 0.0
    ab2_val = m.get("АБ2") or m.get("РК2") or m.get("Аттестация2") or 0.0
    exam_val = (
        m.get("Емт.")
        or m.get("Экз.")
        or m.get("Итоговыйэкзамен")
        or m.get("Итог.экз.")
        or 0.0
    )

    # Course Work / Project check as exam grade fallback
    coursework_val = (
        m.get("Курс.ж.")
        or m.get("Курсоваяработа")
        or m.get("Курсовойпроект")
        or m.get("Курс.раб.")
        or m.get("Курс.пр.")
        or 0.0
    )
    if not exam_val and coursework_val:
        exam_val = coursework_val

    # Fallback: scan raw list for any unmatched key variants
    for item in marks:
        if not isinstance(item, dict) or "name" not in item:
            continue
        n = item["name"].strip()
        mark = item.get("mark")
        if not ab1_val and n in ("АБ 1", "РК 1", "Аттестация 1"):
            ab1_val = mark
        if not ab2_val and n in ("АБ 2", "РК 2", "Аттестация 2"):
            ab2_val = mark
        if not exam_val and n in ("Емт.", "Экз.", "Итоговый экзамен", "Итог. экз."):
            exam_val = mark
        if not exam_val and ("курсов" in n.lower() or "курс.ж" in n.lower() or "курс.р" in n.lower() or "курс.п" in n.lower()):
            exam_val = mark

    # Custom check for Practice or other non-standard single grades
    practice_val = 0.0
    for item in marks:
        if isinstance(item, dict) and "name" in item:
            name_lower = item["name"].lower()
            if "практ" in name_lower or "pract" in name_lower:
                practice_val = item.get("mark")
                break
                
    if practice_val:
        if not ab1_val or parse_mark(ab1_val) == 0.0: ab1_val = practice_val
        if not ab2_val or parse_mark(ab2_val) == 0.0: ab2_val = practice_val
        if not exam_val or parse_mark(exam_val) == 0.0: exam_val = practice_val

    ab1 = parse_mark(ab1_val)
    ab2 = parse_mark(ab2_val)
    exam = parse_mark(exam_val)

    # Fallback to center_mark if everything is 0
    if ab1 == 0.0 and ab2 == 0.0 and exam == 0.0 and center_mark:
        c_mark = parse_mark(center_mark)
        if c_mark > 0.0:
            ab1 = c_mark
            ab2 = c_mark
            exam = c_mark

    return [
        ["АБ1", ab1, ab1 == 0],
        ["АБ2", ab2, ab2 == 0 and ab1 > 0],
        ["АА", exam, exam == 0 and ab2 > 0],
    ]


async def platonus_get_attestation(
    pt_cookie: str, year: int, semester: int
) -> Optional[List]:
    """
    Returns:
       None   — auth token expired / personID unavailable → trigger refresh
       []     — authenticated but no subjects
       [...]  — list of subject dicts
    """
    person_id = await platonus_get_person_id(pt_cookie)
    if not person_id:
        return None

    headers, cookies = _pt_headers_and_cookies(pt_cookie)
    url = f"{PLATONUS_URL}/journal/{year}/{semester}/{person_id}"

    try:
        async with aiohttp.ClientSession(cookies=cookies, timeout=PLATONUS_TIMEOUT) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status in _AUTH_FAIL_STATUSES:
                    return None
                if resp.status != 200:
                    print(f"Platonus journal failed: {resp.status}")
                    return []

                subjects = await resp.json()
                result = []
                for s in subjects:
                    exams = s.get("exams", [])
                    result.append(
                        {
                            "subject": s.get("subjectName", "").split("(")[0].strip(),
                            "subject_id": s.get("subjectID"),
                            "query_id": s.get("queryID"),
                            "attestation": transform_marks(exams, s.get("centerMark")),
                            "attendance": [],
                            "sum": ["Барлығы", 0, False],
                        }
                    )
                return result
    except Exception as e:
        print(f"Platonus attestation error: {e}")
        return []


async def platonus_get_subject_details(
    pt_cookie: str, year: int, semester: int, subject_id: int, query_id: int
) -> Optional[List]:
    """
    Returns:
        None   — auth token expired → trigger refresh
        []     — no data or server error
        [...]  — list of class types with day-by-day marks (L / Lab / SRSP)
    """
    person_id = await platonus_get_person_id(pt_cookie)
    if not person_id:
        return None

    headers, cookies = _pt_headers_and_cookies(pt_cookie)
    url = f"{PLATONUS_URL}/subject/{year}/{semester}/{subject_id}/{person_id}?queryID={query_id}"

    try:
        async with aiohttp.ClientSession(cookies=cookies, timeout=PLATONUS_TIMEOUT) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status in _AUTH_FAIL_STATUSES:
                    return None
                if resp.status != 200:
                    print(f"Platonus subject details failed: {resp.status}")
                    return []
                return await resp.json()
    except Exception as e:
        print(f"Platonus subject details error: {e}")
        return []


async def platonus_get_transcript(pt_cookie: str) -> Optional[dict]:
    """
    POST /rest/transcript/load/ru/0
    Returns the student transcript data containing profile, GPA, and grade history.
    """
    headers, cookies = _pt_headers_and_cookies(pt_cookie)
    url = f"{PLATONUS_URL}/rest/transcript/load/ru/0"
    payload = {
        "includeSubjectUnderStudy": True,
        "showDeletedRecords": False,
        "showAllRecords": True,
        "showRewritableDisciplines": False,
        "showRetakenRecords": False,
        "searchText": ""
    }
    try:
        async with aiohttp.ClientSession(cookies=cookies, timeout=PLATONUS_TIMEOUT) as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status in _AUTH_FAIL_STATUSES:
                    return None
                if resp.status != 200:
                    print(f"Platonus load transcript failed: {resp.status}")
                    return None
                return await resp.json()
    except Exception as e:
        print(f"Platonus get transcript error: {e}")
        return None


async def platonus_get_umkd_list(pt_cookie: str, year: int, semester: int) -> Optional[dict]:
    """
    GET /rest/umkd/studentRecords/{year}/{semester}/ru
    Returns list of course folders with their methodological package cryptFileId.
    """
    headers, cookies = _pt_headers_and_cookies(pt_cookie)
    url = f"{PLATONUS_URL}/rest/umkd/studentRecords/{year}/{semester}/ru"
    try:
        async with aiohttp.ClientSession(cookies=cookies, timeout=PLATONUS_TIMEOUT) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status in _AUTH_FAIL_STATUSES:
                    return None
                if resp.status != 200:
                    print(f"Platonus get studentRecords failed: {resp.status}")
                    return None
                return await resp.json()
    except Exception as e:
        print(f"Platonus get UMKD list error: {e}")
        return None


async def platonus_get_umkd_files(pt_cookie: str, umkd_id: int) -> Optional[list]:
    """
    GET /rest/student/umkd/{umkd_id}/ru
    Returns the individual requirement folders inside the UMKD.
    """
    headers, cookies = _pt_headers_and_cookies(pt_cookie)
    url = f"{PLATONUS_URL}/rest/student/umkd/{umkd_id}/ru"
    try:
        async with aiohttp.ClientSession(cookies=cookies, timeout=PLATONUS_TIMEOUT) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status in _AUTH_FAIL_STATUSES:
                    return None
                if resp.status != 200:
                    print(f"Platonus student UMKD requirements failed: {resp.status}")
                    return None
                return await resp.json()
    except Exception as e:
        print(f"Platonus get UMKD files error: {e}")
        return None

