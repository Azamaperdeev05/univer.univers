# Contributing

Univer Platonus жобасына үлес қосқыңыз келсе, осы нұсқаулықты ұстаныңыз. Жобаның басты мақсаты - студенттерге нақты, жылдам және түсінікті дерек көрсету.

## Бастамас бұрын

- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) ережелерін оқыңыз.
- Ашық Issue бар-жоғын тексеріңіз.
- UI өзгерісі болса, mobile viewport-ты міндетті түрде тексеріңіз.
- Auth, cookie, password, token flow өзгерсе, security risk-ті бөлек сипаттаңыз.

## Жергілікті орта

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Frontend:

```bash
cd univer.client
pnpm install
pnpm dev
```

Production build:

```bash
cd univer.client
pnpm build
```

## Branch атауы

Ұсынылатын формат:

```text
feature/short-name
fix/short-name
docs/short-name
refactor/short-name
```

Мысал:

```bash
git checkout -b fix/enu-gradebook-aa
```

## Commit стилі

Commit қысқа және нақты болсын:

```text
fix: parse ENU differentiated credit marks
docs: refresh SEO setup instructions
feat: add university selector to login
```

Үлкен өзгерісті бірнеше commit-ке бөліңіз: backend parser, frontend UI, docs, tests.

## Pull Request

PR сипаттамасында мыналар болсын:

- Не өзгерді.
- Неге өзгерді.
- Қалай тексерілді.
- Қандай risk қалды.
- UI өзгерісі болса, screenshot немесе қысқа видео.
- Backend интеграция болса, нақты endpoint және sample response.

Минималды PR checklist:

- [ ] Build немесе syntax check өтті.
- [ ] Негізгі user flow қолмен тексерілді.
- [ ] Mobile viewport тексерілді.
- [ ] Құпия дерек commit-ке кірмеді.
- [ ] Құжаттама қажет болса жаңартылды.

## Қате туралы хабарлау

Issue ашқанда:

1. Қандай бет немесе endpoint.
2. Қандай университет.
3. Қай семестр/оқу жылы.
4. Күтілген нәтиже.
5. Нақты нәтиже.
6. Скриншот немесе redacted response.
7. Browser/OS/device.

Құпия сөз, token, cookie, ЖСН сияқты деректерді public Issue-ға жазбаңыз.

## Жаңа мүмкіндік ұсыну

Feature proposal ішінде:

- Қай user problem шешіледі.
- Қандай экран немесе API өзгереді.
- Қай университеттерге әсер етеді.
- Offline/PWA behavior қалай болады.
- Қауіпсіздікке әсері бар ма.

## Код стилі

### Python

- `async` flow-ды blocking call-мен араластырмаңыз.
- Network timeout қойыңыз.
- Broad `except` қолдансаңыз, кемінде лог немесе fallback болсын.
- Parser логикасын нақты mark name variant-тарымен тексеріңіз.

### Svelte/TypeScript

- Бар компоненттер мен Tailwind semantic class-тарын қолданыңыз.
- Mobile layout-та fixed/floating navigation overlap тексеріңіз.
- Svelte 5 runes қолданылған жерлерде state/derived логикасын сақтаңыз.
- UI text i18n арқылы берілгені дұрыс.

### CSS/UI

- Қараңғы және жарық тақырыпты бірге тексеріңіз.
- Text overlap, clipped card, nav астында қалған content болмауы керек.
- Тек декоративті элемент үшін үлкен layout shift жасамаңыз.

## Қауіпсіздік

Қауіпсіздік мәселесін public Issue ретінде ашпаңыз. [SECURITY.md](SECURITY.md) нұсқаулығын қолданыңыз.

## Құжаттама

Жаңа feature user-facing болса, README немесе ROADMAP жаңартыңыз. Deploy, SEO, auth, parser behavior өзгерсе, құжаттаманы міндетті түрде жаңарту керек.
