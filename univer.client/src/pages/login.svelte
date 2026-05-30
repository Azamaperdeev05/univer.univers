<script lang="ts">
    import {
        CircleHelp,
        Settings,
        Eye,
        EyeOff,
        MonitorDown,
    } from "lucide-svelte"
    import { Button } from "$lib/components/ui/button"
    import { Input } from "$lib/components/ui/input"
    import { Label } from "$lib/components/ui/label"
    import { Checkbox } from "$lib/components/ui/checkbox"

    import { routes } from "./url"
    import { useApi } from "../api"

    import { _ } from "$lib/i18n"
    import Page from "$lib/layouts/page.svelte"
    import AppBar from "$lib/components/app-bar.svelte"
    import { useRouter } from "$lib/router"
    import { onMount } from "svelte"
    import { useApp } from "../app.svelte"
    import InstallButton from "$lib/components/install-button.svelte"
    import Telegram from "$lib/icons/telegram.svelte"
    import Github from "$lib/icons/github.svelte"

    const api = useApi()
    let username = $state("")
    let password = $state("")
    let status = $state<"ready" | "loading" | "error">("ready")
    let agree = $state(false)
    let error = $state("")

    let active = $derived(username.length && agree && password.length)
    let disabled = $derived(status == "loading" ? true : !active)
    const router = useRouter()
    const app = useApp()

    const onsubmit = async (event: SubmitEvent) => {
        event.preventDefault()
        status = "loading"
        const s = await api.login({
            password,
            username,
        })
        if (s === 200) {
            router.navigate(routes.home, { mode: "replace" })
            app.isAuth = true
            return
        }
        status = "ready"
        if (s === 401) {
            error = _("error.invalid-credentials")
            return
        }
        error = _("error.connection-error")
    }
    let showPassword = $state(false)
</script>

<Page class="grid grid-rows-min-auto-min">
    {#snippet header()}
        <AppBar>
            {#snippet left()}
                <Button variant="ghost" size="icon" href={routes.faq}
                    ><CircleHelp /></Button
                >
            {/snippet}
            {#snippet right()}
                <div class="flex gap-2">
                    <InstallButton>
                        {#snippet children(onclick)}
                            <Button variant="ghost" size="icon" {onclick}>
                                <MonitorDown />
                            </Button>
                        {/snippet}
                    </InstallButton>
                    <Button
                        variant="ghost"
                        size="icon"
                        href={routes.telegram}
                        target="_blank"
                    >
                        <Telegram />
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon"
                        href={routes.github}
                        target="_blank"
                    >
                        <Github />
                    </Button>
                    <Button variant="ghost" size="icon" href={routes.settings}>
                        <Settings />
                    </Button>
                </div>
            {/snippet}
        </AppBar>
    {/snippet}

    <form
        class="w-full max-w-[370px] justify-self-center grid gap-5 self-center px-4"
        {onsubmit}
    >
        <div class="flex flex-col items-center gap-2 p-2">
            <img
                src="/images/kstu.png"
                alt={_("univer.kstu")}
                class="w-16 h-16 object-contain drop-shadow"
            />
            <h2 class="text-xl font-bold tracking-tight text-foreground">{_("univer.kstu")}</h2>
            <p class="text-xs text-muted-foreground text-center">Студенттерге арналған бірыңғай портал</p>
        </div>

        <Label class="flex w-full max-w-sm flex-col gap-1.5"
            >{_("username")}
            <Input
                type="text"
                bind:value={username}
                name="username"
                placeholder=""
            />
        </Label>

        <Label class="flex w-full max-w-sm flex-col gap-1.5"
            >{_("password")}
            <div class="relative">
                <Input
                    type={showPassword ? "text" : "password"}
                    bind:value={password}
                    name="password"
                    placeholder={showPassword
                        ? api.version.client
                        : "●●●●●●●●●"}
                />
                <Button
                    variant="ghost"
                    type="button"
                    size="icon"
                    class="absolute right-0 top-0"
                    onclick={() => (showPassword = !showPassword)}
                >
                    {#if showPassword}
                        <EyeOff />
                    {:else}
                        <Eye />
                    {/if}
                </Button>
            </div>
        </Label>

        <Label class="flex items-center gap-2">
            <Checkbox id="terms" bind:checked={agree} name="agree" />
            <div class="privacy text-sm">
                {@html _("privacy-policy.agree", routes.privacy)}
            </div>
        </Label>
        {#if error}
            <p class="text-destructive">
                {error}
            </p>
        {/if}
        <Button {disabled} type="submit"
            >{status === "loading" ? _("loading") : _("login")}</Button
        >
    </form>
    <div class="flex justify-center p-4">
        <p class="text-muted-foreground">{api.version.client}</p>
    </div>
</Page>

<style>
    .privacy :global(a) {
        @apply text-primary underline hover:no-underline;
    }
</style>
