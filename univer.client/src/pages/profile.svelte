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
                {@const {fullname, education_program} = query.data}
                <div>
                    <p class="font-bold">{fullname}</p>
                    <p>{education_program}</p>
                </div>
            {/if}
            <p>{_("username")}: <b>{username}</b></p>

            {#if query.loading}
                <Loader />
            {:else if query.data}
                {@const {year_of_study, length_of_program, language, graid_point, avarage_point} = query.data}
                <div>
                    <p class="profile__year">
                        {_("transcript.year-of-study")}:
                        <b>{year_of_study}</b>
                        <span class="opacity-50">/ {length_of_program}</span>
                    </p>
                    <p>
                        {_("transcript.language")}:
                        <b>{language}</b>
                    </p>
                </div>
                <div>
                    <p>
                        {_("transcript.graid-point")}:
                        <b>{graid_point}</b>
                    </p>
                    <p>
                        {_("transcript.avarage-point")}:
                        <b>{avarage_point}</b>
                    </p>
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