<script lang="ts">
    import { _ } from "$lib/i18n"
    import {
        CalendarDays,
        BookA,
        Calculator,
        Folder,
        CircleUserRound,
        Settings,
        GraduationCap,
        X,
    } from "lucide-svelte"
    import { routes } from "../../pages"
    import { useApp } from "../../app.svelte"
    import { useApi } from "../../api"
    import { fade, slide, fly } from "svelte/transition"
    import { useRouter } from "$lib/router"
    import Telegram from "$lib/icons/telegram.svelte"

    const app = useApp()
    const api = useApi()
    const router = useRouter()

    let query = api.fetchTranscript()

    $effect(() => {
        console.log("Sidebar rendered, sidebarOpen state:", app.sidebarOpen)
    })

    const close = () => {
        app.sidebarOpen = false
    }

    const navigate = (href: string) => {
        router.navigate(href)
        close()
    }

    const items = [
        { href: routes.schedule, label: _("schedule"), icon: CalendarDays },
        { href: routes.attestation, label: _("attestation"), icon: BookA },
        { href: routes.calculator, label: _("calculator"), icon: Calculator },
        { href: routes.files, label: _("umkd"), icon: Folder },
        { href: routes.exams, label: _("exams"), icon: GraduationCap },
        { href: routes.profile, label: _("profile"), icon: CircleUserRound },
        {
            href: routes.telegram,
            label: "Telegram",
            icon: Telegram,
            external: true,
        },
        { href: routes.settings, label: _("settings"), icon: Settings },
    ]
</script>

{#if app.sidebarOpen}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
        class="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm"
        onclick={close}
        transition:fade={{ duration: 200 }}
    ></div>

    <aside
        class="fixed left-0 top-0 bottom-0 z-[101] w-[280px] bg-background border-r flex flex-col shadow-2xl"
        transition:fly={{ x: -280, duration: 300, opacity: 1 }}
    >
        <!-- Header -->
        <div
            class="bg-primary p-6 text-primary-foreground relative overflow-hidden"
        >
            <div class="absolute right-2 top-2">
                <button
                    onclick={close}
                    class="p-1 hover:bg-white/20 rounded-full transition-colors"
                >
                    <X size={20} />
                </button>
            </div>

            <div class="mt-4">
                {#if query.loading}
                    <div
                        class="h-6 w-32 bg-white/20 animate-pulse rounded mb-2"
                    ></div>
                    <div
                        class="h-4 w-48 bg-white/20 animate-pulse rounded opacity-70"
                    ></div>
                {:else if query.data}
                    <h2 class="text-lg font-bold leading-tight mb-1">
                        {query.data.fullname}
                    </h2>
                    <p class="text-xs opacity-80 leading-snug">
                        {query.data.education_program}
                    </p>
                {:else}
                    <h2 class="text-lg font-bold mb-1">Univer</h2>
                    <p class="text-xs opacity-80">Студент портылы</p>
                {/if}
            </div>
        </div>

        <!-- Navigation items -->
        <nav class="flex-1 overflow-y-auto py-2">
            <ul class="space-y-1">
                {#each items as item}
                    <li>
                        {#if item.external}
                            <a
                                href={item.href}
                                target="_blank"
                                class="flex items-center gap-4 px-4 py-3 text-sm transition-colors hover:bg-accent hover:text-accent-foreground"
                            >
                                <div
                                    class="w-6 flex justify-center text-primary"
                                >
                                    <item.icon size={22} />
                                </div>
                                <span class="flex-1">{item.label}</span>
                            </a>
                        {:else}
                            <button
                                onclick={() => navigate(item.href)}
                                class="w-full flex items-center gap-4 px-4 py-3 text-sm transition-colors hover:bg-accent hover:text-accent-foreground"
                                class:bg-accent={router.path === item.href}
                                class:text-primary={router.path === item.href}
                                class:font-semibold={router.path === item.href}
                            >
                                <div
                                    class="w-6 flex justify-center"
                                    class:text-primary={router.path ===
                                        item.href}
                                >
                                    <item.icon size={22} />
                                </div>
                                <span class="flex-1 text-left"
                                    >{item.label}</span
                                >
                            </button>
                        {/if}
                    </li>
                {/each}
            </ul>
        </nav>

        <!-- Footer -->
        <div class="p-4 border-t opacity-50 text-[10px] text-center">
            Univer v{api.version.client}
        </div>
    </aside>
{/if}

<style>
    /* Кез келген қосымша стильдер */
</style>
