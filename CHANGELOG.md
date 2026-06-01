# Changelog

Бұл файлда жобадағы маңызды өзгерістер жазылады. Формат [Keep a Changelog](https://keepachangelog.com/) принципіне жақын, ал нұсқалау SemVer логикасына сүйенеді.

## [Unreleased]

### Added

- Google Search Console verification файлы.
- `robots.txt` және `sitemap.xml`.
- SEO meta tags, canonical URL, Open Graph, Twitter card және JSON-LD structured data.
- Login бетіне университет таңдау flow.

### Changed

- Login бетінің университет логотип ticker орналасуы жақсартылды.
- Attestation бетінің төменгі navigation overlap мәселесі түзетілді.
- Page layout төменгі safe-area inset мәнін ескереді.
- Bottom navigation биіктігі runtime кезінде өлшенеді.

### Fixed

- ENU `ДС` mark type енді `АА` ретінде оқылады.
- ENU differentiated credit / differentiated test атаулары қорытынды бақылау ретінде танылады.
- "Дене шынықтыру" пәнінде `AA: 0` болып көріну қатесі түзетілді.

## [1.3.1] - 2026-06-01

### Added

- Бірнеше Platonus университетін таңдауға арналған login selector.
- ENU current progress gradebook логикасын зерттеу және parser mapping кеңейту.
- Пән detail drawer арқылы күн бойынша бағаларды қарау.
- Push notification infrastructure.

### Changed

- Token refresh flow тұрақтандырылды.
- Platonus request timeout мәндері қайта қаралды.
- Light/dark theme class handling жақсартылды.
- Settings cache clear theme кілтін дұрыс сақтайды.
- Exams және profile беттеріндегі hardcoded dark color-лар semantic class-тарға жақындатылды.

### Fixed

- `attendance.svelte` data binding қатесі.
- Platonus 401/403 response refresh trigger ретінде өңделмеуі.
- Broad exception handling орындары.
- Subject details endpoint refresh retry behavior.

## [1.3.0] - 2026-03-02

### Added

- Platonus интеграциясы.
- 1 және 2 семестр бағаларын ауыстыру.
- Университет және Platonus session handling.
- Transcript және UMKD деректерін оқу.
- Емтихан кестесі және профиль беттері.

### Changed

- Backend API error handling жақсартылды.
- Frontend navigation және settings flow жаңартылды.

## [1.0.1] - 2026-02-10

### Added

- Жаңа mobile-first дизайн.
- Telegram арна сілтемесі.
- FAQ жауаптары қазақ, орыс және ағылшын тілдерінде.
- Push notification алғашқы flow.

### Changed

- Logo, favicon және PWA screenshot-тар жаңартылды.
- Privacy policy беті толықтырылды.
- PWA manifest реттелді.

### Removed

- Артық static asset дубликаттары.
- Ескі layout бөліктері.

## [1.0.0] - 2026-01-28

### Added

- Алғашқы тұрақты нұсқа.
- Сабақ кестесі.
- Бағалар.
- GPA/баға калькуляторы.
- Транскрипт.
- UMKD материалдары.
- Қазақ, орыс және ағылшын тілдері.
- Жарық/қараңғы тақырып.
- PWA support.

## [0.9.0] - 2026-01-15

### Added

- Алғашқы beta.
- Backend және frontend негізі.
- Негізгі Platonus дерек оқу flow.
