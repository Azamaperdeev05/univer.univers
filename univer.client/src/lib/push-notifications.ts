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
    await fetch('/api/push/subscribe', {
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
