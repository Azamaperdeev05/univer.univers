export class Network {
    online = $state(typeof navigator !== "undefined" ? navigator.onLine : true)

    constructor() {
        if (typeof window !== "undefined") {
            window.addEventListener("online", () => (this.online = true))
            window.addEventListener("offline", () => (this.online = false))
        }
    }
}

export const network = new Network()
