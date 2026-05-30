from aiohttp import web
from dataclasses import asdict
import asyncio
import json
import os
import socket
import sys
import base64

# Core папкасын path-қа қосу (импорттар жұмыс істеуі үшін)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))

from push_notifications import push_service, scheduled_notifications
from functions.platonus import (
    platonus_login,
    platonus_get_student_info,
    platonus_get_attestation,
    platonus_get_subject_details,
    platonus_get_transcript,
    platonus_get_umkd_list,
    platonus_get_umkd_files,
)

# Frontend static папкасының жолы
CLIENT_DIR = os.path.join(os.path.dirname(__file__), "static")

routes = web.RouteTableDef()

DEFAULT_PORT = 7435
FALLBACK_PORT_START = 7436
FALLBACK_PORT_END = 7499


def try_bind(port: int) -> socket.socket | None:
    """Try binding to port and return a listening socket or None."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("0.0.0.0", port))
        sock.listen(128)
        return sock
    except OSError:
        sock.close()
        return None


def resolve_startup_socket() -> tuple[socket.socket, int, str]:
    """
    Resolve startup socket with strict behavior:
    - explicit PORT: strict bind, no fallback
    - no PORT: default 7435, then fallback 7436..7499
    """
    env_port = os.environ.get("PORT")
    if env_port is not None:
        try:
            port = int(env_port)
        except ValueError as exc:
            raise ValueError("PORT must be integer") from exc

        sock = try_bind(port)
        if sock is None:
            raise OSError(f"Configured PORT={port} is already in use")
        return sock, port, "env"

    sock = try_bind(DEFAULT_PORT)
    if sock is not None:
        return sock, DEFAULT_PORT, "default"

    for port in range(FALLBACK_PORT_START, FALLBACK_PORT_END + 1):
        sock = try_bind(port)
        if sock is not None:
            return sock, port, "fallback"

    raise OSError(
        f"No free ports in range {DEFAULT_PORT}..{FALLBACK_PORT_END}"
    )


# Credentials шифрлау/дешифрлау функциялары
def encode_credentials(username: str, password: str) -> str:
    """Username мен password-ты base64-ке шифрлау"""
    credentials = f"{username}:{password}"
    return base64.b64encode(credentials.encode()).decode()


def decode_credentials(encoded: str) -> tuple[str, str] | None:
    """Base64-тен credentials-ты дешифрлау"""
    try:
        decoded = base64.b64decode(encoded.encode()).decode()
        if ":" in decoded:
            username, password = decoded.split(":", 1)
            return username, password
    except Exception:
        pass
    return None


# Login handler
@routes.post("/auth/login")
async def login(request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")

    try:
        pt_token = await platonus_login(username, password)
        if not pt_token:
            return web.json_response({"error": "Platonus login failed"}, status=401)

        response = web.json_response({"status": "ok"})
        
        # Platonus session cookies
        response.set_cookie("_pt", pt_token, httponly=True, max_age=3600 * 24 * 30)
        pc = base64.b64encode(f"{username}:{password}".encode()).decode()
        response.set_cookie("_pc", pc, httponly=True, max_age=3600 * 24 * 30)
        response.set_cookie("_pl", "1", max_age=3600 * 24 * 30)

        return response
    except Exception as e:
        return web.json_response({"error": str(e)}, status=401)


# CORS middleware - Локальді әзірлеу кезінде CORS қателіктерінің алдын алу
async def cors_middleware(app, handler):
    async def middleware_handler(request):
        if request.method == "OPTIONS":
            response = web.Response(status=204)
        else:
            try:
                response = await handler(request)
            except web.HTTPException as ex:
                response = ex

        response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, token, sid"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    return middleware_handler


# API middleware - Platonus сессиясын дайындау және токенді автоматты жаңарту
async def platonus_middleware(app, handler):
    async def middleware_handler(request):
        public_paths = ["/api/privacy-policy", "/api/version"]
        if request.path.startswith("/api/") and request.path not in public_paths:
            pt = request.cookies.get("_pt")
            pc = request.cookies.get("_pc")

            # Егер Platonus токені жоқ болса, бірақ credentials бар болса - қайта кіру
            if not pt and pc:
                try:
                    decoded = base64.b64decode(pc).decode()
                    username, password = decoded.split(":", 1)
                    pt = await platonus_login(username, password)
                    if pt:
                        request["new_pt"] = pt
                except Exception:
                    pass

            if not pt:
                return web.json_response(
                    {"error": "unauthorized", "message": "Авторизация қажет"},
                    status=401,
                )

            request["pt_token"] = pt

        response = await handler(request)

        # Егер жаңа токен жасалса, оны cookie-ге жазу
        if isinstance(response, web.StreamResponse) and "new_pt" in request:
            response.set_cookie("_pt", request["new_pt"], httponly=True, max_age=3600 * 24 * 30)
            response.set_cookie(".ASPXAUTH", request["new_pt"], httponly=True, max_age=3600 * 24 * 30)

        return response

    return middleware_handler



def calculate_academic_week():
    from datetime import date
    today_date = date.today()
    
    # 2025-2026 Academic Year
    # Fall 2025
    fall_start = date(2025, 9, 1)
    fall_end = date(2025, 12, 13)
    
    # Spring 2026
    spring_start = date(2026, 1, 26)
    spring_end = date(2026, 4, 4)
    
    # Check Fall 2025
    if fall_start <= today_date <= fall_end:
        days = (today_date - fall_start).days
        week_num = (days // 7) + 1
        return {
            "finished": False,
            "week": week_num,
            "term": "Осенний семестр",
            "semester_name": "Күзгі семестр"
        }
        
    # Check Spring 2026
    if spring_start <= today_date <= spring_end:
        days = (today_date - spring_start).days
        week_num = (days // 7) + 1
        return {
            "finished": False,
            "week": week_num,
            "term": "Весенний семестр",
            "semester_name": "Көктемгі семестр"
        }
        
    # Otherwise, study is finished / not started
    # Determine which calendar to display
    if today_date < spring_start:
        # We are between Fall 2025 and Spring 2026 (Winter holidays/exams)
        return {
            "finished": True,
            "week": "Сабақ жоқ",
            "term": "Осенний семестр",
            "semester_name": "Күзгі семестр",
            "calendar": {
                "start": "1 қыркүйек",
                "end": "13 желтоқсан",
                "weeks": 15,
                "attestation1": "20-25 қазан",
                "attestation2": "8-13 желтоқсан",
                "exams": "15 желтоқсан - 31 желтоқсан",
                "holidays": "5 қаңтар - 23 қаңтар"
            }
        }
    else:
        # We are after Spring 2026 (Spring exams / summer practice / holidays)
        return {
            "finished": True,
            "week": "Сабақ жоқ",
            "term": "Весенний семестр",
            "semester_name": "Көктемгі семестр",
            "calendar": {
                "start": "26 қаңтар",
                "end": "4 сәуір",
                "weeks": 10,
                "attestation1": "23-28 ақпан",
                "attestation2": "30 наурыз - 4 сәуір",
                "exams": "6 сәуір - 11 сәуір",
                "practice": "13 сәуір - 16 мамыр (Өндірістік/Диплом алдындағы практика)",
                "thesis": "20 мамыр - 4 шілде (Дипломдық жұмысты қорғау)"
            }
        }


@routes.get("/api/schedule")
async def get_schedule(request):
    week_info = calculate_academic_week()
    return web.json_response({
        "lessons": [],
        "factor": None,
        "week": week_info.get("week", 1),
        "finished": week_info.get("finished", False),
        "semester_name": week_info.get("semester_name", ""),
        "calendar": week_info.get("calendar", {})
    })


@routes.get("/api/transcript")
async def get_transcript(request):
    pt_token = request.get("pt_token")
    if not pt_token:
        return web.json_response({"error": "unauthorized"}, status=401)

    try:
        res = await platonus_get_transcript(pt_token)
        if res is None:
            # Token might be expired, try refreshing using _pc
            pc_cookie = request.cookies.get("_pc")
            if pc_cookie:
                pt_token = await _platonus_refresh_token(pc_cookie)
                if pt_token:
                    res = await platonus_get_transcript(pt_token)

        if not res:
            return web.json_response({"error": "Failed to load transcript from Platonus"}, status=400)

        student = res.get("student") or {}
        
        # Extract localized fields
        study_lang = student.get("studyLanguageNameKz") or student.get("studyLanguageName") or "қазақ"
        fullname = student.get("fullName") or student.get("personName") or "Студент"
        faculty = student.get("facultyNameKz") or student.get("faculty_name") or "Факультет информационных технологий"
        degree = student.get("degreeNameKz") or student.get("degreeName") or "Бакалавр"
        program = student.get("specializationNameKz") or student.get("specializationName") or "Системы информационной безопасности"
        group = student.get("onlyProfessionNameKz") or student.get("professionName") or "Информационная безопасность"
        
        transcript_data = {
            "fullname": fullname,
            "faculty": faculty,
            "level_of_the_qualification": degree,
            "level_of_education": "Жоғары",
            "education_program": program,
            "education_program_group": group,
            "language": study_lang,
            "year_of_study": student.get("courseNumber") or 4,
            "length_of_program": float(student.get("courseCount") or 4.0),
            "graid_point": student.get("GPA") or 2.87,
            "avarage_point": student.get("averageMark") or 75.0,
            "form_of_study": student.get("studyFormNameKz") or student.get("studyFormName") or "күндізгі",
            "semesters": []
        }
        
        resp = web.json_response(transcript_data)
        if "new_pt" not in request and pt_token != request.cookies.get("_pt"):
            resp.set_cookie("_pt", pt_token, httponly=True, max_age=3600 * 24 * 30)
        return resp
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


@routes.get("/api/attestation")
async def get_attestation(request):
    pt_token = request.get("pt_token")
    if not pt_token:
        return web.json_response({"error": "unauthorized"}, status=401)

    from datetime import date
    today = date.today()
    year = today.year - 1 if today.month < 9 else today.year
    semester = 2 if today.month < 9 else 1

    term_param = request.query.get("term")
    if term_param:
        try:
            semester = int(term_param)
        except ValueError:
            pass

    try:
        data = await platonus_get_attestation(pt_token, year, semester)
        if data is None:
            # Token might be expired, try refreshing using _pc
            pc_cookie = request.cookies.get("_pc")
            if pc_cookie:
                pt_token = await _platonus_refresh_token(pc_cookie)
                if pt_token:
                    data = await platonus_get_attestation(pt_token, year, semester)

        if data is None:
            return web.json_response({"error": "session_expired"}, status=401)

        resp = web.json_response(data)
        if "new_pt" not in request and pt_token != request.cookies.get("_pt"):
            resp.set_cookie("_pt", pt_token, httponly=True, max_age=3600 * 24 * 30)
            resp.set_cookie(".ASPXAUTH", pt_token, httponly=True, max_age=3600 * 24 * 30)
        return resp
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def _platonus_refresh_token(pc_cookie: str | None) -> str | None:
    """Refresh Platonus token using stored credentials (_pc cookie)."""
    if not pc_cookie:
        return None
    try:
        decoded = base64.b64decode(pc_cookie).decode()
        u, p = decoded.split(":", 1)
        return await platonus_login(u, p)
    except Exception:
        return None


async def _get_pt_cookie(request) -> str | None:
    """Get existing Platonus token, or refresh if missing."""
    pt = request.cookies.get("_pt")
    if not pt:
        pt = await _platonus_refresh_token(request.cookies.get("_pc"))
    return pt


@routes.get("/api/subject_details")
async def get_subject_details(request):
    pt_token = request.get("pt_token")
    if not pt_token:
        return web.json_response({"error": "unauthorized"}, status=401)

    from datetime import date
    today = date.today()
    year = today.year - 1 if today.month < 9 else today.year
    semester = 2 if today.month < 9 else 1

    term_param = request.query.get("term")
    if term_param:
        try:
            semester = int(term_param)
        except ValueError:
            pass

    subject_id = request.query.get("subject_id")
    query_id = request.query.get("query_id")

    if not subject_id or not query_id:
        return web.json_response(
            {"error": "Missing subject_id or query_id"}, status=400
        )

    try:
        data = await platonus_get_subject_details(
            pt_token, int(year), int(semester), int(subject_id), int(query_id)
        )
        if data is None:
            # Token might be expired, try refreshing
            pc_cookie = request.cookies.get("_pc")
            if pc_cookie:
                pt_token = await _platonus_refresh_token(pc_cookie)
                if pt_token:
                    data = await platonus_get_subject_details(
                        pt_token, int(year), int(semester), int(subject_id), int(query_id)
                    )

        if data is None:
            return web.json_response({"error": "session_expired"}, status=401)

        resp = web.json_response(data)
        if "new_pt" not in request and pt_token != request.cookies.get("_pt"):
            resp.set_cookie("_pt", pt_token, httponly=True, max_age=3600 * 24 * 30)
        return resp
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


@routes.get("/api/exams")
async def get_exams(request):
    return web.json_response([])


@routes.post("/api/push/subscribe")
async def push_subscribe(request):
    data = await request.json()
    encoded_creds = request.cookies.get("_pc")  # Cookie-ден оқу
    univer_code = request.cookies.get("univer_code", "kstu")
    lang = request.query.get("lang", "kk")

    if not encoded_creds:
        return web.json_response({"error": "unauthorized"}, status=401)

    # Username-ді user_id ретінде қолдану
    creds = decode_credentials(encoded_creds)
    if not creds:
        return web.json_response({"error": "invalid_creds"}, status=401)

    username, _ = creds

    push_service.subscribe(
        user_id=username,
        subscription_info=data,
        univer_code=univer_code,
        encoded_creds=encoded_creds,
        language=lang,
    )

    return web.json_response({"status": "ok"})


@routes.post("/api/push/unsubscribe")
async def push_unsubscribe(request):
    encoded_creds = request.cookies.get("_pc")  # Cookie-ден оқу
    if not encoded_creds:
        return web.json_response({"error": "unauthorized"}, status=401)

    creds = decode_credentials(encoded_creds)
    if not creds:
        return web.json_response({"error": "invalid_creds"}, status=401)

    username, _ = creds
    push_service.unsubscribe(username)

    return web.json_response({"status": "ok"})


@routes.get("/api/push/status")
async def push_status(request):
    """Пайдаланушының жазылу статусын тексеру"""
    encoded_creds = request.cookies.get("_pc")
    if not encoded_creds:
        return web.json_response({"subscribed": False})

    creds = decode_credentials(encoded_creds)
    if not creds:
        return web.json_response({"subscribed": False})

    username, _ = creds
    is_subscribed = push_service.is_subscribed(username)
    settings = push_service.get_settings(username) if is_subscribed else None

    return web.json_response({"subscribed": is_subscribed, "settings": settings})


@routes.post("/api/push/settings")
async def push_update_settings(request):
    """Хабарлама параметрлерін жаңарту"""
    encoded_creds = request.cookies.get("_pc")
    if not encoded_creds:
        return web.json_response({"error": "unauthorized"}, status=401)

    creds = decode_credentials(encoded_creds)
    if not creds:
        return web.json_response({"error": "invalid_creds"}, status=401)

    username, _ = creds
    data = await request.json()
    settings = data.get("settings", {})

    success = push_service.update_settings(username, settings)
    if success:
        return web.json_response({"status": "ok", "settings": settings})
    else:
        return web.json_response({"error": "not_subscribed"}, status=404)


@routes.post("/api/push/test")
async def push_test(request):
    """Тестілік хабарлама жіберу"""
    encoded_creds = request.cookies.get("_pc")
    if not encoded_creds:
        return web.json_response({"error": "unauthorized"}, status=401)

    creds = decode_credentials(encoded_creds)
    if not creds:
        return web.json_response({"error": "invalid_creds"}, status=401)

    username, _ = creds

    # Тілді алу
    lang = request.query.get("lang", "kk")

    # Тілге сәйкес хабарлама
    messages = {
        "kk": {
            "title": "🎉 Тестілік хабарлама",
            "body": "Хабарламалар дұрыс жұмыс істеп тұр!",
        },
        "ru": {
            "title": "🎉 Тестовое уведомление",
            "body": "Уведомления работают правильно!",
        },
        "en": {
            "title": "🎉 Test Notification",
            "body": "Notifications are working correctly!",
        },
    }

    msg = messages.get(lang, messages["kk"])

    success = await push_service.send_notification(
        user_id=username, title=msg["title"], body=msg["body"], tag="test-notification"
    )

    if success:
        return web.json_response({"status": "ok"})
    else:
        return web.json_response({"error": "not_subscribed"}, status=404)


@routes.get("/api/push/history")
async def push_get_history(request):
    """Хабарлама тарихын алу"""
    encoded_creds = request.cookies.get("_pc")
    if not encoded_creds:
        return web.json_response({"error": "unauthorized"}, status=401)

    creds = decode_credentials(encoded_creds)
    if not creds:
        return web.json_response({"error": "invalid_creds"}, status=401)

    username, _ = creds
    limit = int(request.query.get("limit", 50))
    offset = int(request.query.get("offset", 0))

    history = push_service.get_notification_history(username, limit, offset)
    return web.json_response({"history": history, "count": len(history)})


@routes.post("/api/push/history/{notification_id}/mark-read")
async def push_mark_read(request):
    """Хабарламаны оқылған деп белгілеу"""
    encoded_creds = request.cookies.get("_pc")
    if not encoded_creds:
        return web.json_response({"error": "unauthorized"}, status=401)

    creds = decode_credentials(encoded_creds)
    if not creds:
        return web.json_response({"error": "invalid_creds"}, status=401)

    username, _ = creds
    notification_id = request.match_info["notification_id"]

    success = push_service.mark_notification_read(username, notification_id)
    if success:
        return web.json_response({"status": "ok"})
    else:
        return web.json_response({"error": "not_found"}, status=404)


@routes.post("/api/push/history/{notification_id}/mark-clicked")
async def push_mark_clicked(request):
    """Хабарламаны басылған деп белгілеу"""
    encoded_creds = request.cookies.get("_pc")
    if not encoded_creds:
        return web.json_response({"error": "unauthorized"}, status=401)

    creds = decode_credentials(encoded_creds)
    if not creds:
        return web.json_response({"error": "invalid_creds"}, status=401)

    username, _ = creds
    notification_id = request.match_info["notification_id"]

    success = push_service.mark_notification_clicked(username, notification_id)
    if success:
        return web.json_response({"status": "ok"})
    else:
        return web.json_response({"error": "not_found"}, status=404)


@routes.delete("/api/push/history/{notification_id}")
async def push_delete_notification(request):
    """Хабарламаны жою"""
    encoded_creds = request.cookies.get("_pc")
    if not encoded_creds:
        return web.json_response({"error": "unauthorized"}, status=401)

    creds = decode_credentials(encoded_creds)
    if not creds:
        return web.json_response({"error": "invalid_creds"}, status=401)

    username, _ = creds
    notification_id = request.match_info["notification_id"]

    success = push_service.delete_notification(username, notification_id)
    if success:
        return web.json_response({"status": "ok"})
    else:
        return web.json_response({"error": "not_found"}, status=404)


@routes.delete("/api/push/history")
async def push_clear_history(request):
    """Барлық хабарлама тарихын тазалау"""
    encoded_creds = request.cookies.get("_pc")
    if not encoded_creds:
        return web.json_response({"error": "unauthorized"}, status=401)

    creds = decode_credentials(encoded_creds)
    if not creds:
        return web.json_response({"error": "invalid_creds"}, status=401)

    username, _ = creds
    push_service.clear_notification_history(username)
    return web.json_response({"status": "ok"})


@routes.get("/api/push/stats")
async def push_get_stats(request):
    """Хабарлама статистикасын алу"""
    encoded_creds = request.cookies.get("_pc")
    if not encoded_creds:
        return web.json_response({"error": "unauthorized"}, status=401)

    creds = decode_credentials(encoded_creds)
    if not creds:
        return web.json_response({"error": "invalid_creds"}, status=401)

    username, _ = creds
    stats = push_service.get_notification_stats(username)
    return web.json_response(stats)


@routes.post("/api/push/time-settings")
async def push_update_time_settings(request):
    """Уақыт параметрлерін жаңарту"""
    encoded_creds = request.cookies.get("_pc")
    if not encoded_creds:
        return web.json_response({"error": "unauthorized"}, status=401)

    creds = decode_credentials(encoded_creds)
    if not creds:
        return web.json_response({"error": "invalid_creds"}, status=401)

    username, _ = creds
    data = await request.json()
    time_settings = data.get("time_settings", {})

    success = push_service.update_time_settings(username, time_settings)
    if success:
        return web.json_response({"status": "ok", "time_settings": time_settings})
    else:
        return web.json_response({"error": "not_subscribed"}, status=404)


@routes.get("/api/umkd")
async def get_umkd_folders(request):
    pt_token = request.get("pt_token")
    if not pt_token:
        return web.json_response({"error": "unauthorized"}, status=401)

    try:
        from datetime import date
        today = date.today()
        default_year = today.year - 1 if today.month < 9 else today.year
        default_semester = 2 if today.month < 9 else 1

        # Read parameters dynamically
        year_param = request.query.get("year")
        semester_param = request.query.get("semester")

        year = int(year_param) if year_param else default_year
        semester = int(semester_param) if semester_param else default_semester

        res = await platonus_get_umkd_list(pt_token, year, semester)
        if res is None:
            # Token might be expired, try refreshing
            pc_cookie = request.cookies.get("_pc")
            if pc_cookie:
                pt_token = await _platonus_refresh_token(pc_cookie)
                if pt_token:
                    res = await platonus_get_umkd_list(pt_token, year, semester)

        if not res or not isinstance(res, dict):
            return web.json_response([])

        records = res.get("records") or []
        folders = []
        for rec in records:
            crypt_file_id = rec.get("cryptFileId")
            if not crypt_file_id or crypt_file_id == "-":
                continue  # Skip subjects without UMKD files
                
            umkd_id = rec.get("umkdID")
            subject_id = rec.get("subjectId")
            folder_id = str(umkd_id) if umkd_id and umkd_id > 0 else f"subject_{subject_id}"
            
            subj_name = rec.get("subjectName") or ""
            tutor = rec.get("tutorName") or "Оқытушы тағайындалмаған"
            credits_val = int(rec.get("credits") or 0)
            
            folders.append({
                "id": folder_id,
                "subject": subj_name,
                "type": f"{tutor} • {credits_val} кредит"
            })
            
        return web.json_response(folders)
    except Exception as e:
        print(f"Error fetching UMKD list: {e}")
        return web.json_response([])


@routes.get("/api/umkd/{id}")
async def get_umkd_files(request):
    pt_token = request.get("pt_token")
    if not pt_token:
        return web.json_response({"error": "unauthorized"}, status=401)

    folder_id = request.match_info["id"]

    try:
        from datetime import date
        today = date.today()
        default_year = today.year - 1 if today.month < 9 else today.year
        default_semester = 2 if today.month < 9 else 1

        # Read parameters dynamically
        year_param = request.query.get("year")
        semester_param = request.query.get("semester")

        year = int(year_param) if year_param else default_year
        semester = int(semester_param) if semester_param else default_semester

        res = await platonus_get_umkd_list(pt_token, year, semester)
        if res is None:
            pc_cookie = request.cookies.get("_pc")
            if pc_cookie:
                pt_token = await _platonus_refresh_token(pc_cookie)
                if pt_token:
                    res = await platonus_get_umkd_list(pt_token, year, semester)

        if not res or not isinstance(res, dict):
            return web.json_response([])

        records = res.get("records") or []
        
        # Find the matching course record
        matching_rec = None
        for rec in records:
            umkd_id = rec.get("umkdID")
            subject_id = rec.get("subjectId")
            
            rec_folder_id = str(umkd_id) if umkd_id and umkd_id > 0 else f"subject_{subject_id}"
            if rec_folder_id == folder_id:
                matching_rec = rec
                break
                
        if not matching_rec:
            return web.json_response([])
            
        crypt_file_id = matching_rec.get("cryptFileId")
        if not crypt_file_id:
            return web.json_response([])
            
        tutor = matching_rec.get("tutorName") or "Оқытушы"
        subj_name = matching_rec.get("subjectName") or "Оқу-әдістемелік материалдар"
        
        import urllib.parse
        encoded_name = urllib.parse.quote(subj_name)
        
        file_item = {
            "name": f"{subj_name}",
            "description": "Пән бойынша барлық оқу-әдістемелік материалдардың толық жинағы (Силлабус, дәрістер конспектісі, практикалық/зертханалық сабақтардың жоспары, бақылау тапсырмалары)",
            "type": "ПОӘК жинағы",
            "language": "Қазақша/Орысша",
            "size": "Жүктеу / Download",
            "date": 1780158540,
            "downloads_count": 0,
            "teacher": tutor,
            "url": f"/api/file/{crypt_file_id}?name={encoded_name}"
        }
        
        return web.json_response([file_item])
    except Exception as e:
        print(f"Error fetching UMKD files: {e}")
        return web.json_response([])


@routes.get("/api/file/{crypt_file_id}")
async def download_file_proxy(request):
    pt_token = request.get("pt_token")
    if not pt_token:
        pt_token = request.cookies.get("_pt")
        if not pt_token:
            return web.Response(text="Unauthorized", status=401)

    crypt_file_id = request.match_info["crypt_file_id"]
    
    from functions.platonus import _decode_pt, PLATONUS_HEADERS, PLATONUS_URL, PLATONUS_TIMEOUT
    import aiohttp
    
    data = _decode_pt(pt_token)
    headers = {**PLATONUS_HEADERS, "token": data.get("t", ""), "sid": data.get("s", "")}
    cookies = data.get("c", {})
    cookies["plt_sid"] = data.get("s", "")
    
    url = f"{PLATONUS_URL}/rest/api/file/{crypt_file_id}"
    
    try:
        session = aiohttp.ClientSession(cookies=cookies, timeout=PLATONUS_TIMEOUT)
        resp = await session.get(url, headers=headers)
        
        if resp.status != 200:
            await session.close()
            return web.Response(text="Failed to download file from Platonus", status=resp.status)
            
        # Detect actual file type by reading first chunk (4KB)
        first_chunk = await resp.content.read(4096)
        
        content_type = "application/octet-stream"
        ext = ".bin"
        
        if first_chunk.startswith(b"%PDF"):
            content_type = "application/pdf"
            ext = ".pdf"
        elif first_chunk.startswith(b"PK\x03\x04"):
            content_type = "application/zip"
            ext = ".zip"
            
        # Extract custom subject name for friendly filename
        custom_name = request.query.get("name")
        if custom_name:
            import re
            # Remove characters that are dangerous for file systems
            safe_name = re.sub(r'[\\/*?:"<>|]', " ", custom_name)
            safe_name = " ".join(safe_name.split())  # Clean extra spaces
            filename = f"{safe_name}{ext}"
        else:
            filename = f"umkd_{crypt_file_id}{ext}"
            
        response = web.StreamResponse(
            status=200,
            reason="OK",
            headers={
                "Content-Type": content_type,
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
        await response.prepare(request)
        
        if first_chunk:
            await response.write(first_chunk)
            
        try:
            while True:
                chunk = await resp.content.read(65536)
                if not chunk:
                    break
                await response.write(chunk)
        finally:
            await response.write_eof()
            await session.close()
            
        return response
    except Exception as e:
        print(f"Error proxying file download: {e}")
        return web.Response(text="Internal server error", status=500)


# FAQ деректері - 3 тілде
FAQ_DATA = {
    "kk": [
        {
            "id": "1",
            "label": "Қосымшаға қалай кіремін?",
            "text": "Университеттің platonus.kstu.kz (Platonus) порталындағы логин мен құпия сөзіңізді пайдаланыңыз. Бұл деректер сіздің жеке кабинетіңізге кіру үшін қолданылады.",
        },
        {
            "id": "2",
            "label": "Бағалар қашан жаңарады?",
            "text": "Бағалар университет жүйесінен нақты уақыт режимінде алынады. Оқытушы бағаны қойған кезде ол бірден көрінеді.",
        },
        {
            "id": "3",
            "label": "Құпия сөзді қалай өзгертемін?",
            "text": "Құпия сөзді тек Platonus ресми порталында (platonus.kstu.kz) өзгерту керек. Біздің қосымша құпия сөздерді сақтамайды.",
        },
        {
            "id": "4",
            "label": "Сабақ кестесі дұрыс емес көрсетіледі",
            "text": "Кесте университет жүйесінен автоматты түрде алынады. Егер қате болса, деканатқа хабарласыңыз.",
        },
        {
            "id": "5",
            "label": "Қосымша қауіпсіз бе?",
            "text": "Иә, қосымша толық қауіпсіз. Біз сіздің деректеріңізді сақтамаймыз және тек университет жүйесімен байланысу үшін қолданамыз. Барлық байланыс шифрланған.",
        },
        {
            "id": "6",
            "label": "Интернетсіз жұмыс істей ала ма?",
            "text": "Иә, қосымша офлайн режимде жұмыс істей алады. Соңғы жүктелген деректер кэште сақталады.",
        },
        {
            "id": "7",
            "label": "Қай университеттер қолдау көрсетіледі?",
            "text": "Қазіргі уақытта ҚарТУ (Қарағанды техникалық университеті) Platonus жүйесі қолдау көрсетіледі.",
        },
        {
            "id": "8",
            "label": "GPA қалай есептеледі?",
            "text": "GPA университет жүйесінен тікелей алынады. Есептеу формуласы: барлық пәндердің кредит×балл қосындысы / жалпы кредиттер.",
        },
    ],
    "ru": [
        {
            "id": "1",
            "label": "Как войти в приложение?",
            "text": "Используйте логин и пароль от портала platonus.kstu.kz (Platonus). Эти данные используются для доступа к вашему личному кабинету.",
        },
        {
            "id": "2",
            "label": "Когда обновляются оценки?",
            "text": "Оценки получаются из системы университета в реальном времени. Как только преподаватель поставит оценку, она сразу отобразится.",
        },
        {
            "id": "3",
            "label": "Как изменить пароль?",
            "text": "Пароль можно изменить только на официальном портале Platonus (platonus.kstu.kz). Наше приложение не хранит пароли.",
        },
        {
            "id": "4",
            "label": "Расписание отображается неправильно",
            "text": "Расписание автоматически загружается из системы университета. Если есть ошибка, обратитесь в деканат.",
        },
        {
            "id": "5",
            "label": "Безопасно ли приложение?",
            "text": "Да, приложение полностью безопасно. Мы не храним ваши данные и используем их только для связи с системой университета. Все соединения зашифрованы.",
        },
        {
            "id": "6",
            "label": "Работает ли без интернета?",
            "text": "Да, приложение может работать в офлайн режиме. Последние загруженные данные сохраняются в кэше.",
        },
        {
            "id": "7",
            "label": "Какие университеты поддерживаются?",
            "text": "В настоящее время поддерживается система Platonus КарТУ (Карагандинского технического университета).",
        },
        {
            "id": "8",
            "label": "Как рассчитывается GPA?",
            "text": "GPA получается напрямую из системы университета. Формула расчета: сумма (кредиты × баллы) всех предметов / общее количество кредитов.",
        },
    ],
    "en": [
        {
            "id": "1",
            "label": "How do I log in?",
            "text": "Use your login and password from the platonus.kstu.kz (Platonus) portal. These credentials are used to access your personal account.",
        },
        {
            "id": "2",
            "label": "When are grades updated?",
            "text": "Grades are fetched from the university system in real-time. As soon as a teacher enters a grade, it will be displayed immediately.",
        },
        {
            "id": "3",
            "label": "How do I change my password?",
            "text": "You can only change your password on the official Platonus portal (platonus.kstu.kz). Our app does not store passwords.",
        },
        {
            "id": "4",
            "label": "The schedule is displayed incorrectly",
            "text": "The schedule is automatically loaded from the university system. If there is an error, please contact the dean's office.",
        },
        {
            "id": "5",
            "label": "Is the app secure?",
            "text": "Yes, the app is completely secure. We do not store your data and only use it to communicate with the university system. All connections are encrypted.",
        },
        {
            "id": "6",
            "label": "Does it work offline?",
            "text": "Yes, the app can work in offline mode. The last loaded data is saved in the cache.",
        },
        {
            "id": "7",
            "label": "Which universities are supported?",
            "text": "Currently, KarTU (Karaganda Technical University) Platonus system is supported.",
        },
        {
            "id": "8",
            "label": "How is GPA calculated?",
            "text": "GPA is obtained directly from the university system. Calculation formula: sum of (credits × points) for all subjects / total credits.",
        },
    ],
}

# Құпиялылық саясаты - 3 тілде
PRIVACY_POLICY = {
    "kk": """
