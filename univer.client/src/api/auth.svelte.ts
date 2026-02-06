import { _, i18n } from "$lib/i18n"
import { api } from "./config"
import { HTTPError, Unauthorized } from "./errors"
import { secureStorage } from "./secure-storage"
import { singleFetch } from "./utils"

interface User {
    username: string
    password: string
    univer: string
}

export const checkAuth = () => secureStorage.getItem("password") !== null

const authFetchUrl = (apiUrl: string) => {
    const url = new URL(apiUrl)
    url.searchParams.set("lang", i18n.language)
    return url
}
export const authFetch = async <T>(
    url: string,
    reader?: (r: Response) => unknown
): Promise<T> => {
    let retryCount = 0
    const maxRetries = 3
    
    while (retryCount < maxRetries) {
        const [data, status, errorType] = await singleFetch<T>(
            authFetchUrl(url),
            { credentials: "include" },
            reader
        )
        if (data) return data
        
        if (status === 401) {
            // Backend жауабындағы error типін тексеру
            if (errorType === "session_refreshed") {
                // Сессия жаңартылды - қайталау
                retryCount++
                continue
            }
            
            if (errorType === "credentials_changed") {
                // Пароль ауысқан - толық logout
                await forceLogout()
                throw new Unauthorized()
            }
            
            // Әдеттегі 401 - refreshToken арқылы қайта кіру
            const refreshStatus = await refreshToken()
            if (refreshStatus === 401) {
                await forceLogout()
                throw new Unauthorized()
            }
            retryCount++
            continue
        }
        if (status === 403) throw new Unauthorized()
        throw HTTPError(status)
    }
    throw HTTPError(408) // Timeout after max retries
}

export const refreshToken = async () => {
    const username = localStorage.getItem("username")
    const univer = localStorage.getItem("univer")
    const password = secureStorage.getItem("password")

    if (username && univer && password)
        return await login({ password, username, univer })
    return 401
}

let loginPromise: Promise<number> | null = null
export const login = (user: User) => {
    if (loginPromise) return loginPromise
    loginPromise = new Promise(async (resolve) => {
        await new Promise((r) => setTimeout(r, 1000))
        try {
            const { status } = await fetch(api("/auth/login"), {
                method: "POST",
                credentials: "include",
                body: JSON.stringify(user),
            })
            if (status === 200) {
                const { password, username, univer } = user
                secureStorage.setItem("password", password)
                localStorage.setItem("username", username)
                localStorage.setItem("univer", univer)
            }
            resolve(status)
        } catch {
            resolve(404)
        }
    })
    loginPromise.then(() => setTimeout(() => (loginPromise = null), 1000))
    return loginPromise
}

export const logout = async () => {
    fetch(api(`/auth/logout`), { credentials: "include" })
    secureStorage.removeItem("password")
}

// Толық logout - барлық local деректерді тазалау
export const forceLogout = async () => {
    await fetch(api(`/auth/logout`), { credentials: "include" })
    secureStorage.removeItem("password")
    localStorage.removeItem("username")
    localStorage.removeItem("univer")
}
