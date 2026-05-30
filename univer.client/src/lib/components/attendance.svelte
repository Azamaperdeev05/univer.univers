<script lang="ts">
    import * as Drawer from "./ui/drawer"
    import * as Tabs from "./ui/tabs"

    import { _ } from "$lib/i18n"
    import type { Attestation, Mark, PlatonusDetailedClassType } from "$api"
    import Marks from "./marks.svelte"
    import { groupBy } from "$lib/utils"
    import { Skeleton } from "$lib/components/ui/skeleton"
    import { useApi } from "$api"

    let attestation = $state<Attestation>()
    let currentTerm = $state(2)
    const platonusLinked = true
    let isOpen = $state(false)

    export function open(value: Attestation, term: number = 2) {
        attestation = value
        currentTerm = term
        isOpen = true
    }
    export function close() {
        attestation = undefined
    }
    let groups = $derived(
        attestation
            ? groupBy(attestation.attendance, ({ part }) => part.split("(")[0])
            : new Map<string, Attestation["attendance"]>(),
    )

    let activeTab = $derived(
        Array.from(groups.keys()).reduce((active, value) =>
            active.localeCompare(value) === 1 ? active : value,
        ),
    )
    const getSum = (marks: Mark[]) =>
        marks.reduce((sum, [_, value]) => sum + (parseInt(`${value}`) || 0), 0)

    const api = useApi()
    const platonusQuery = $derived(
        isOpen &&
            attestation?.subject_id &&
            attestation?.query_id
            ? api.fetchSubjectDetails(
                  currentTerm,
                  attestation.subject_id,
                  attestation.query_id,
              )
            : null,
    )

    const monthNames = [
        "Қаңтар",
        "Ақпан",
        "Наурыз",
        "Сәуір",
        "Мамыр",
        "Маусым",
        "Шілде",
        "Тамыз",
        "Қыркүйек",
        "Қазан",
        "Қараша",
        "Желтоқсан",
    ]

    const getFlattenedMarks = (data: PlatonusDetailedClassType[]) => {
        let result = []
        if (!data || !Array.isArray(data)) return []
        for (const classType of data) {
            let monthsMap = new Map()
            if (classType.Marks) {
                // Платформдағы Marks структурасы: { monthId: { Marks: { dayId: [Marks] } } }
                for (const monthId in classType.Marks) {
                    const monthObj = classType.Marks[monthId]?.Marks
                    if (!monthObj) continue

                    for (const dayId in monthObj) {
                        const marksArr = monthObj[dayId]
                        if (!marksArr || !Array.isArray(marksArr)) continue

                        for (const m of marksArr) {
                            if (!m.MarkDate) continue
                            const mMonth = m.MarkDate.Month
                            const mDay = m.MarkDate.Day

                            if (!monthsMap.has(mMonth)) {
                                monthsMap.set(mMonth, {
                                    id: mMonth,
                                    name:
                                        monthNames[mMonth - 1] ||
                                        `${mMonth}-ай`,
                                    days: [],
                                })
                            }
                            monthsMap.get(mMonth).days.push({
                                day: mDay,
                                mark:
                                    typeof m.Mark === "number"
                                        ? Math.round(m.Mark)
                                        : m.Mark,
                            })
                        }
                    }
                }
            }

            let sortedMonths = Array.from(monthsMap.values()).sort(
                (a, b) => a.id - b.id,
            )
            for (let m of sortedMonths) {
                m.days.sort((a, b) => a.day - b.day)
            }

            result.push({
                name: classType.Name || "Пән",
                tutor: classType.TutorFullName || "",
                months: sortedMonths,
            })
        }
        return result
    }

    let flattenedMarks = $derived(getFlattenedMarks(platonusQuery?.data))

    const getShortMonth = (name: string) => {
        if (!name) return ""
        const mappings: Record<string, string> = {
            "Қаңтар": "ҚАҢ",
            "Ақпан": "АҚП",
            "Наурыз": "НАУ",
            "Сәуір": "СӘУ",
            "Мамыр": "МАМ",
            "Маусым": "МАУ",
            "Шілде": "ШІЛ",
            "Тамыз": "ТАМ",
            "Қыркүйек": "ҚЫР",
            "Қазан": "ҚАЗ",
            "Қараша": "ҚАР",
            "Желтоқсан": "ЖЕЛ"
        }
        return mappings[name] || name.substring(0, 3).toUpperCase()
    }

    const getChronologicalDays = (months: any[]) => {
        let list: { monthName: string; day: number; mark: number }[] = []
        if (!months || !Array.isArray(months)) return list
        for (let m of months) {
            if (m && m.days) {
                for (let d of m.days) {
                    list.push({
                        monthName: m.name || "",
                        day: d.day,
                        mark: d.mark
                    })
                }
            }
        }
        return list
    }
