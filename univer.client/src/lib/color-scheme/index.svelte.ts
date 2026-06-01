class StoredValue<T extends string> {
    value = $state<T>("" as T)
    constructor(public key: string, public defaultValue: T) {
        this.value = defaultValue
    }
    apply(...args: unknown[]) {
        $effect(() => {
            if (this.value === this.defaultValue) {
                localStorage.removeItem(this.key)
            } else {
                localStorage.setItem(this.key, this.value)
            }
        })
        this.value = (localStorage.getItem(this.key) as T) ?? this.defaultValue
    }
}

export class ColorScheme extends StoredValue<"auto" | "dark" | "light"> {
    #matched = $state<"light" | "dark">("light")
    scheme = $derived(this.value === "auto" ? this.#matched : this.value)
    constructor() {
        super("color-theme", "auto")
    }
    apply(node: HTMLElement) {
        super.apply()
        $effect(() => {
            const active = this.scheme
            node.classList.remove(active === "dark" ? "light" : "dark")
            node.classList.add(active)
        })

        const update = ({ matches }: Pick<MediaQueryList, "matches">) => {
            this.#matched = matches ? "dark" : "light"
        }
        $effect(() => {
            const media = matchMedia("(prefers-color-scheme: dark)")
            update(media)

            media.addEventListener("change", update)
            return () => {
                media.removeEventListener("change", update)
            }
        })
    }
}
