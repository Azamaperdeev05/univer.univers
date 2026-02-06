import { randInt } from "$lib/utils"

const singleCache = new Map<string | URL, Promise<unknown>>()

type _Promise<T> = Promise<[T | null, number, string | null]>
export const singleFetch = <T>(
    url: string | URL,
    params?: RequestInit,
    reader: (r: Response) => unknown = (r) => r.json()
) => {
    if (singleCache.has(url)) return singleCache.get(url) as _Promise<T>
    const promise = new Promise(async (resolve) => {
        try {
            const response = await fetch(url, params)
            const { status } = response
            if (status === 200) {
                const data = await reader(response)
                resolve([data, status, null])
            } else if (status === 401) {
                // 401 болса error type-ты алу
                try {
                    const errorData = await response.json()
                    resolve([null, status, errorData?.error || null])
                } catch {
                    resolve([null, status, null])
                }
            } else {
                resolve([null, status, null])
            }
        } catch (e) {
            resolve([null, 404, null])
        } finally {
            singleCache.delete(url)
        }
    })
    singleCache.set(url, promise)
    return promise as _Promise<T>
}

export const subject = () => randInt(40, 80)
export const teacher = () => randInt(20, 30)
