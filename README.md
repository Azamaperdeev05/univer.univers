<div align="center">

<img src="univer.client/public/images/logo.svg" alt="Univer Platonus logo" width="120">

# Univer Platonus

Қазақстан студенттеріне арналған Platonus деректерін ыңғайлы көрсететін PWA.

[univerkstu.site](https://univerkstu.site) · [Telegram](https://t.me/univerkstusite) · [Issues](../../issues)

<img src="univer.client/public/images/banner.png" alt="Univer Platonus banner" width="720">

</div>

## Жоба туралы

Univer Platonus - Platonus жүйесіндегі сабақ кестесін, бағаларды, емтихан ақпаратын, транскриптті және оқу материалдарын бір интерфейсте көрсететін веб-қосымша. Қосымша мобильді экранға бейімделген және PWA ретінде орнатылады.

Бұл ресми университет жүйесін алмастырмайды. Қосымша студенттің Platonus аккаунты арқылы деректерді оқып, оларды түсінікті интерфейске жинақтайды.

## Мүмкіндіктер

- Сабақ кестесін көру.
- Ағымдағы бағалар мен аттестацияларды көру.
- ENU сияқты өзгеше бағалау формуласы бар университеттерді өңдеу.
- Емтихан кестесін және GPA ақпаратын қарау.
- Транскрипт пен оқу материалдарын ашу.
- Баға калькуляторын қолдану.
- Push хабарламаларды қосу.
- Жарық, қараңғы және жүйелік тақырыпты таңдау.
- Қазақ, орыс және ағылшын тілдері.
- Android/iOS браузерлерінде PWA ретінде орнату.

## Қолдау көрсетілетін университеттер

Қосымша Platonus порталдары бар бірнеше университетпен жұмыс істеуге арналған. Қазіргі конфигурацияда ҚарТУ, Buketov University, ENU, KazATU, MNU, AlmaU, Narxoz, AUES және басқа Platonus порталдары бар оқу орындары көрсетілген.

Логин бетінде "Автоматты анықтау" режимі бар. Егер автоматты режим сәйкес университетті таппаса, университетті қолмен таңдауға болады.

## Технологиялар

- Backend: Python 3.11, aiohttp.
- Frontend: Svelte 5, TypeScript, Vite.
- UI: Tailwind CSS, bits-ui, lucide-svelte.
- PWA: vite-plugin-pwa, service worker, web manifest.
- Deploy: Docker, Railway-compatible startup.

## Жоба құрылымы

```text
.
├── core/                 # Platonus интеграциясы және backend helper-лері
├── static/               # Production frontend build және public файлдар
├── univer.client/        # Svelte/Vite frontend
├── server.py             # aiohttp backend және static file serving
├── requirements.txt      # Python тәуелділіктері
├── Dockerfile            # Production image
└── railway.toml          # Railway deploy конфигурациясы
```

## Жергілікті іске қосу

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

Әдеткі порттар:

- Backend: `7435`, бос болмаса `7436..7499`.
- Frontend dev server: `5173`.

Егер `PORT` environment variable берілсе, backend сол портқа ғана bind жасайды.

## Build

Frontend production build:

```bash
cd univer.client
pnpm build
```

Vite build нәтижесі root ішіндегі `static/` папкасына жазылады. Backend production режимінде осы папканы serve етеді.

Docker build:

```bash
docker build -t univer-platonus .
docker run -p 7435:7435 univer-platonus
```

## SEO және Google verification

Жоба root-та Google Search Console verification файлын, `robots.txt`, `sitemap.xml`, canonical meta, Open Graph meta және JSON-LD structured data қолданады.

Deploy жасағаннан кейін Search Console ішінде:

1. `https://univerkstu.site/google6b11bbffd33748dd.html` арқылы сайтты растау.
2. `https://univerkstu.site/sitemap.xml` sitemap ретінде жіберу.
3. Негізгі URL үшін indexing request жасау.

Google-да бірінші орынға шығуға кепілдік жоқ. Бірақ техникалық SEO, жылдамдық, пайдалы контент және сыртқы сілтемелер ranking-ті жақсартады.

## Қауіпсіздік

Құпия сөздер backend дерекқорында сақталмайды. Session үшін Platonus token және refresh логикасы cookie арқылы өңделеді. Қауіпсіздік мәселесін тапсаңыз, public Issue ашпай, [SECURITY.md](SECURITY.md) нұсқаулығын қолданыңыз.

## Қатысу

Жобаға үлес қосу тәртібі [CONTRIBUTING.md](CONTRIBUTING.md) ішінде жазылған. Мінез-құлық ережелері [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) файлында.

## Лицензия

Бұл жоба [MIT License](LICENSE) бойынша таратылады.
