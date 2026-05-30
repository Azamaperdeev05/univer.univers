<script lang="ts">
    import { subject, useApi } from "$api"
    import AppBar from "$lib/components/app-bar.svelte"
    import { Skeleton } from "$lib/components/ui/skeleton"
    import { _ } from "$lib/i18n"
    import Page from "$lib/layouts/page.svelte"
    import { nullish, randInt } from "$lib/utils"
    import { ChevronDown } from "lucide-svelte"
    import FilesList from "./files-list.svelte"

    const api = useApi()

    // Determine current semester default based on current month
    const currentMonth = new Date().getMonth() + 1
    const defaultSemester = (currentMonth >= 1 && currentMonth <= 8) ? 2 : 1
    
    // States for Academic Year and Period
    let year = $state(2025)
    let semester = $state(defaultSemester)
    let activeId = $state<string | null>(null)

    // Derived reactive query
    let query = $derived(api.fetchFolders(year, semester))

    function toggleAccordion(id: string) {
        activeId = activeId === id ? null : id
    }
</script>

<Page>
    {#snippet header()}
        <AppBar>
            {#snippet title()}
            {#if query.state === "update"}
                {_("updating")}
            {:else}
                {_("umkd")}
            {/if}
            {/snippet}
        </AppBar>
    {/snippet}

    <div class="grid mx-auto p-2 gap-2 max-w-md w-full">
        <!-- Term Dropdowns Selector Section -->
        <div class="p-4 rounded-2xl bg-card border border-border flex flex-col gap-4 shadow-sm mb-1">
            <div class="flex gap-4">
                <div class="flex-1 flex flex-col gap-1.5">
                    <label for="year-select" class="text-xs font-semibold opacity-75">{_("academic-year") ?? "Оқу жылы"}</label>
                    <select id="year-select" bind:value={year} class="w-full bg-input/40 border border-border p-2 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary">
                        <option value={2025}>2025-2026</option>
                        <option value={2026}>2026-2027</option>
                        <option value={2027}>2027-2028</option>
                    </select>
                </div>
                <div class="flex-1 flex flex-col gap-1.5">
                    <label for="period-select" class="text-xs font-semibold opacity-75">{_("academic-period") ?? "Академиялық кезең"}</label>
                    <select id="period-select" bind:value={semester} class="w-full bg-input/40 border border-border p-2 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary">
                        <option value={1}>1</option>
                        <option value={2}>2</option>
                        <option value={-1}>Қосымша академиялық кезең 1</option>
                        <option value={-2}>Қосымша академиялық кезең 2</option>
                    </select>
                </div>
            </div>
        </div>

        {#if nullish(query.data)}
            {#each {length: 6} as _}
                <div class="p-4 rounded-2xl bg-card border border-border flex flex-col gap-2">
                    <Skeleton symbols={subject()} />
                    <Skeleton symbols={randInt(10, 20)} />
                </div>
            {/each}
        {:else}
            {#each query.data as {id, subject, type} (id)}
                <div class="rounded-2xl bg-card border border-border overflow-hidden flex flex-col transition-all shadow-sm">
                    <!-- Accordion Trigger Button Card -->
                    <button 
                        onclick={() => toggleAccordion(id)} 
                        class="p-4 flex items-center justify-between text-left hover:bg-input/10 active:bg-input/20 transition-all w-full focus:outline-none"
                    >
                        <div class="flex flex-col gap-0.5 pr-2">
                            <span class="font-bold text-foreground text-sm leading-snug">{subject}</span>
                            <span class="text-xs opacity-70 leading-normal">{type}</span>
                        </div>
                        <ChevronDown 
                            size={18} 
                            class="opacity-70 transition-transform duration-300 shrink-0" 
                            style="transform: rotate({activeId === id ? 180 : 0}deg)" 
                        />
                    </button>

                    <!-- Accordion Content Panel (with Smooth CSS Grid Transition) -->
                    <div class="accordion-content" class:open={activeId === id}>
                        <div class="accordion-inner">
                            <div class="p-4 pt-1 flex flex-col gap-2 bg-secondary/10 border-t border-border/40">
                                {#if activeId === id}
                                    <FilesList {id} {year} {semester} />
                                {/if}
                            </div>
                        </div>
                    </div>
                </div>
            {:else}
                <div class="p-8 text-center text-sm opacity-60">
                    {_("no-data") ?? "Деректер табылмады"}
                </div>
            {/each}
        {/if}
    </div>
</Page>

<style>
    .accordion-content {
        display: grid;
        grid-template-rows: 0fr;
        transition: grid-template-rows 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s ease-out;
        opacity: 0;
    }
    .accordion-content.open {
        grid-template-rows: 1fr;
        opacity: 1;
    }
    .accordion-inner {
        overflow: hidden;
    }
</style>
