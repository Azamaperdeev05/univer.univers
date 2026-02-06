// Уведомление (Notification) қызметі
// Сабақ басталуынан 5 минут бұрын және кешкі сағат 22:00-де ертеңгі сабақтар туралы хабарлама

export interface NotificationSettings {
    enabled: boolean
    lessonReminder: boolean  // Сабаққа 5 минут қалғанда
    eveningReminder: boolean // Кешке 22:00-де ертеңгі сабақтар
    reminderMinutes: number  // Қанша минут бұрын ескерту (default: 5)
}

const STORAGE_KEY = "notification_settings"

// Әдепкі баптаулар
const defaultSettings: NotificationSettings = {
    enabled: false,
    lessonReminder: true,
    eveningReminder: true,
    reminderMinutes: 5
}

// Баптауларды оқу
export function getNotificationSettings(): NotificationSettings {
    try {
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored) {
            return { ...defaultSettings, ...JSON.parse(stored) }
        }
    } catch (e) {
        console.error("Notification settings parse error:", e)
    }
    return defaultSettings
}

// Баптауларды сақтау
export function saveNotificationSettings(settings: NotificationSettings): void {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
}

// Уведомление рұқсатын сұрау
export async function requestNotificationPermission(): Promise<boolean> {
    if (!("Notification" in window)) {
        console.warn("This browser does not support notifications")
        return false
    }
    
    if (Notification.permission === "granted") {
        return true
    }
    
    if (Notification.permission !== "denied") {
        const permission = await Notification.requestPermission()
        return permission === "granted"
    }
    
    return false
}

// Уведомлениени көрсету
export function showNotification(title: string, body: string, icon?: string): void {
    if (Notification.permission === "granted") {
        const notification = new Notification(title, {
            body,
            icon: icon || "/android-chrome-192x192.png",
            badge: "/android-chrome-192x192.png",
            tag: "univer-notification",
            requireInteraction: false
        })
        
        // 10 секундтан кейін автоматты жабу
        setTimeout(() => notification.close(), 10000)
    }
}

// Уақытты парсинг жасау (мысалы: "09:00-10:35")
function parseTime(timeStr: string): { hours: number, minutes: number } | null {
    const match = timeStr.match(/^(\d{1,2}):(\d{2})/)
    if (match) {
        return {
            hours: parseInt(match[1], 10),
            minutes: parseInt(match[2], 10)
        }
    }
    return null
}

// Келесі сабаққа қанша минут қалғанын есептеу
export function getMinutesUntilLesson(lessonTime: string): number {
    const parsed = parseTime(lessonTime)
    if (!parsed) return -1
    
    const now = new Date()
    const lessonDate = new Date()
    lessonDate.setHours(parsed.hours, parsed.minutes, 0, 0)
    
    const diff = lessonDate.getTime() - now.getTime()
    return Math.floor(diff / (1000 * 60))
}

// Бүгінгі апта күні (0 = дүйсенбі, 6 = жексенбі)
export function getTodayWeekday(): number {
    const day = new Date().getDay()
    return day === 0 ? 6 : day - 1  // JS-те 0 = жексенбі
}

// Ертеңгі апта күні
export function getTomorrowWeekday(): number {
    const today = getTodayWeekday()
    return (today + 1) % 7
}

// Қазіргі сағат
export function getCurrentHour(): number {
    return new Date().getHours()
}

// Notification checker (Service Worker арқылы немесе setInterval арқылы)
export class NotificationScheduler {
    private intervalId: number | null = null
    private settings: NotificationSettings
    private lessons: any[] = []
    private notifiedLessons: Set<string> = new Set() // Бірдей уведомлениeні қайталамау үшін
    private eveningNotified: boolean = false
    
    constructor() {
        this.settings = getNotificationSettings()
    }
    
    // Кестені орнату
    setSchedule(lessons: any[]): void {
        this.lessons = lessons
    }
    
    // Баптауларды жаңарту
    updateSettings(settings: NotificationSettings): void {
        this.settings = settings
        saveNotificationSettings(settings)
        
        if (settings.enabled) {
            this.start()
        } else {
            this.stop()
        }
    }
    
    // Scheduler-ді іске қосу
    async start(): Promise<void> {
        if (this.intervalId !== null) return
        
        const hasPermission = await requestNotificationPermission()
        if (!hasPermission) {
            console.warn("Notification permission not granted")
            return
        }
        
        // Әр минут сайын тексеру
        this.intervalId = window.setInterval(() => this.check(), 60 * 1000)
        
        // Бірден бір рет тексеру
        this.check()
    }
    
    // Scheduler-ді тоқтату
    stop(): void {
        if (this.intervalId !== null) {
            clearInterval(this.intervalId)
            this.intervalId = null
        }
    }
    
    // Тексеру және уведомление жіберу
    private check(): void {
        if (!this.settings.enabled) return
        
        const now = new Date()
        const currentHour = now.getHours()
        const currentMinute = now.getMinutes()
        const todayWeekday = getTodayWeekday()
        
        // 1. Сабаққа 5 минут қалғанда ескерту
        if (this.settings.lessonReminder) {
            const todayLessons = this.lessons.filter(l => l.day === todayWeekday)
            
            for (const lesson of todayLessons) {
                const minutesUntil = getMinutesUntilLesson(lesson.time)
                const lessonId = `${lesson.day}-${lesson.time}-${lesson.subject}`
                
                if (minutesUntil > 0 && minutesUntil <= this.settings.reminderMinutes && !this.notifiedLessons.has(lessonId)) {
                    showNotification(
                        `🔔 ${minutesUntil} минуттан кейін сабақ!`,
                        `${lesson.subject}\n📍 ${lesson.audience}`
                    )
                    this.notifiedLessons.add(lessonId)
                }
            }
        }
        
        // 2. Кешке 22:00-де ертеңгі сабақтар туралы
        if (this.settings.eveningReminder && currentHour === 22 && currentMinute === 0 && !this.eveningNotified) {
            const tomorrowWeekday = getTomorrowWeekday()
            const tomorrowLessons = this.lessons.filter(l => l.day === tomorrowWeekday)
            
            if (tomorrowLessons.length > 0) {
                const firstLesson = tomorrowLessons[0]
                showNotification(
                    `📚 Ертең ${tomorrowLessons.length} сабақ бар`,
                    `Бірінші сабақ: ${firstLesson.subject}\n⏰ ${firstLesson.time}\n📍 ${firstLesson.audience}`
                )
                this.eveningNotified = true
                
                // Ертеңге дейін флагты қалпына келтіру
                setTimeout(() => {
                    this.eveningNotified = false
                    this.notifiedLessons.clear()
                }, 2 * 60 * 60 * 1000) // 2 сағаттан кейін
            }
        }
        
        // Түн ортасында notifiedLessons-ті тазалау
        if (currentHour === 0 && currentMinute === 0) {
            this.notifiedLessons.clear()
        }
    }
}

// Singleton instance
export const notificationScheduler = new NotificationScheduler()
