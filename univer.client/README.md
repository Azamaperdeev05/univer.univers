# Univer Platonus Frontend

Бұл папкада Univer Platonus қосымшасының Svelte/Vite frontend бөлігі орналасқан.

## Stack

- Svelte 5.
- TypeScript.
- Vite.
- Tailwind CSS.
- bits-ui.
- lucide-svelte.
- vite-plugin-pwa.

## Іске қосу

```bash
pnpm install
pnpm dev
```

Dev server әдетте `http://localhost:5173` ашады. API dev режимінде `http://localhost:7435` backend-іне сұрау жібереді.

Backend root папкадан іске қосылады:

```bash
cd ..
python server.py
```

## Build

```bash
pnpm build
```

Build нәтижесі root ішіндегі `static/` папкасына жазылады. Бұл Vite config ішіндегі `outDir: "../static"` арқылы жасалады.

Preview:

```bash
pnpm preview
```

## Check

```bash
pnpm check
```

Бұл команда `svelte-check` және TypeScript config тексерісін жүргізеді.

## Құрылым

```text
src/
├── api/              # Backend API wrapper және auth/session helper-лері
├── lib/              # UI компоненттер, router, i18n, theme
├── pages/            # App беттері
├── app.svelte        # Root app shell
├── app.css           # Tailwind және theme tokens
├── main.ts           # Entry point
└── manifest.js       # PWA manifest source
```

## Негізгі беттер

- `login.svelte` - авторизация және университет таңдау.
- `schedule.svelte` - сабақ кестесі.
- `attestation.svelte` - бағалар және калькуляторға өту.
- `exams.svelte` - емтихан/транскрипт summary.
- `profile.svelte` - студент профилі.
- `settings.svelte` - тақырып, тіл, хабарлама және кэш баптаулары.
- `files/` - оқу материалдары.

## Тақырып жүйесі

Theme state `src/lib/color-scheme` ішінде сақталады. Негізгі storage key:

```text
color-theme
```

Tailwind semantic color token-дарын қолдану керек:

- `bg-background`
- `bg-card`
- `text-foreground`
- `text-muted-foreground`
- `border-border`
- `text-primary`

Hardcoded `text-white`, `border-white`, `bg-white/..` кластарын app беттерінде тек нақты дизайн қажет болғанда ғана қолданыңыз.

## Mobile layout

Қосымша mobile-first. Fixed/floating bottom navigation бар беттерде:

- content соңында жеткілікті bottom padding болуы керек;
- `env(safe-area-inset-bottom)` ескерілуі керек;
- соңғы card navigation астына кірмеуі керек;
- 390x844 және 430x932 сияқты viewport-тарда тексеру ұсынылады.

## PWA public файлдары

`public/` ішіндегі файлдар build кезінде `static/` root-ына көшіріледі:

- `favicon.svg`
- `404.html`
- `robots.txt`
- `sitemap.xml`
- Google verification HTML
- `images/`

SEO немесе verification файлын өзгертсеңіз, source `public/` және build output `static/` күйін тексеріңіз.

## API

Dev режимінде API base:

```text
http://localhost:7435
```

Production режимінде same-origin қолданылады.

API base logic: `src/api/config.ts`.

## UI өзгерісін тексеру

1. `pnpm build`.
2. Қажет болса local backend іске қосу.
3. Mobile viewport-та негізгі flow тексеру.
4. Dark және light theme тексеру.
5. Console error жоқ екенін қарау.

## Қауіпсіздік ескертпесі

Frontend ішінде password, token немесе cookie log жазбаңыз. Auth/session logic өзгерсе, root [SECURITY.md](../SECURITY.md) файлын қараңыз.