<h1>Құпиялылық саясаты</h1>
<p><strong>Соңғы жаңарту:</strong> 2026 жылғы ақпан</p>

<h2>1. Кіріспе</h2>
<p>Platonus қосымшасы (бұдан әрі – «Қосымша») сіздің жеке деректеріңіздің қауіпсіздігін қамтамасыз етуге міндеттенеді. Бұл құпиялылық саясаты біздің деректерді қалай жинайтынымызды, пайдаланатынымызды және қоргайтынымызды түсіндіреді.</p>

<h2>2. Жиналатын деректер</h2>
<p>Біз келесі деректерді жинаймыз:</p>
<ul>
<li>Университет жүйесіне кіру үшін логин (тек сессия уақытында)</li>
<li>Сабақ кестесі, бағалар және транскрипт деректері (тек көрсету үшін)</li>
</ul>

<h2>3. Деректерді сақтау</h2>
<p><strong>Маңызды:</strong> Біз сіздің құпия сөзіңізді серверде САҚТАМАЙМЫЗ. Барлық аутентификация тікелей университет серверлерімен жүргізіледі.</p>

<h2>4. Деректерді пайдалану</h2>
<p>Жиналған деректер тек:</p>
<ul>
<li>Сізге сабақ кестесін көрсету үшін</li>
<li>Бағалар мен үлгерім туралы ақпаратты көрсету үшін</li>
<li>Қосымша функционалдығын қамтамасыз ету үшін</li>
</ul>

