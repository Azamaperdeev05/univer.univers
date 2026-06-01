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
    let univer_code = $state("auto")
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
            univer_code,
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

<Page class="relative flex flex-col justify-between min-h-screen bg-[#07070a] overflow-hidden">
    {#snippet header()}
        <AppBar class="border-b border-white/5 bg-transparent backdrop-blur-md">
            {#snippet left()}
                <Button variant="ghost" size="icon" href={routes.faq} class="text-zinc-400 hover:text-white transition-colors duration-300"
                    ><CircleHelp style="width: 20px; height: 20px;" /></Button
                >
            {/snippet}
            {#snippet right()}
                <div class="flex gap-1.5">
                    <InstallButton>
                        {#snippet children(onclick)}
                            <Button variant="ghost" size="icon" {onclick} class="text-zinc-400 hover:text-white transition-colors duration-300">
                                <MonitorDown style="width: 20px; height: 20px;" />
                            </Button>
                        {/snippet}
                    </InstallButton>
                    <Button
                        variant="ghost"
                        size="icon"
                        href={routes.telegram}
                        target="_blank"
                        class="text-zinc-400 hover:text-white transition-colors duration-300"
                    >
                        <Telegram style="width: 20px; height: 20px;" />
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon"
                        href={routes.github}
                        target="_blank"
                        class="text-zinc-400 hover:text-white transition-colors duration-300"
                    >
                        <Github style="width: 20px; height: 20px;" />
                    </Button>
                    <Button variant="ghost" size="icon" href={routes.settings} class="text-zinc-400 hover:text-white transition-colors duration-300">
                        <Settings style="width: 20px; height: 20px;" />
                    </Button>
                </div>
            {/snippet}
        </AppBar>
    {/snippet}

    <div class="flex-1 flex items-center justify-center px-4 relative z-10 py-10">
        <form
            class="w-full max-w-[390px] bg-[#0c0c12]/80 backdrop-blur-2xl border border-white/10 rounded-3xl p-8 flex flex-col gap-6 shadow-[0_24px_64px_rgba(0,0,0,0.6)] relative overflow-hidden group hover:border-white/15 transition-all duration-500"
            {onsubmit}
        >
            <!-- Background light flare inside card -->
            <div class="absolute -top-24 -left-24 w-48 h-48 bg-sky-500/5 rounded-full blur-3xl pointer-events-none group-hover:bg-sky-500/10 transition-all duration-500"></div>

            <div class="flex flex-col items-center gap-3 pb-2">
                <!-- Pulsing Ambient Glow behind logo with dynamic theme -->
                <div class="relative flex items-center justify-center w-20 h-20 rounded-2xl bg-white/5 border border-white/10 shadow-[0_8px_32px_rgba(255,255,255,0.02)] transition-all duration-300 group-hover:border-white/20">
                    <div class="absolute inset-0 rounded-2xl bg-gradient-to-tr from-sky-500/10 to-blue-500/10 animate-pulse"></div>
                    <img
                        src="/images/logo.svg"
                        alt="Platonus Logo"
                        class="w-12 h-12 object-contain relative z-10 filter drop-shadow-[0_4px_12px_rgba(0,0,0,0.5)]"
                    />
                </div>
                <div class="text-center mt-1">
                    <h2 class="text-2xl font-bold tracking-tight text-white/90">
                        Platonus
                    </h2>
                    <p class="text-xs text-zinc-400 mt-1 max-w-[240px]">Бірыңғай студенттік портал</p>
                </div>
            </div>

            <div class="flex flex-col gap-1.5">
                <span class="text-xs font-semibold tracking-wider text-zinc-400 uppercase ml-1">{_("username")}</span>
                <div class="relative">
                    <Input
                        type="text"
                        bind:value={username}
                        name="username"
                        placeholder="Логин енгізіңіз..."
                        class="w-full bg-zinc-900/60 border border-white/5 focus:border-sky-500/50 focus:ring-2 focus:ring-sky-500/10 text-white rounded-xl h-11 px-4 transition-all duration-300 placeholder:text-zinc-600 shadow-[inset_0_2px_4px_rgba(0,0,0,0.4)]"
                    />
                </div>
            </div>

            <div class="flex flex-col gap-1.5">
                <span class="text-xs font-semibold tracking-wider text-zinc-400 uppercase ml-1">{_("password")}</span>
                <div class="relative">
                    <Input
                        type={showPassword ? "text" : "password"}
                        bind:value={password}
                        name="password"
                        placeholder={showPassword ? api.version.client : "••••••••••••"}
                        class="w-full bg-zinc-900/60 border border-white/5 focus:border-sky-500/50 focus:ring-2 focus:ring-sky-500/10 text-white rounded-xl h-11 pl-4 pr-11 transition-all duration-300 placeholder:text-zinc-600 shadow-[inset_0_2px_4px_rgba(0,0,0,0.4)]"
                    />
                    <Button
                        variant="ghost"
                        type="button"
                        size="icon"
                        class="absolute right-1 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white transition-colors duration-300"
                        onclick={() => (showPassword = !showPassword)}
                    >
                        {#if showPassword}
                            <EyeOff style="width: 20px; height: 20px;" />
                        {:else}
                            <Eye style="width: 20px; height: 20px;" />
                        {/if}
                    </Button>
                </div>
            </div>

            <label class="flex items-start gap-3 my-1 cursor-pointer select-none">
                <Checkbox id="terms" bind:checked={agree} name="agree" class="mt-0.5 rounded border-zinc-700 bg-zinc-900/60 text-sky-500 focus:ring-sky-500/30" />
                <span class="privacy text-xs leading-relaxed text-zinc-400">
                    {@html _("privacy-policy.agree", routes.privacy)}
                </span>
            </label>

            {#if error}
                <p class="text-xs font-medium text-rose-500 bg-rose-500/10 border border-rose-500/20 px-3.5 py-2.5 rounded-xl text-center">
                    {error}
                </p>
            {/if}

            <Button 
                {disabled} 
                type="submit"
                class="w-full rounded-xl h-11 font-semibold tracking-wide text-white transition-all duration-300 active:scale-[0.98] select-none
                       {disabled 
                           ? 'bg-zinc-800 text-zinc-500 border border-zinc-700/50 cursor-not-allowed shadow-none' 
                           : 'bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 border border-sky-400/20 shadow-[0_8px_24px_rgba(14,165,233,0.15)] hover:shadow-[0_12px_32px_rgba(14,165,233,0.25)]'}"
            >
                {#if status === "loading"}
                    <div class="flex items-center justify-center gap-2">
                        <!-- Premium loading spinner -->
                        <svg class="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>{_("loading")}...</span>
                    </div>
                {:else}
                    <span>{_("login")}</span>
                {/if}
            </Button>
        </form>
    </div>

    <div class="flex justify-center p-6 relative z-10">
        <p class="text-xs tracking-wider text-zinc-500 select-none">
            Platonus • Бірыңғай Портал • {api.version.client}
        </p>
    </div>
</Page>

<style>
    .privacy :global(a) {
        @apply text-sky-400 underline hover:no-underline hover:text-sky-300 transition-colors duration-300;
    }
</style>

