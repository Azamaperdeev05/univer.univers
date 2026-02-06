// Production-да same-origin қолдану үшін
const getApiPath = () => {
    if (import.meta.env.DEV) {
        return "http://localhost:7435"
    }
    // Production: browser-да window.location.origin қолдану
    if (typeof window !== "undefined") {
        return window.location.origin
    }
    return "" // SSR fallback
}

const API_PATH = getApiPath()
export const api = (path: string) => `${API_PATH}${path}`
