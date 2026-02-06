<script lang="ts">
    import { onMount, type Snippet } from "svelte"
    interface BeforeInstallPromptEvent {
        prompt: () => void
        userChoice: Promise<{ outcome: "accepted" }>
    }

    let canInstall = $state(false)
    let disabled = $state(true)
    let installEvent = $state<BeforeInstallPromptEvent>()
    let isSafari = $state(false)
    let isIOS = $state(false)

    let {
        class: class_ = "",
        tag = "div",
        children,
    }: {
        class?: string
        tag?: string
        children: Snippet<[() => void]>
    } = $props()

    const onInstall = () => {
        canInstall = false
        installEvent = undefined
    }

    const onBeforeInstallPrompt = (event: any) => {
        event.preventDefault()
        installEvent = event
        canInstall = true
        disabled = false
    }

    onMount(() => {
        const ua = navigator.userAgent
        isIOS = /iPad|iPhone|iPod/.test(ua)
        isSafari = /^((?!chrome|android).)*safari/i.test(ua)

        if ("BeforeInstallPromptEvent" in window) {
            window.addEventListener(
                "beforeinstallprompt",
                onBeforeInstallPrompt,
            )
            window.addEventListener("appinstalled", onInstall)
        } else if (isSafari || isIOS) {
            // Safari/iOS doesn't support the event, but we show the button
            canInstall = true
            disabled = false
        }

        return () => {
            window.removeEventListener(
                "beforeinstallprompt",
                onBeforeInstallPrompt,
            )
            window.removeEventListener("appinstalled", onInstall)
        }
    })

    const onclick = async () => {
        if (installEvent) {
            installEvent.prompt()
            const result = await installEvent.userChoice
            if (result.outcome === "accepted") onInstall()
        } else if (isSafari || isIOS) {
            alert(
                "Safari-де орнату үшін:\n1. 'Бөлісу' (Share) батырмасын басыңыз\n2. 'Басты экранға қосу' (Add to Home Screen) таңдаңыз",
            )
        }
    }
</script>

{#if !disabled && canInstall}
    <svelte:element this={tag} class="install-button {class_}">
        {@render children(onclick)}
    </svelte:element>
{/if}

<style>
    @media (display-mode: standalone) {
        .install-button {
            @apply hidden;
        }
    }
</style>
