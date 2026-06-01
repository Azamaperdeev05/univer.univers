<script lang="ts">
    import { useApi } from "$api"
    import AppBar from "$lib/components/app-bar.svelte"
    import Loader from "$lib/components/loader.svelte"
    import Page from "$lib/layouts/page.svelte"
    import { _ } from "$lib/i18n"

    const api = useApi()
    const query = api.fetchTranscript()
</script>

<Page>
    {#snippet header()}
        <AppBar title={_("exams")} />
    {/snippet}
    
    <div class="grid mx-auto p-3 gap-4 max-w-md w-full pb-20">
        {#if query.loading}
            <Loader />
        {:else if query.data}
            {@const { semesters, overall_gpa, min_gpa, year_of_study } = query.data}
            
            {#if semesters && semesters.length > 0}
                {#each semesters as semester}
                    <div class="bg-white/5 border border-white/10 rounded-2xl overflow-hidden shadow-lg backdrop-blur-md flex flex-col gap-0">
                        <!-- Semester Header -->
                        <div class="bg-white/5 px-4 py-3 border-b border-white/10 flex justify-between items-center">
                            <span class="font-bold text-white text-sm">{semester.name}</span>
                            <span class="bg-primary/20 text-primary border border-primary/30 px-2 py-0.5 rounded-lg text-xs font-semibold">
                                GPA: {semester.gpa}
                            </span>
                        </div>
                        
                        <!-- Subjects Table -->
                        <div class="divide-y divide-white/5">
                            {#each semester.subjects as subject}
                                <div class="px-4 py-3 flex items-center justify-between text-xs xs:text-sm hover:bg-white/[0.02] transition-colors">
                                    <div class="flex items-start gap-2.5 max-w-[65%]">
                                        <span class="text-white/40 font-mono select-none w-4">{subject.number}</span>
                                        <span class="text-white/90 font-medium leading-relaxed">{subject.name}</span>
                                    </div>
                                    <div class="flex items-center gap-4 text-right">
                                        <div class="flex flex-col">
                                            <span class="text-white/80 font-bold">{subject.percent}%</span>
                                            <span class="text-[10px] text-white/40">Пайыз</span>
                                        </div>
                                        <div class="flex flex-col min-w-[32px]">
                                            <span class="text-primary font-bold">{subject.points}</span>
                                            <span class="text-[10px] text-white/40">Балл</span>
                                        </div>
                                    </div>
                                </div>
                            {/each}
                        </div>
                    </div>
                {/each}
            {/if}
            
            <!-- Overall Course GPA Summary Card -->
            <div class="bg-primary/10 border border-primary/20 rounded-2xl p-5 flex flex-col gap-2 shadow-lg backdrop-blur-md">
                <div class="flex justify-between items-center border-b border-primary/10 pb-2">
                    <span class="text-sm font-bold text-white">{year_of_study} Курс қорытындысы</span>
                    <span class="bg-primary text-white px-3 py-1 rounded-xl text-sm font-black">
                        GPA: {overall_gpa}
                    </span>
                </div>
                <p class="text-xs text-white/70 leading-relaxed mt-1">
                    Курстан курсқа ауыстыру үшін минималды GPA : <span class="font-bold text-primary">{min_gpa}</span>
                </p>
            </div>
        {:else}
            <div class="text-center text-white/50 py-8">
                {_("no-data")}
            </div>
        {/if}
    </div>
</Page>

