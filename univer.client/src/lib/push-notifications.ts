/**
 * Push Notification модулі - клиент жағы
 * Service Worker арқылы хабарламаларды қабылдау
 */

// VAPID Public Key (сервердегімен сәйкес болуы керек)
const VAPID_PUBLIC_KEY = 'BFOUQrzKRE_RZ2hxy8Xo76kDU_r3VVsNNz7iutQRp2rgKOLmHYPJszzsGtQGE6rF7z9_H7k_7sPZbK3KvAQA9zg'

/**
 * Base64 URL-safe строкаларды Uint8Array-ға түрлендіру
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
    const base64 = (base64String + padding)
        .replace(/-/g, '+')
        .replace(/_/g, '/')

    const rawData = window.atob(base64)
    const outputArray = new Uint8Array(rawData.length)

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i)
    }
    return outputArray
}

/**
 * Push хабарламаларына рұқсат сұрау және жазылу
 */
export async function subscribeToPush(): Promise<PushSubscription | null> {
    // Service Worker тіркелгенін тексеру
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.warn('Push notifications are not supported')
        return null
    }

    try {
        // Рұқсат сұрау
        const permission = await Notification.requestPermission()
        if (permission !== 'granted') {
            console.warn('Notification permission denied')
            return null
        }

        // Service Worker-ді алу
        const registration = await navigator.serviceWorker.ready

        // Бар subscription-ды тексеру
        let subscription = await registration.pushManager.getSubscription()
        
        if (!subscription) {
            // Жаңа subscription жасау
            subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
            })
        }

        // Серверге жіберу
        await sendSubscriptionToServer(subscription)

        return subscription
    } catch (error) {
        console.error('Failed to subscribe to push:', error)
        return null
    }
}

/**
 * Push хабарламаларынан бас тарту
 */
export async function unsubscribeFromPush(): Promise<boolean> {
    try {
        const registration = await navigator.serviceWorker.ready
        const subscription = await registration.pushManager.getSubscription()

        if (subscription) {
            await subscription.unsubscribe()
            await removeSubscriptionFromServer(subscription)
            return true
        }

        return false
    } catch (error) {
        console.error('Failed to unsubscribe:', error)
        return false
    }
}

/**
 * Subscription күйін тексеру
 */
export async function isPushSubscribed(): Promise<boolean> {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        return false
    }

    try {
        const registration = await navigator.serviceWorker.ready
        const subscription = await registration.pushManager.getSubscription()
        return subscription !== null
    } catch {
        return false
    }
}

/**
 * Subscription-ды серверге жіберу
 */
