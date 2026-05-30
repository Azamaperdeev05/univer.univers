<script lang="ts">
    import { useApi } from "$api"
    import { Skeleton } from "$lib/components/ui/skeleton"
    import { nullish } from "$lib/utils"
    import { Download } from "lucide-svelte"
    import { _ } from "$lib/i18n"

    let { id, year, semester }: { id: string; year: number; semester: number } = $props()
    const api = useApi()
    const query = $derived(api.fetchFiles(id, year, semester))
</script>

{#if nullish(query.data)}
    <div class="p-3 bg-secondary/30 border border-border/60 rounded-xl flex items-center justify-between">
        <Skeleton symbols={15} />
        <Skeleton symbols={8} />
    </div>
{:else}
    {#each query.data as { name, size, url, teacher }}
        <a href={api.url(url)} class="p-3 bg-secondary/20 border border-border/60 rounded-xl flex items-center justify-between hover:bg-secondary/40 active:scale-[0.99] transition-all group">
            <div class="flex flex-col gap-0.5 text-left">
                <span class="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">{name}</span>
                <span class="text-xs opacity-65">{teacher}</span>
            </div>
            <div class="flex items-center gap-2 text-xs font-semibold text-primary">
                <span>{size}</span>
                <Download size={14} class="group-hover:translate-y-[1px] transition-transform" />
            </div>
        </a>
    {:else}
        <div class="p-4 text-center text-xs opacity-60">
            {_("no-files") ?? "Оқу материалдары жүктелмеген"}
        </div>
    {/each}
{/if}
