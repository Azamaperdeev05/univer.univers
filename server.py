from aiohttp import web
from dataclasses import asdict
import json
import os
import sys
import base64

# Core папкасын path-қа қосу (импорттар жұмыс істеуі үшін)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))

from univers import KSTU, KazNU, get_univer
from univers.base import Univer
from functions.login import UserCookies
from exceptions import ForbiddenException, InvalidCredential
from push_notifications import push_service, scheduled_notifications

# Frontend static папкасының жолы
CLIENT_DIR = os.path.join(os.path.dirname(__file__), "static")

routes = web.RouteTableDef()


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


# Univer объектісін алу үшін көмекші функция
def get_user_univer(request) -> Univer:
    # Сессиядан немесе cookie-ден деректерді алу керек
    # Бұл жерде қарапайым болу үшін cookie-ден оқимыз деп болжаймыз
    # Шын мәнінде, client жағы token мен session_id жіберуі керек
    # Қазірше login арқылы алынған cookie-лерді қалай сақтайтынын қарастыру керек
    # Client secure-storage-тен оқып headers-ке қоса ма?
    # auth.svelte.ts қарасақ credentials: "include" бар.
    # Демек cookies серверге келеді.
    pass


# Login handler
@routes.post("/auth/login")
async def login(request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    university = data.get("univer")  # 'kstu' or 'kaznu' or url

    try:
        UniverClass = get_univer(university)  # Егер университет атымен келсе
        if not UniverClass:
            # Егер url болса, мүмкін kstu деп default алу керек пе?
            # univer.client логикасында универ қалай таңдалады?
            UniverClass = KSTU

        # Инстанция құру
        univer = UniverClass()

        # Логин жасау (бұл aiohttp session қолданады)
        cookies = await univer.login(username, password)

        response = web.json_response({"status": "ok"})
        # Cookie-лерді орнату
        response.set_cookie(".ASPXAUTH", cookies.token, httponly=True)
        response.set_cookie("ASP.NET_SessionId", cookies.session_id, httponly=True)
        response.set_cookie("univer_code", university)  # Қай универ екенін сақтау

        # Credentials-ты cookie-ге шифрлап сақтау (автоматты жаңарту үшін)
        encoded_creds = encode_credentials(username, password)
        response.set_cookie(
            "_uc", encoded_creds, httponly=True
        )  # _uc = user credentials

        return response
    except Exception as e:
        return web.json_response({"error": str(e)}, status=401)


# Helper функция - API қателерін дұрыс handle ету және токенді автоматты жаңарту
async def handle_api_error(e: Exception, request):
    """API қатесін дұрыс өңдеу - сессия аяқталса қайта кіру"""
    if isinstance(e, ForbiddenException):
        # Сессия аяқталған - credentials арқылы қайта кіру
        encoded_creds = request.get("encoded_creds")
        univer_code = request.cookies.get("univer_code", "kstu")

        if encoded_creds:
            creds = decode_credentials(encoded_creds)
            if creds:
                username, password = creds
                try:
                    UniverClass = get_univer(univer_code) or KSTU
                    univer = UniverClass()
                    new_cookies = await univer.login(username, password)

                    # Жаңа cookies-пен redirect жасау (client retry етеді)
                    response = web.json_response(
                        {
                            "error": "session_refreshed",
                            "message": "Сессия жаңартылды. Қайталаңыз.",
                        },
                        status=401,
                    )
                    response.set_cookie(".ASPXAUTH", new_cookies.token, httponly=True)
                    response.set_cookie(
                        "ASP.NET_SessionId", new_cookies.session_id, httponly=True
                    )
                    return response
                except InvalidCredential:
                    # Пароль ауысқан - барлығын тазалап login-ге жіберу
                    response = web.json_response(
                        {
                            "error": "credentials_changed",
                            "message": "Құпия сөз өзгерген. Қайта кіріңіз.",
                        },
                        status=401,
                    )
                    response.del_cookie(".ASPXAUTH")
                    response.del_cookie("ASP.NET_SessionId")
                    response.del_cookie("_uc")
                    return response
                except Exception:
                    pass

        # Credentials жоқ немесе қате - login-ге жіберу
        return web.json_response(
            {
                "error": "session_expired",
                "message": "Сессия мерзімі бітті. Қайта кіріңіз.",
            },
            status=401,
        )
    return web.json_response({"error": str(e)}, status=500)


# API middleware - Univer объектісін дайындау және токенді автоматты жаңарту
async def univer_middleware(app, handler):
    async def middleware_handler(request):
        if request.path.startswith("/api/"):
            token = request.cookies.get(".ASPXAUTH")
            session_id = request.cookies.get("ASP.NET_SessionId")
            univer_code = request.cookies.get("univer_code", "kstu")
            encoded_creds = request.cookies.get("_uc")  # encrypted credentials

            if not token or not session_id:
                # Токен жоқ, бірақ credentials бар ма?
                if encoded_creds:
                    # Credentials арқылы қайта кіру
                    creds = decode_credentials(encoded_creds)
                    if creds:
                        username, password = creds
                        try:
                            UniverClass = get_univer(univer_code) or KSTU
                            univer = UniverClass()
                            new_cookies = await univer.login(username, password)

                            # Жаңа cookies-пен univer дайындау
                            request["univer"] = UniverClass(cookies=new_cookies)
                            request["new_cookies"] = (
                                new_cookies  # Response-та update жасау үшін
                            )
                            return await handler(request)
                        except InvalidCredential:
                            # Пароль ауысқан - барлығын тазалап login-ге жіберу
                            response = web.json_response(
                                {
                                    "error": "credentials_changed",
                                    "message": "Құпия сөз өзгерген. Қайта кіріңіз.",
                                },
                                status=401,
                            )
                            response.del_cookie(".ASPXAUTH")
                            response.del_cookie("ASP.NET_SessionId")
                            response.del_cookie("_uc")
                            return response
                        except Exception:
                            pass

                return web.json_response(
                    {"error": "unauthorized", "message": "Авторизация қажет"},
                    status=401,
                )

            cookies = UserCookies(token=token, session_id=session_id, username="")
            UniverClass = get_univer(univer_code) or KSTU
            request["univer"] = UniverClass(cookies=cookies)
            request["encoded_creds"] = encoded_creds  # Қайта кіру үшін сақтау

        return await handler(request)

    return middleware_handler


@routes.get("/api/schedule")
async def get_schedule(request):
    univer: Univer = request["univer"]
    # Тілді алу (query params: lang)
    lang = request.query.get("lang", "ru")
    univer.language = lang

    try:
        schedule = await univer.get_schedule()
        return web.json_response(
            asdict(schedule), dumps=lambda x: json.dumps(x, default=str)
        )
    except Exception as e:
        return await handle_api_error(e, request)


@routes.get("/api/transcript")
async def get_transcript(request):
    univer: Univer = request["univer"]
    try:
        transcript = await univer.get_transcript()
        return web.json_response(
            asdict(transcript), dumps=lambda x: json.dumps(x, default=str)
        )
    except Exception as e:
        return await handle_api_error(e, request)


@routes.get("/api/attestation")
async def get_attestation(request):
    univer: Univer = request["univer"]
    try:
        attestation = await univer.get_attestation()
        # тізімді dict-ке айналдыру немесе сол күйінде жіберу
        # attestation - бұл список
        return web.json_response(
            [asdict(a) for a in attestation], dumps=lambda x: json.dumps(x, default=str)
        )
    except Exception as e:
        return await handle_api_error(e, request)


@routes.get("/api/exams")
async def get_exams(request):
    univer: Univer = request["univer"]
    try:
        exams = await univer.get_exams()
        return web.json_response(
            [asdict(e) for e in exams], dumps=lambda x: json.dumps(x, default=str)
        )
    except Exception as e:
        return await handle_api_error(e, request)


@routes.post("/api/push/subscribe")
async def push_subscribe(request):
    data = await request.json()
    encoded_creds = request.get("encoded_creds")
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
    encoded_creds = request.get("encoded_creds")
    if not encoded_creds:
        return web.json_response({"error": "unauthorized"}, status=401)

    creds = decode_credentials(encoded_creds)
    if not creds:
        return web.json_response({"error": "invalid_creds"}, status=401)

    username, _ = creds
    push_service.unsubscribe(username)

    return web.json_response({"status": "ok"})
    # Тілді алу
    lang = request.query.get("lang", "ru")
    univer.language = lang

    try:
        exams = await univer.get_exams()
        return web.json_response(
            [asdict(e) for e in exams], dumps=lambda x: json.dumps(x, default=str)
        )
    except Exception as e:
        return await handle_api_error(e, request)


@routes.get("/api/umkd")
async def get_umkd_folders(request):
    univer: Univer = request["univer"]
    lang = request.query.get("lang", "ru")
    univer.language = lang
    try:
        folders = await univer.get_umkd()
        return web.json_response(
            [asdict(f) for f in folders], dumps=lambda x: json.dumps(x, default=str)
        )
    except Exception as e:
        return await handle_api_error(e, request)


@routes.get("/api/umkd/{id}")
async def get_umkd_files(request):
    univer: Univer = request["univer"]
    subject_id = request.match_info["id"]
    lang = request.query.get("lang", "ru")
    univer.language = lang
    try:
        files = await univer.get_umkd_files(subject_id)
        return web.json_response(
            [asdict(f) for f in files], dumps=lambda x: json.dumps(x, default=str)
        )
    except Exception as e:
        return await handle_api_error(e, request)


# FAQ деректері - 3 тілде
FAQ_DATA = {
    "kk": [
        {
            "id": "1",
            "label": "Қосымшаға қалай кіремін?",
            "text": "Университеттің univer.kstu.kz немесе univer.kaznu.kz порталындағы логин мен құпия сөзіңізді пайдаланыңыз. Бұл деректер сіздің жеке кабинетіңізге кіру үшін қолданылады.",
        },
        {
            "id": "2",
            "label": "Бағалар қашан жаңарады?",
            "text": "Бағалар университет жүйесінен нақты уақыт режимінде алынады. Оқытушы бағаны қойған кезде ол бірден көрінеді.",
        },
        {
            "id": "3",
            "label": "Құпия сөзді қалай өзгертемін?",
            "text": "Құпия сөзді тек университеттің ресми порталында (univer.kstu.kz немесе univer.kaznu.kz) өзгерту керек. Біздің қосымша құпия сөздерді сақтамайды.",
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
            "text": "Қазіргі уақытта KSTU (Қарағанды техникалық университеті) және KazNU (Әл-Фараби атындағы Қазақ ұлттық университеті) қолдау көрсетіледі.",
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
            "text": "Используйте логин и пароль от портала univer.kstu.kz или univer.kaznu.kz. Эти данные используются для доступа к вашему личному кабинету.",
        },
        {
            "id": "2",
            "label": "Когда обновляются оценки?",
            "text": "Оценки получаются из системы университета в реальном времени. Как только преподаватель поставит оценку, она сразу отобразится.",
        },
        {
            "id": "3",
            "label": "Как изменить пароль?",
            "text": "Пароль можно изменить только на официальном портале университета (univer.kstu.kz или univer.kaznu.kz). Наше приложение не хранит пароли.",
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
            "text": "В настоящее время поддерживаются KSTU (Карагандинский технический университет) и KazNU (Казахский национальный университет им. аль-Фараби).",
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
            "text": "Use your login and password from the univer.kstu.kz or univer.kaznu.kz portal. These credentials are used to access your personal account.",
        },
        {
            "id": "2",
            "label": "When are grades updated?",
            "text": "Grades are fetched from the university system in real-time. As soon as a teacher enters a grade, it will be displayed immediately.",
        },
        {
            "id": "3",
            "label": "How do I change my password?",
            "text": "You can only change your password on the official university portal (univer.kstu.kz or univer.kaznu.kz). Our app does not store passwords.",
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
            "text": "Currently, KSTU (Karaganda Technical University) and KazNU (Al-Farabi Kazakh National University) are supported.",
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
<p>Univer қосымшасы (бұдан әрі – «Қосымша») сіздің жеке деректеріңіздің қауіпсіздігін қамтамасыз етуге міндеттенеді. Бұл құпиялылық саясаты біздің деректерді қалай жинайтынымызды, пайдаланатынымызды және қорғайтынымызды түсіндіреді.</p>

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
<p>Приложение Univer (далее – «Приложение») обязуется обеспечивать безопасность ваших персональных данных. Настоящая политика конфиденциальности объясняет, как мы собираем, используем и защищаем данные.</p>

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
<p>The Univer application (hereinafter – "Application") is committed to ensuring the security of your personal data. This privacy policy explains how we collect, use, and protect data.</p>

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
    response.del_cookie(".ASPXAUTH")
    response.del_cookie("ASP.NET_SessionId")
    response.del_cookie("_uc")  # Credentials cookie-ін де жою
    response.del_cookie("univer_code")  # Университет кодын да жою
    return response


# Frontend Routes
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
    await scheduled_notifications.start()
    print("Background tasks started")


async def on_cleanup(app):
    """Сервер тоқтағанда орындалатын іс-шаралар"""
    await scheduled_notifications.stop()
    print("Background tasks stopped")


# App setup
app = web.Application(middlewares=[univer_middleware])
app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)
app.add_routes(routes)
app.router.add_get("/{path:.*}", frontend_handler)  # Catch-all for frontend

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7435))
    web.run_app(app, port=port)