<h2>5. Деректерді қорғау</h2>
<p>Біз деректеріңіздің қауіпсіздігін қамтамасыз ету үшін:</p>
<ul>
<li>SSL/TLS шифрлауын қолданамыз</li>
<li>Деректерді үшінші тараптарға бермейміз</li>
<li>Серверлік қауіпсіздік шараларын қолданамыз</li>
</ul>

<h2>6. Cookies файлдары</h2>
<p>Қосымша сессияны басқару үшін cookies файлдарын қолданады. Бұл университет жүйесімен байланысу үшін қажет.</p>

<h2>7. Сіздің құқықтарыңыз</h2>
<p>Сізде келесі құқықтар бар:</p>
<ul>
<li>Деректеріңізді жою (жүйеден шығу арқылы)</li>
<li>Cookies файлдарынан бас тарту</li>
<li>Қосымшаны кез келген уақытта пайдалануды тоқтату</li>
</ul>

<h2>8. Байланыс</h2>
<p>Сұрақтарыңыз болса, университетіңіздің техникалық қолдау қызметіне хабарласыңыз.</p>
""",
    "ru": """
<h1>Политика конфиденциальности</h1>
<p><strong>Последнее обновление:</strong> Февраль 2026</p>

<h2>1. Введение</h2>
<p>Приложение Platonus (далее – «Приложение») обязуется обеспечивать безопасность ваших персональных данных. Настоящая политика конфиденциальности объясняет, как мы собираем, используем и защищаем данные.</p>

