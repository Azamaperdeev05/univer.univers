<script>
    import { useApi } from "$api"
    import AppBar from "$lib/components/app-bar.svelte"
    import Loader from "$lib/components/loader.svelte"
    import * as Drawer from "$lib/components/ui/drawer"
    import Button from "$lib/components/ui/button/button.svelte"
    import { _ } from "$lib/i18n"

    import Page from "$lib/layouts/page.svelte"
    import { onMount } from "svelte"
    import { useApp } from "../app.svelte"
    import { routes } from "./url"

    const app = useApp()
    const api = useApi()

    let username = $state("")
    onMount(() => {
        username = localStorage.getItem("username") ?? ""
    })

    let query = api.fetchTranscript()
    const onLogoutClick = () => app.logout()
</script>
<Page class="grid grid-rows-min-auto">
    {#snippet header()}
        <AppBar title={_("profile")} />
    {/snippet}

    <div class="grid grid-rows-auto-min mx-auto px-2 py-4 max-w-md w-full">
        <div class="flex flex-col gap-4">
            {#if query.loading}
                <Loader />
            {:else if query.data}
                {@const {fullname, education_program, faculty, education_program_group, level_of_the_qualification} = query.data}
                <div class="bg-card border border-border rounded-3xl p-5 flex flex-col gap-4 shadow-md">
                    <div class="flex items-center gap-3 border-b border-border pb-3">
                        <div class="w-12 h-12 rounded-2xl bg-primary/20 border border-primary/30 flex items-center justify-center text-primary font-bold text-xl">
                            {fullname ? fullname.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase() : "ST"}
                        </div>
                        <div>
                            <p class="text-xs text-muted-foreground font-medium uppercase tracking-wider">{_("transcript.fullname")}</p>
                            <p class="font-bold text-base text-foreground">{fullname}</p>
                        </div>
                    </div>
                    
                    <div class="grid gap-3 text-sm">
                        <div class="flex flex-col gap-0.5">
                            <span class="text-xs text-muted-foreground">{_("transcript.faculty")}</span>
                            <span class="font-medium text-foreground">{faculty}</span>
                        </div>
                        
                        <div class="flex flex-col gap-0.5">
                            <span class="text-xs text-muted-foreground">{_("transcript.education-program-group")}</span>
                            <span class="font-medium text-foreground text-xs sm:text-sm leading-relaxed">{education_program_group}</span>
                        </div>
                        
                        <div class="flex flex-col gap-0.5">
                            <span class="text-xs text-muted-foreground">{_("transcript.education-program")}</span>
                            <span class="font-medium text-foreground text-xs sm:text-sm leading-relaxed">{education_program}</span>
                        </div>
                        
                        <div class="flex flex-col gap-0.5">
                            <span class="text-xs text-muted-foreground">{_("transcript.level-of-the-qualification")}</span>
                            <span class="font-medium text-foreground text-xs leading-relaxed">{level_of_the_qualification}</span>
                        </div>
                    </div>
                </div>
            {/if}

            <div class="bg-card border border-border rounded-2xl p-4 flex items-center justify-between shadow-sm">
                <span class="text-sm text-muted-foreground">{_("username")}</span>
                <span class="font-bold text-foreground bg-muted px-3 py-1 rounded-lg text-sm">{username}</span>
            </div>

            {#if query.loading}
                <Loader />
            {:else if query.data}
                {@const {year_of_study, length_of_program, language, graid_point, avarage_point} = query.data}
                <div class="grid grid-cols-2 gap-3">
                    <div class="bg-card border border-border rounded-2xl p-4 flex flex-col gap-1 shadow-sm">
                        <span class="text-xs text-muted-foreground">{_("transcript.year-of-study")}</span>
                        <span class="font-bold text-lg text-foreground">
                            {year_of_study} <span class="text-sm font-normal text-muted-foreground">/ {length_of_program}</span>
                        </span>
                    </div>
                    <div class="bg-card border border-border rounded-2xl p-4 flex flex-col gap-1 shadow-sm">
                        <span class="text-xs text-muted-foreground">{_("transcript.language")}</span>
                        <span class="font-bold text-base text-foreground">{language}</span>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div class="bg-card border border-border rounded-2xl p-4 flex flex-col gap-1 shadow-sm">
                        <span class="text-xs text-muted-foreground">{_("transcript.graid-point")}</span>
                        <span class="font-bold text-lg text-foreground">{graid_point}</span>
                    </div>
                    <div class="bg-card border border-border rounded-2xl p-4 flex flex-col gap-1 shadow-sm">
                        <span class="text-xs text-muted-foreground">{_("transcript.avarage-point")}</span>
                        <span class="font-bold text-lg text-foreground">{avarage_point}</span>
                    </div>
                </div>
            {/if}
        </div>
        <div class="flex flex-col gap-3 mt-6">
            <Button 
                variant="outline" 
                class="w-full flex items-center justify-center gap-2 border-white/10 hover:bg-white/5 rounded-2xl py-3 text-sm font-semibold transition-all duration-200" 
                onclick={() => app.router?.navigate(routes.settings)}
            >
                <svg class="w-5 h-5 opacity-80" style="width: 20px; height: 20px;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {_("settings")}
            </Button>
            
            <Drawer.Root>
                <Drawer.Trigger let:builder>
                    <Button variant="secondary" class="w-full flex items-center justify-center gap-2 rounded-2xl py-3 text-sm font-semibold transition-all duration-200" builders={[builder]}>
                        <svg class="w-5 h-5 opacity-80" style="width: 20px; height: 20px;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        {_("logout")}
                    </Button>
                </Drawer.Trigger>
                <Drawer.Content class="mx-auto w-[90%] max-w-sm">
                    <Drawer.Header>
                        <Drawer.Title>{_("logout.sure")}</Drawer.Title>
                        <Drawer.Description>
                            {_("logout.message")}
                        </Drawer.Description>
                    </Drawer.Header>
                    <Drawer.Footer class="flex justify-end flex-row gap-2">
                        <Button variant="outline" class="rounded-xl" onclick={onLogoutClick}>
                            {_("logout")}
                        </Button>
                        <Drawer.Close>
                            <Button class="rounded-xl">{_("cancel")}</Button>
                        </Drawer.Close>
                    </Drawer.Footer>
                </Drawer.Content>
            </Drawer.Root>
        </div>
    </div>
</Page>