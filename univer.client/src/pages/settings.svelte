<script lang="ts">
    import { useApi } from "$api"
    import AppBar from "$lib/components/app-bar.svelte"
    import { Label } from "$lib/components/ui/label"
    import * as Radio from "$lib/components/ui/segmented-radio"
    import { _, i18n } from "$lib/i18n"
    import { locales } from "$lib/i18n"
    import { onMount } from "svelte"
    import Switch from "$lib/components/ui/switch"
    import { Button } from "$lib/components/ui/button"

    import Page from "$lib/layouts/page.svelte"
    import { routes } from "./url"
    import colorScheme from "$lib/color-scheme"
    import {
        getNotificationSettings,
        saveNotificationSettings,
        requestNotificationPermission,
        showNotification,
        type NotificationSettings,
    } from "$lib/notifications"
    import {
        subscribeToPush,
        unsubscribeFromPush,
        isPushSubscribed,
    } from "$lib/push-notifications"

    const { version } = useApi()

    // Уведомление баптаулары
    let notifSettings = $state<NotificationSettings>(getNotificationSettings())
    let permissionGranted = $state(false)
    let permissionDenied = $state(false)
    let pushSubscribed = $state(false)

    onMount(async () => {
        if ("Notification" in window) {
            permissionGranted = Notification.permission === "granted"
            permissionDenied = Notification.permission === "denied"
        }
        pushSubscribed = await isPushSubscribed()
    })

    const toggleNotifications = async () => {
        if (!notifSettings.enabled) {
            // Қосу әрекеті
            const granted = await requestNotificationPermission()
            if (granted) {
                notifSettings.enabled = true
                permissionGranted = true

                // Server Push-қа жазылу
                const sub = await subscribeToPush()
                pushSubscribed = !!sub

                saveNotificationSettings(notifSettings)
                if (pushSubscribed) {
                    showNotification(
                        _("notifications.enabled-title" as any),
                        _("notifications.enabled-body" as any),
                    )
                }
            } else {
                permissionDenied = true
            }
        } else {
            // Өшіру
            notifSettings.enabled = false
            await unsubscribeFromPush()
            pushSubscribed = false
            saveNotificationSettings(notifSettings)
        }
    }

    const sendTestNotification = () => {
        showNotification(
            _("notifications.test-title"),
            _("notifications.test-body"),
        )
    }

    // Кэшті тазалау функциясы
    const clearCache = async () => {
        if (!confirm(_("cache.clear-confirm"))) return

        try {
            // Service Worker кэшін тазалау
            if ("caches" in window) {
                const cacheNames = await caches.keys()
                await Promise.all(cacheNames.map((name) => caches.delete(name)))
            }

            // Service Worker-ді қайта тіркеу
            if ("serviceWorker" in navigator) {
                const registrations =
                    await navigator.serviceWorker.getRegistrations()
                for (const registration of registrations) {
                    await registration.unregister()
                }
            }

            // Local Storage тазалау (тіл мен тема сақталады)
            const lang = localStorage.getItem("lang")
            const colorSchemeValue = localStorage.getItem("color-scheme")
            localStorage.clear()
            if (lang) localStorage.setItem("lang", lang)
            if (colorSchemeValue)
                localStorage.setItem("color-scheme", colorSchemeValue)

            alert(_("cache.cleared"))

            // Бетті қайта жүктеу
            window.location.reload()
        } catch (error) {
            console.error("Cache clear error:", error)
            alert("Error: " + error)
        }
    }
</script>

<Page>
    {#snippet header()}
        <AppBar title={_("settings")} />
    {/snippet}

    <div class="max-w-xl mx-auto px-2 py-4 grid gap-y-8">
        <Label class="grid gap-2">
            {_("color-scheme")}
            <Radio.Root bind:value={colorScheme.value}>
                <Radio.Item value="light">{_("color-scheme.light")}</Radio.Item>
                <Radio.Item value="auto">{_("color-scheme.auto")}</Radio.Item>
                <Radio.Item value="dark">{_("color-scheme.dark")}</Radio.Item>
            </Radio.Root>
        </Label>
        <Label class="grid gap-2">
            {_("language")}
            <Radio.Root bind:value={i18n.language}>
                {#each Object.entries(locales) as [value, locale]}
                    <Radio.Item {value}>{locale.CURRENT_LANGUAGE}</Radio.Item>
                {/each}
            </Radio.Root>
        </Label>

        <!-- Уведомление параметрлері -->
        <div class="grid gap-4">
            <h3 class="font-semibold">{_("notifications")}</h3>

            {#if permissionDenied}
                <p class="text-destructive text-sm">
                    {_("notifications.permission-denied")}
                </p>
            {/if}

            <label class="flex items-center justify-between gap-4">
                <span>{_("notifications.enabled")}</span>
                <Switch
                    checked={notifSettings.enabled}
                    onchange={toggleNotifications}
                />
            </label>

            {#if notifSettings.enabled}
                <label class="flex items-center justify-between gap-4 pl-4">
                    <span class="text-sm"
                        >{_("notifications.lesson-reminder")}</span
                    >
                    <Switch
                        bind:checked={notifSettings.lessonReminder}
                        onchange={() => saveNotificationSettings(notifSettings)}
                    />
                </label>

                <label class="flex items-center justify-between gap-4 pl-4">
                    <span class="text-sm"
                        >{_("notifications.evening-reminder")}</span
                    >
                    <Switch
                        bind:checked={notifSettings.eveningReminder}
                        onchange={() => saveNotificationSettings(notifSettings)}
                    />
                </label>

                <Button variant="outline" onclick={sendTestNotification}>
                    {_("notifications.test")}
                </Button>
            {/if}
        </div>

        <!-- Кэш -->
        <div class="grid gap-4">
            <h3 class="font-semibold">{_("cache")}</h3>
            <Button variant="destructive" onclick={clearCache}>
                {_("cache.clear")}
            </Button>
        </div>

        <div>
            <p>{_("version.client")}: <b>{version.client}</b></p>
        </div>

        <a
            class="text-primary underline hover:no-underline"
            href={routes.privacy}>{@html _("privacy-policy", routes.privacy)}</a
        >
    </div>
</Page>