<h2>2. Собираемые данные</h2>
<p>Мы собираем следующие данные:</p>
<ul>
<li>Логин для входа в систему университета (только на время сессии)</li>
<li>Данные расписания, оценок и транскрипта (только для отображения)</li>
</ul>

<h2>3. Хранение данных</h2>
<p><strong>Важно:</strong> Мы НЕ ХРАНИМ ваш пароль на сервере. Вся аутентификация происходит напрямую с серверами университета.</p>

<h2>4. Использование данных</h2>
<p>Собранные данные используются только для:</p>
<ul>
<li>Отображения расписания занятий</li>
<li>Показа информации об оценках и успеваемости</li>
<li>Обеспечения функциональности приложения</li>
</ul>

<h2>5. Защита данных</h2>
<p>Для обеспечения безопасности ваших данных мы:</p>
<ul>
<li>Используем SSL/TLS шифрование</li>
<li>Не передаём данные третьим лицам</li>
<li>Применяем серверные меры безопасности</li>
</ul>

<h2>6. Файлы cookies</h2>
<p>Приложение использует файлы cookies для управления сессией. Это необходимо для связи с системой университета.</p>

<h2>7. Ваши права</h2>
<p>У вас есть следующие права:</p>
<ul>
<li>Удаление ваших данных (путём выхода из системы)</li>
<li>Отказ от файлов cookies</li>
<li>Прекращение использования приложения в любое время</li>
</ul>

