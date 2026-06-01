# Security Policy

Univer Platonus студенттердің Platonus аккаунты арқылы оқу деректерін көрсетеді. Сондықтан authentication, cookies, token refresh және log hygiene ерекше маңызды.

## Қолдау көрсетілетін нұсқалар

| Нұсқа | Қолдау |
| --- | --- |
| 1.x | Қолдау көрсетіледі |
| 0.x | Қолдау көрсетілмейді |

## Осалдық туралы хабарлау

Қауіпсіздік мәселесін тапсаңыз, public Issue ашпаңыз.

Хабарламада мыналарды көрсетіңіз:

- Осалдық түрі.
- Қай endpoint немесе экран.
- Қай нұсқа/commit.
- Қайта шығару қадамдары.
- Impact: қандай дерекке немесе user flow-ға әсер етеді.
- Мүмкін болса, proof of concept.

Құпия деректерді, нақты студент аккаунтын, cookie немесе token-ді толық күйінде жібермеңіз. Қажет болса, redacted формат қолданыңыз.

## Қауіпсіздік принциптері

- Құпия сөздер backend дерекқорында сақталмауы керек.
- Cookie мүмкіндігінше `HttpOnly`, `Secure`, `SameSite` параметрлерімен берілуі керек.
- Token refresh flow тек керек endpoint-терде жүруі керек.
- Құпия деректер log-қа жазылмауы керек.
- Public API endpoint-тері нақты whitelisted болуы керек.
- Frontend localStorage ішінде password сақтаудан аулақ болу керек.
- Third-party portal response-тарын user-facing parser арқылы ғана көрсету керек.

## Құпия деректер

Public repo-ға мыналарды commit етпеңіз:

- Platonus логиндері мен құпия сөздері.
- Session cookie.
- API token.
- Private VAPID key.
- Production database dump.
- ЖСН немесе studentID бар raw response.

Егер құпия дерек commit-ке түссе:

1. Дереу revoke/rotate жасаңыз.
2. Commit history cleanup қажет пе, бағалаңыз.
3. Жоба maintainer-іне хабарлаңыз.
4. Қай дерек exposed болғанын құжаттаңыз.

## Backend risk checklist

- [ ] Auth-required endpoint middleware-пен қорғалған.
- [ ] Public endpoint нақты қажет.
- [ ] Timeout бар.
- [ ] 401/403 refresh flow дұрыс.
- [ ] Exception user-ға құпия stack trace қайтармайды.
- [ ] Cookie flags тексерілген.
- [ ] Sensitive value log-қа жазылмайды.

## Frontend risk checklist

- [ ] Password/token DOM-да немесе console log-та шықпайды.
- [ ] Error message құпия backend detail ашпайды.
- [ ] External links `rel="noopener noreferrer"` қолданады.
- [ ] PWA cache sensitive API response сақтамайды.
- [ ] Login және logout flow тексерілген.

## Жауап беру тәртібі

1. Хабарлама қабылданады.
2. Осалдық қайта шығарылады.
3. Severity бағаланады.
4. Fix дайындалады.
5. Deploy жасалады.
6. Қажет болса changelog/security note жазылады.

## Белгілі шектеулер

- Қосымша сыртқы Platonus порталдарының тұрақтылығына тәуелді.
- Әр университеттің Platonus нұсқасы әртүрлі болуы мүмкін.
- Public/shared құрылғыда аккаунттан шығуды ұмытпау керек.
