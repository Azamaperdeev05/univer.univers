<script lang="ts">
    import {
        CalendarDays,
        BookA,
        Folder,
        CircleUserRound,
        GraduationCap,
    } from "lucide-svelte"
    import { routes } from "../../pages"
    import { useApp } from "../../app.svelte"
    import { onDestroy } from "svelte"

    const app = useApp()

    let bottomNavHeight = $state(0)

    $effect(() => {
        app.navigationHeight = bottomNavHeight + 40
    })

    onDestroy(() => {
        app.navigationHeight = 0
    })

    const items = [
        { href: routes.schedule, icon: CalendarDays },
        { href: routes.attestation, icon: BookA },
        { href: routes.files, icon: Folder },
        { href: routes.exams, icon: GraduationCap },
        { href: routes.profile, icon: CircleUserRound },
    ]

    const isActive = (href: string) => app.router?.path === href

    const navigate = (href: string) => {
        app.router?.navigate(href, { mode: "replace" })
    }
</script>

<div class="bottom-nav-container" bind:clientHeight={bottomNavHeight}>
    <nav class="bottom-nav">
        {#each items as item}
            {@const active = isActive(item.href)}
            <button
                class="nav-item"
                class:active
                onclick={() => navigate(item.href)}
            >
                <div class="icon-wrapper">
                    <item.icon size={20} strokeWidth={active ? 2.5 : 2} />
                </div>
            </button>
        {/each}
    </nav>
</div>

<style>
    .bottom-nav-container {
        position: fixed;
        bottom: 16px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 50;
        width: 90%;
        max-width: 360px;
        pointer-events: none;
    }

    .bottom-nav {
        pointer-events: auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 5px;
        background: rgba(10, 10, 10, 0.78);
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(22px) saturate(190%);
        -webkit-backdrop-filter: blur(22px) saturate(190%);
        border-radius: 999px;
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.65),
            0 1px 2px rgba(255, 255, 255, 0.05) inset;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .nav-item {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 9px;
        border-radius: 999px;
        border: none;
        background: transparent;
        color: #8e8e93;
        cursor: pointer;
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
        aspect-ratio: 1;
    }

    .nav-item:hover {
        color: #ffffff;
        background: rgba(255, 255, 255, 0.03);
    }

    .icon-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.22s;
    }

    /* Active State: Mockup-Perfect Oval Highlight Capsule */
    .nav-item.active {
        background: rgba(255, 255, 255, 0.09);
        color: #ffffff;
        padding-left: 18px;
        padding-right: 18px;
        aspect-ratio: auto; /* Allow expanding into an oval */
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }

    .nav-item.active .icon-wrapper {
        transform: scale(1.06);
    }
</style>