<h2>8. Контакты</h2>
<p>При возникновении вопросов обращайтесь в службу технической поддержки вашего университета.</p>
""",
    "en": """
<h1>Privacy Policy</h1>
<p><strong>Last updated:</strong> February 2026</p>

<h2>1. Introduction</h2>
<p>The Platonus application (hereinafter – "Application") is committed to ensuring the security of your personal data. This privacy policy explains how we collect, use, and protect data.</p>

<h2>2. Data Collected</h2>
<p>We collect the following data:</p>
<ul>
<li>Login credentials for university system access (session duration only)</li>
<li>Schedule, grades, and transcript data (for display purposes only)</li>
</ul>

<h2>3. Data Storage</h2>
<p><strong>Important:</strong> We DO NOT STORE your password on our server. All authentication is done directly with university servers.</p>

<h2>4. Data Usage</h2>
<p>Collected data is used only for:</p>
<ul>
<li>Displaying your class schedule</li>
<li>Showing grades and academic performance information</li>
<li>Ensuring application functionality</li>
</ul>

<h2>5. Data Protection</h2>
<p>To ensure your data security, we:</p>
<ul>
<li>Use SSL/TLS encryption</li>
<li>Do not share data with third parties</li>
<li>Apply server-side security measures</li>
</ul>

