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
    import { fade, fly } from "svelte/transition"
    import Telegram from "$lib/icons/telegram.svelte"

    const app = useApp()
    const api = useApi()

    let query = api.fetchTranscript()

    const close = () => {
        app.sidebarOpen = false
    }

    // Навигация: мәзірді жауып, replace режимінде бетке өту
    const navigate = (href: string) => {
        close()
        // Кішігірім кідіру — мәзірдің жабылу анимациясын күту
        setTimeout(() => {
            app.router?.navigate(href, { mode: "replace" })
        }, 50)
    }

    const items: {
        href: string
        label: string
        icon: any
        external?: boolean
    }[] = [
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

    // Ағымдағы бетті анықтау
    const isActive = (href: string) => app.router?.path === href
</script>

{#if app.sidebarOpen}
    <!-- Overlay: мәзірден тыс басқанда жабылады -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
        class="overlay"
        onclick={close}
        transition:fade={{ duration: 200 }}
    ></div>

    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <aside
        class="sidebar"
        transition:fly={{ x: -280, duration: 250, opacity: 1 }}
    >
        <!-- Профиль бөлігі -->
        <div class="sidebar-header">
            <button onclick={close} class="close-btn" aria-label="Close menu">
                <X size={20} />
            </button>

            <div class="mt-4">
                {#if query.loading}
                    <div
                        class="h-6 w-32 bg-white/20 animate-pulse rounded mb-2"
                    ></div>
                    <div
                        class="h-4 w-48 bg-white/20 animate-pulse rounded opacity-70"
                    ></div>
                {:else if query.data}
                    <h2 class="sidebar-name">{query.data.fullname}</h2>
                    <p class="sidebar-program">
                        {query.data.education_program}
                    </p>
                {:else}
                    <h2 class="sidebar-name">Univer</h2>
                    <p class="sidebar-program">Студент порталы</p>
                {/if}
            </div>
        </div>

        <!-- Навигация элементтері -->
        <nav class="sidebar-nav">
            <ul>
                {#each items as item}
                    <li>
                        {#if item.external}
                            <a
                                href={item.href}
                                target="_blank"
                                rel="noopener noreferrer"
                                class="nav-item"
                                onclick={close}
                            >
                                <div class="nav-icon">
                                    <item.icon size={22} />
                                </div>
                                <span>{item.label}</span>
                            </a>
                        {:else}
                            <button
                                class="nav-item"
                                class:active={isActive(item.href)}
                                onclick={() => navigate(item.href)}
                            >
                                <div
                                    class="nav-icon"
                                    class:active={isActive(item.href)}
                                >
                                    <item.icon size={22} />
                                </div>
                                <span>{item.label}</span>
                            </button>
                        {/if}
                    </li>
                {/each}
            </ul>
        </nav>

        <!-- Төменгі бөлім -->
        <div class="sidebar-footer">
            Univer v{api.version.client}
        </div>
    </aside>
{/if}

<style>
    .overlay {
        position: fixed;
        inset: 0;
        z-index: 100;
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(4px);
    }

    .sidebar {
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        z-index: 101;
        width: 280px;
        display: flex;
        flex-direction: column;
        background: hsl(var(--background));
        border-right: 1px solid hsl(var(--border));
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }

    .sidebar-header {
        background: hsl(var(--primary));
        color: hsl(var(--primary-foreground));
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
    }

    .close-btn {
        position: absolute;
        right: 0.5rem;
        top: 0.5rem;
        padding: 0.375rem;
        border-radius: 9999px;
        background: transparent;
        border: none;
        color: inherit;
        cursor: pointer;
        transition: background-color 0.15s;
    }
    .close-btn:hover {
        background: rgba(255, 255, 255, 0.2);
    }

    .sidebar-name {
        font-size: 1.125rem;
        font-weight: 700;
        line-height: 1.25;
        margin-bottom: 0.25rem;
    }

    .sidebar-program {
        font-size: 0.75rem;
        opacity: 0.8;
        line-height: 1.4;
    }

    .sidebar-nav {
        flex: 1;
        overflow-y: auto;
        padding: 0.5rem 0;
    }

    .sidebar-nav ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .nav-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.75rem 1rem;
        width: 100%;
        font-size: 0.875rem;
        background: transparent;
        border: none;
        color: hsl(var(--foreground));
        cursor: pointer;
        text-decoration: none;
        text-align: left;
        transition:
            background-color 0.15s,
            color 0.15s;
    }

    .nav-item:hover {
        background: hsl(var(--accent));
        color: hsl(var(--accent-foreground));
    }

    .nav-item.active {
        background: hsl(var(--accent));
        color: hsl(var(--primary));
        font-weight: 600;
    }

    .nav-icon {
        width: 1.5rem;
        display: flex;
        justify-content: center;
        flex-shrink: 0;
    }

    .nav-icon.active {
        color: hsl(var(--primary));
    }

    .sidebar-footer {
        padding: 1rem;
        border-top: 1px solid hsl(var(--border));
        opacity: 0.5;
        font-size: 0.625rem;
        text-align: center;
    }
</style>
