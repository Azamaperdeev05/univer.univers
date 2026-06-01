# Roadmap

Бұл файл жобаның даму бағытын көрсетеді. Басымдықтар нақты пайдаланушы мәселелеріне, Platonus порталдарының өзгерісіне және deploy тұрақтылығына қарай өзгеруі мүмкін.

## Аяқталған негізгі кезеңдер

### v1.0 - MVP

- Логин және session flow.
- Сабақ кестесі.
- Бағалар және аттестация.
- GPA/баға калькуляторы.
- Емтихан кестесі.
- Профиль.
- FAQ және privacy policy.
- Қазақ, орыс, ағылшын тілдері.
- PWA manifest және service worker.
- Жарық/қараңғы тақырып.

### v1.2 - UI жаңарту

- Мобильді-first интерфейс.
- Drawer/sidebar navigation.
- Privacy және FAQ беттері.
- Кэш тазалау және basic settings.
- Тақырып пен тіл таңдауы.

### v1.3 - Platonus интеграциясы

- Platonus login flow.
- Бірнеше университет конфигурациясы.
- 1 және 2 семестр бағаларын ауыстыру.
- Transcript және UMKD интеграциялары.
- Емтихан және профиль деректерін шығару.

### v1.3.1 - Тұрақтылық

- Token refresh flow.
- 401/403 жауаптарын refresh trigger ретінде өңдеу.
- Timeout handling.
- Пән detail drawer.
- Push notification service.
- ENU бағалау ерекшеліктерін өңдеу.
- Light/dark theme bug fixes.
- Login university selector.
- Google verification, sitemap, robots және basic SEO.

## Қысқа мерзімді жоспар

### v1.4 - UX және тұрақтылық

- Attestation бетінің төменгі navigation overlap мәселелерін толық тексеру.
- Login бетінің mobile/desktop layout QA.
- Университет selector іздеу/filter қосу.
- Кэш тазалағанда auth емес preference кілттерін сақтау.
- Skeleton/loading state-терді біріздендіру.
- Error state-терді user-friendly мәтіндерге көшіру.
- Pull-to-refresh немесе manual refresh control.

### v1.5 - Бағалар логикасы

- ENU current progress gradebook parser-ін production API-ге шығару.
- Әртүрлі университеттердің mark type mapping кестесін бөлек конфигурацияға шығару.
- "е.а.", "ж", "к.ж.", "ДС", "Емт.", "Практика" сияқты mark name variant-тарын тестілеу.
- Ағым түрлеріне салмақ беру логикасын university-specific ету.
- Баға өзгерісін бұрынғы мәнмен салыстырып көрсету.

### v1.6 - Хабарламалар

- Жаңа баға туралы push хабарлама.
- Сабаққа дейінгі reminder.
- Кешкі "ертеңгі сабақтар" summary.
- Notification history.
- Notification permission recovery UI.

## Орта мерзімді жоспар

### v2.0 - Аналитика

- GPA динамикасы.
- Семестр бойынша пән progress.
- Емтиханға дейінгі countdown.
- Қатысу/attendance dashboard.
- Баға болжамы және мақсатқа жету калькуляторы.

### v2.1 - Персонализация

- Accent color таңдау.
- Font size accessibility.
- Compact/comfortable density mode.
- Пайдаланушыға ыңғайлы dashboard widgets.

### v2.2 - Көп университетті қолдау

- Университет metadata management.
- Portal health check.
- Университет бойынша feature flags.
- Platonus version differences registry.
- Auto-detect логикасын жылдамдату.

## Ұзақ мерзімді жоспар

### v3.0 - Platform

- Admin dashboard.
- OpenAPI/Swagger құжаттамасы.
- E2E тестілер.
- Monitoring және error reporting.
- CI/CD pipeline.
- Production observability.

## Техникалық борыш

- Svelte 5 runes қолдануын толық біріздендіру.
- TypeScript strict mode-қа жақындау.
- Backend response model-дерін типтеу.
- Platonus parser-лерін unit test-пен жабу.
- Static build артефактілерін deploy flow-ға нақты бөлу.
- Service worker cache strategy audit.
- Accessibility audit.
- Security headers және CSRF strategy audit.

## Басымдық принципі

1. Пайдаланушы көріп тұрған дерек дұрыс болуы керек.
2. Auth/session flow тұрақты болуы керек.
3. Mobile UI navigation астында қалмауы керек.
4. Әр университеттің Platonus айырмашылығы бөлек конфигурациямен жабылуы керек.
5. SEO және public landing тек негізгі app flow бұзылмаған кезде жақсартылады.