</script>

<Drawer.Root onClose={close} bind:open={isOpen}>
    <Drawer.Content class="mx-auto w-[90%] max-h-[96%] max-w-2xl bg-neutral-950 border border-white/10 rounded-t-3xl shadow-2xl">
        {#if attestation}
            <Drawer.Header class="px-5 pb-3 pt-5">
                <Drawer.Title class="text-left bg-gradient-to-r from-white to-neutral-400 bg-clip-text text-transparent font-extrabold tracking-tight text-xl md:text-2xl"
                    >{attestation.subject}</Drawer.Title
                >
                <div class="flex gap-3 mt-4 border-b border-white/5 pb-5 overflow-x-auto scroll-container">
                    {#each attestation.attestation as [label, value]}
                        <div
                            class="flex flex-col items-start bg-neutral-900/40 border border-white/[0.04] backdrop-blur-md rounded-2xl px-4 py-2.5 min-w-[90px] flex-1 relative overflow-hidden group hover:border-white/[0.08] transition-all duration-300"
                        >
                            <!-- Color-coded Progress Indicator bar under the card -->
                            <div 
                                class="absolute bottom-0 left-0 h-[3px] rounded-full transition-all duration-500 ease-out" 
                                style="width: {value}%; background: {value >= 90 ? 'linear-gradient(90deg, #10b981, #34d399)' : value >= 75 ? 'linear-gradient(90deg, #06b6d4, #22d3ee)' : value >= 50 ? 'linear-gradient(90deg, #f59e0b, #fbbf24)' : 'linear-gradient(90deg, #f43f5e, #fb7185)'}"
                            ></div>
                            <span class="text-[9px] uppercase text-muted-foreground font-bold tracking-wider">{label}</span>
                            <span class="text-lg font-extrabold mt-1 text-foreground transition-transform group-hover:scale-105 duration-200"
                                class:text-emerald-400={value >= 90}
                                class:text-cyan-400={value >= 75 && value < 90}
                                class:text-amber-400={value >= 50 && value < 75}
                                class:text-rose-400={value < 50}
                            >{value}</span>
                        </div>
                    {/each}
                </div>
            </Drawer.Header>

            {#if attestation.subject_id}
                <div class="overflow-y-auto px-5 pb-5 space-y-5 min-h-[120px] scroll-container">
                    {#if platonusQuery?.state === "load" || platonusQuery?.state === "update"}
                        <div class="space-y-4">
                            <Skeleton class="h-28 w-full rounded-2xl bg-neutral-900/50" />
                            <Skeleton class="h-28 w-full rounded-2xl bg-neutral-900/50" />
                        </div>
                    {:else if platonusQuery?.data && flattenedMarks.length > 0}
                        {#each flattenedMarks as category}
                            {@const dayList = getChronologicalDays(category.months)}
                            {@const classType = category.name.split("--")[1] ?? category.name}
                            <div class="bg-neutral-900/25 border border-white/[0.04] backdrop-blur-md rounded-2xl p-4 space-y-3.5 hover:border-white/[0.07] transition-all duration-300 shadow-md">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center gap-2.5">
                                        <!-- Sleek Class Type Badge -->
                                        <span 
                                            class="inline-flex items-center px-3 py-1 rounded-lg text-[10px] font-extrabold uppercase tracking-wider
                                                {classType.toLowerCase() === 'l' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-[0_0_12px_rgba(99,102,241,0.1)]' : 
                                                 classType.toLowerCase() === 'lab' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_12px_rgba(16,185,129,0.1)]' : 
                                                 'bg-violet-500/10 text-violet-400 border border-violet-500/20 shadow-[0_0_12px_rgba(139,92,246,0.1)]'}"
                                        >
                                            {classType}
                                        </span>
                                        <span class="text-sm font-bold text-foreground">
                                            {category.name.split("--")[0]}
                                        </span>
                                    </div>
                                    <!-- count indicators -->
                                    <span class="text-[10px] text-muted-foreground bg-white/5 rounded-full px-2.5 py-0.5 font-bold">
                                        {dayList.length} баға
                                    </span>
                                </div>
                                {#if category.tutor}
                                    <div class="flex items-center gap-1.5 text-xs text-muted-foreground pl-0.5">
                                        <svg class="w-3.5 h-3.5 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                        </svg>
                                        <span class="font-medium">{category.tutor}</span>
                                    </div>
                                {/if}

                                {#if dayList.length > 0}
                                    <!-- Horizontal Timeline -->
                                    <div class="overflow-x-auto w-full py-1 scroll-container">
                                        <div class="flex gap-2.5 min-w-full">
                                            {#each dayList as item}
                                                <div 
                                                    class="w-14 h-[76px] flex flex-col justify-between items-center p-2 rounded-xl bg-neutral-950/50 border border-white/[0.03] backdrop-blur-sm relative overflow-hidden group hover:bg-neutral-900/70 hover:scale-105 transition-all duration-200 flex-shrink-0 cursor-default
                                                        {item.mark >= 90 ? 'hover:shadow-[0_0_15px_rgba(16,185,129,0.12)] hover:border-emerald-500/35' : 
                                                         item.mark >= 75 ? 'hover:shadow-[0_0_15px_rgba(6,182,212,0.12)] hover:border-cyan-500/35' : 
                                                         item.mark >= 50 ? 'hover:shadow-[0_0_15px_rgba(245,158,11,0.12)] hover:border-amber-500/35' : 
                                                         'hover:shadow-[0_0_15px_rgba(244,63,94,0.12)] hover:border-rose-500/35'}"
                                                >
                                                    <div class="flex flex-col items-center">
                                                        <span class="text-[8px] font-extrabold text-muted-foreground opacity-85 tracking-widest">{getShortMonth(item.monthName)}</span>
                                                        <span class="text-xs font-bold text-foreground -mt-0.5">{item.day}</span>
                                                    </div>
                                                    
                                                    <!-- Grade display -->
                                                    <span 
                                                        class="text-xs font-extrabold tracking-tight px-1.5 py-0.5 rounded-md w-full text-center transition-all duration-300
                                                            {item.mark >= 90 ? 'text-emerald-400 bg-emerald-500/5 group-hover:bg-emerald-500/10' : 
                                                             item.mark >= 75 ? 'text-cyan-400 bg-cyan-500/5 group-hover:bg-cyan-500/10' : 
                                                             item.mark >= 50 ? 'text-amber-400 bg-amber-500/5 group-hover:bg-amber-500/10' : 
                                                             'text-rose-400 bg-rose-500/5 group-hover:bg-rose-500/10'}"
                                                    >
                                                        {item.mark}
                                                    </span>
                                                </div>
                                            {/each}
                                        </div>
                                    </div>
                                {:else}
                                    <div class="text-xs text-muted-foreground italic bg-neutral-950/20 p-4 rounded-xl text-center border border-white/[0.02]">
                                        {_("no-data")}
                                    </div>
                                {/if}
                            </div>
                        {/each}
                    {:else if platonusQuery?.state === "ready" && flattenedMarks.length === 0}
                        <div
                            class="flex flex-col items-center justify-center py-12 text-muted-foreground"
                        >
                            <p class="font-medium text-sm">{_("no-data")}</p>
                        </div>
                    {:else}
                        <div class="space-y-4">
                            <Skeleton class="h-28 w-full rounded-2xl bg-neutral-900/50" />
                            <Skeleton class="h-28 w-full rounded-2xl bg-neutral-900/50" />
                        </div>
                    {/if}
                </div>
            {/if}
        {:else}
            <div class="p-6 text-center text-muted-foreground">{_("no-data")}</div>
        {/if}
    </Drawer.Content>
</Drawer.Root>

<style>
    .scroll-container {
        scrollbar-width: thin;
        scrollbar-color: rgba(255, 255, 255, 0.08) transparent;
    }
    .scroll-container::-webkit-scrollbar {
        height: 5px;
        width: 5px;
    }
    .scroll-container::-webkit-scrollbar-track {
        background: transparent;
    }
    .scroll-container::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 99px;
    }
    .scroll-container::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.16);
    }
</style>