async function sendSubscriptionToServer(subscription: PushSubscription): Promise<void> {
    // Тілді localStorage-тен алу
    const lang = localStorage.getItem('lang') || 'kk'
    
    await fetch(`/api/push/subscribe?lang=${lang}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(subscription.toJSON()),
        credentials: 'include'
    })
}

/**
 * Subscription-ды серверден өшіру
 */
async function removeSubscriptionFromServer(subscription: PushSubscription): Promise<void> {
    await fetch('/api/push/unsubscribe', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ endpoint: subscription.endpoint }),
        credentials: 'include'
    })
}

/**
 * Хабарлама рұқсатын тексеру
 */
export function getNotificationPermission(): NotificationPermission {
    if (!('Notification' in window)) {
        return 'denied'
    }
    return Notification.permission
}

/**
 * Push хабарламалар қолдауын тексеру
 */
export function isPushSupported(): boolean {
    return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
}

/**
 * Хабарлама параметрлерін алу
 */
export async function getPushSettings(): Promise<PushSettings | null> {
    try {
        const response = await fetch('/api/push/status', {
            credentials: 'include'
        })
        const data = await response.json()
        return data.subscribed ? data.settings : null
    } catch (error) {
        console.error('Failed to get push settings:', error)
        return null
    }
}

/**
 * Хабарлама параметрлерін жаңарту
 */
export async function updatePushSettings(settings: PushSettings): Promise<boolean> {
    try {
        const response = await fetch('/api/push/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ settings }),
            credentials: 'include'
        })
        return response.ok
    } catch (error) {
        console.error('Failed to update push settings:', error)
        return false
    }
}

/**
 * Тестілік хабарлама жіберу
 */
export async function sendTestNotification(lang: string = 'kk'): Promise<boolean> {
    try {
        const response = await fetch(`/api/push/test?lang=${lang}`, {
            method: 'POST',
            credentials: 'include'
        })
        return response.ok
    } catch (error) {
        console.error('Failed to send test notification:', error)
        return false
    }
}

/**
 * Жазылу статусын тексеру
 */
export async function checkSubscriptionStatus(): Promise<SubscriptionStatus> {
    try {
        const response = await fetch('/api/push/status', {
            credentials: 'include'
        })
        const data = await response.json()
        return {
            subscribed: data.subscribed,
            settings: data.settings || null
        }
    } catch (error) {
        console.error('Failed to check subscription status:', error)
        return {
            subscribed: false,
            settings: null
        }
    }
}

// Types
export interface PushSettings {
    new_grades: boolean
    lesson_reminders: boolean
    tomorrow_schedule: boolean
    exam_reminders: boolean
}

export interface TimeSettings {
    lesson_reminder_minutes: number  // 5, 10, 15, 30
    evening_schedule_time: string    // "20:00", "21:00", "22:00", "23:00"
    quiet_hours: {
        enabled: boolean
        start: string  // "23:00"
        end: string    // "07:00"
    }
}

export interface NotificationHistoryItem {
    id: string
    type: string
    title: string
    body: string
    data: Record<string, any>
    sent_at: string
    read: boolean
    clicked: boolean
}

export interface NotificationStats {
    total_sent: number
    total_read: number
    total_clicked: number
    read_rate: number
    click_rate: number
    by_type: Record<string, {
        sent: number
        read: number
        clicked: number
    }>
}

export interface SubscriptionStatus {
    subscribed: boolean
    settings: PushSettings | null
}

/**
 * Хабарлама тарихын алу
 */
export async function getNotificationHistory(limit: number = 50, offset: number = 0): Promise<NotificationHistoryItem[]> {
    try {
        const response = await fetch(`/api/push/history?limit=${limit}&offset=${offset}`, {
            credentials: 'include'
        })
        const data = await response.json()
        return data.history || []
    } catch (error) {
        console.error('Failed to get notification history:', error)
        return []
    }
}

/**
 * Хабарламаны оқылған деп белгілеу
 */
export async function markNotificationRead(notificationId: string): Promise<boolean> {
    try {
        const response = await fetch(`/api/push/history/${notificationId}/mark-read`, {
            method: 'POST',
            credentials: 'include'
        })
        return response.ok
    } catch (error) {
        console.error('Failed to mark notification as read:', error)
        return false
    }
}

/**
 * Хабарламаны басылған деп белгілеу
 */
export async function markNotificationClicked(notificationId: string): Promise<boolean> {
    try {
        const response = await fetch(`/api/push/history/${notificationId}/mark-clicked`, {
            method: 'POST',
            credentials: 'include'
        })
        return response.ok
    } catch (error) {
        console.error('Failed to mark notification as clicked:', error)
        return false
    }
}

/**
 * Хабарламаны жою
 */
export async function deleteNotification(notificationId: string): Promise<boolean> {
    try {
        const response = await fetch(`/api/push/history/${notificationId}`, {
            method: 'DELETE',
            credentials: 'include'
        })
        return response.ok
    } catch (error) {
        console.error('Failed to delete notification:', error)
        return false
    }
}

/**
 * Барлық хабарлама тарихын тазалау
 */
export async function clearNotificationHistory(): Promise<boolean> {
    try {
        const response = await fetch('/api/push/history', {
            method: 'DELETE',
            credentials: 'include'
        })
        return response.ok
    } catch (error) {
        console.error('Failed to clear notification history:', error)
        return false
    }
}

/**
 * Хабарлама статистикасын алу
 */
export async function getNotificationStats(): Promise<NotificationStats | null> {
    try {
        const response = await fetch('/api/push/stats', {
            credentials: 'include'
        })
        return await response.json()
    } catch (error) {
        console.error('Failed to get notification stats:', error)
        return null
    }
}

/**
 * Уақыт параметрлерін жаңарту
 */
export async function updateTimeSettings(timeSettings: TimeSettings): Promise<boolean> {
    try {
        const response = await fetch('/api/push/time-settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ time_settings: timeSettings }),
            credentials: 'include'
        })
        return response.ok
    } catch (error) {
        console.error('Failed to update time settings:', error)
        return false
    }
}
