<script lang="ts">
    import { network } from "$lib/network.svelte"
    import { _ } from "$lib/i18n"
    import { WifiOff } from "lucide-svelte"
    import { fly } from "svelte/transition"
    import { onMount } from "svelte"
    import { toast } from "svelte-sonner"

    let wasOffline = $state(false)

    $effect(() => {
        if (!network.online) {
            wasOffline = true
        } else if (wasOffline) {
            toast.success(_("offline.restored"))
            wasOffline = false
        }
    })
</script>

{#if !network.online}
    <div
        transition:fly={{ y: 20 }}
        class="fixed bottom-24 left-1/2 -translate-x-1/2 z-50 bg-destructive text-destructive-foreground px-4 py-2 rounded-full shadow-lg flex items-center gap-2 text-sm font-medium"
    >
        <WifiOff size={16} />
        {_("offline")}
    </div>
{/if}
