<script lang="ts">
    import * as auth from "$api/auth.svelte"
    import { Button } from "$lib/components/ui/button"
    import { Card } from "$lib/components/ui/card"
    import { Input } from "$lib/components/ui/input"
    import { _ } from "$lib/i18n"
    import { toast } from "svelte-sonner"
    import { LockKeyhole, Info } from "lucide-svelte"

    let { onDone = () => {} }: { onDone?: () => void } = $props()

    let username = $state("")
    let password = $state("")
    let loading = $state(false)

    const submit = async () => {
        if (!username || !password) return
        loading = true
        try {
            const status = await auth.platonusLink({ username, password })
            if (status === 200) {
                toast.success(_("platonus.linked"))
                onDone()
            } else {
                toast.error(_("error.invalid-credentials"))
            }
        } catch {
            toast.error(_("error.server-error"))
        } finally {
            loading = false
        }
    }
</script>

<div
    class="p-6 max-w-md mx-auto h-full flex flex-col items-center justify-center animate-in fade-in zoom-in duration-300"
>
    <div class="mb-6 text-center">
        <div class="bg-primary/10 p-4 rounded-full w-fit mx-auto mb-4">
            <LockKeyhole class="text-primary w-8 h-8" />
        </div>
        <h2 class="text-2xl font-bold mb-2">{_("platonus.link-title")}</h2>
        <div
            class="flex items-start gap-2 text-sm text-muted-foreground bg-secondary/50 p-3 rounded-lg text-left"
        >
            <Info class="w-5 h-5 mt-0.5 shrink-0 text-primary" />
            <p>
                Бұл <b>Platonus</b> жүйесіне кіру (platonus.kstu.kz). Универ мен
                Platonus парольдері <b>әр түрлі</b> болуы мүмкін.
            </p>
        </div>
    </div>

    <Card class="w-full border-primary/20 bg-background/50 backdrop-blur-xl">
        <div class="p-4 grid gap-5">
            <div class="grid gap-2">
                <label
                    for="p-username"
                    class="text-xs font-medium uppercase tracking-wider text-muted-foreground ml-1"
                >
                    {_("username")}
                </label>
                <Input
                    id="p-username"
                    type="text"
                    placeholder="Мысалы: Perdeev_A"
                    bind:value={username}
                    class="h-12 bg-secondary/30"
                />
            </div>

            <div class="grid gap-2">
                <label
                    for="p-password"
                    class="text-xs font-medium uppercase tracking-wider text-muted-foreground ml-1"
                >
                    {_("password")}
                </label>
                <Input
                    id="p-password"
                    type="password"
                    placeholder="••••••••"
                    bind:value={password}
                    class="h-12 bg-secondary/30"
                />
            </div>

            <Button
                onclick={submit}
                disabled={loading}
                class="h-12 text-lg font-semibold shadow-lg shadow-primary/20"
            >
                {loading ? _("loading") : _("platonus.link-button")}
            </Button>

            <p
                class="text-[10px] text-center text-muted-foreground uppercase tracking-widest"
            >
                Деректер тек бағаларды алу үшін қолданылады
            </p>
        </div>
    </Card>
</div>