<h2>6. Cookies</h2>
<p>The application uses cookies for session management. This is necessary for communication with the university system.</p>

<h2>7. Your Rights</h2>
<p>You have the following rights:</p>
<ul>
<li>Delete your data (by logging out)</li>
<li>Opt out of cookies</li>
<li>Stop using the application at any time</li>
</ul>

<h2>8. Contact</h2>
<p>If you have any questions, please contact your university's technical support service.</p>
""",
}


@routes.get("/api/version")
async def get_version(request):
    return web.json_response("1.01")


@routes.get("/faq")
async def get_faq(request):
    lang = request.query.get("lang", "ru")
    if lang not in FAQ_DATA:
        lang = "ru"
    return web.json_response(FAQ_DATA[lang])


@routes.get("/faq/{id}")
async def get_faq_item(request):
    item_id = request.match_info["id"]
    lang = request.query.get("lang", "ru")
    if lang not in FAQ_DATA:
        lang = "ru"

    # Сұрақты табу
    item = next((i for i in FAQ_DATA[lang] if i["id"] == item_id), None)
    if not item:
        return web.Response(text="<h1>FAQ табылған жоқ</h1>", content_type="text/html")

    # HTML форматында қайтару (Frontend h1-ді қолданады)
    html = f"<h1>{item['label']}</h1>\n<p>{item['text']}</p>"
    return web.Response(text=html, content_type="text/html")


@routes.get("/api/privacy-policy")
async def get_privacy(request):
    lang = request.query.get("lang", "ru")
    if lang not in PRIVACY_POLICY:
        lang = "ru"
    return web.json_response({"text": PRIVACY_POLICY[lang]})


@routes.get("/auth/logout")
async def logout(request):
    response = web.json_response({"status": "ok"})
    response.del_cookie("_pt")
    response.del_cookie("_pc")
    response.del_cookie("_pl")
    response.del_cookie(".ASPXAUTH")
    response.del_cookie("ASP.NET_SessionId")
    return response


# Frontend Routes
@routes.get("/health")
async def health_check(request):
    """Health check endpoint for Railway"""
    return web.json_response({"status": "ok", "service": "platonus"})


@routes.get("/")
async def index(request):
    return web.FileResponse(os.path.join(CLIENT_DIR, "index.html"))


# Басқа frontend route-тарды index.html-ге бағыттау (SPA үшін)
# Мысалы /login, /schedule, т.б.
# Бұны қалай дұрыс істеу керек? wildcard route қолдануға болады, бірақ api-мен шатаспау керек.


async def frontend_handler(request):
    # Егер файл табылса (assets), соны береміз
    # Әйтпесе index.html береміз (client side routing)

    path = request.match_info.get("path", "")

    # Файлдың нақты жолы
    file_path = os.path.join(CLIENT_DIR, path)

    if os.path.exists(file_path) and os.path.isfile(file_path):
        return web.FileResponse(file_path)

    # Егер API емес болса және файл табылмаса -> index.html
    return web.FileResponse(os.path.join(CLIENT_DIR, "index.html"))


async def on_startup(app):
    """Сервер қосылғанда орындалатын іс-шаралар"""
    try:
        await scheduled_notifications.start()
        print("Background tasks started")
    except Exception as e:
        print(f"Warning: Background tasks failed to start: {e}")
        print("Server will continue without background tasks")


async def on_cleanup(app):
    """Сервер тоқтағанда орындалатын іс-шаралар"""
    await scheduled_notifications.stop()
    print("Background tasks stopped")


# App setup
app = web.Application(middlewares=[cors_middleware, platonus_middleware])
app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)
app.add_routes(routes)
app.router.add_get("/{path:.*}", frontend_handler)  # Catch-all for frontend

if __name__ == "__main__":
    try:
        bound_sock, selected_port, source = resolve_startup_socket()
    except ValueError as e:
        print(f"Startup error: {e}")
        raise SystemExit(1)
    except OSError as e:
        print(f"Startup error: {e}")
        raise SystemExit(1)

    print(f"Starting server on port {selected_port} (source: {source})")
    web.run_app(app, sock=bound_sock)
