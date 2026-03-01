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
    let platonusLinked = $state(localStorage.getItem("platonus_linked") === "1")
    let isOpen = $state(false)

    export function open(value: Attestation, term: number = 2) {
        attestation = value
        currentTerm = term
        platonusLinked = localStorage.getItem("platonus_linked") === "1"
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
        platonusLinked &&
            isOpen &&
            attestation?.subject_id &&
            attestation?.query_id
            ? api.fetchPlatonusSubjectDetails(
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
</script>

<Drawer.Root onClose={close} bind:open={isOpen}>
    <Drawer.Content class="mx-auto w-[90%] max-h-[96%] max-w-2xl">
        {#if attestation}
            <Drawer.Header class="px-4 pb-2">
                <Drawer.Title class="text-balance text-left"
                    >{attestation.subject}</Drawer.Title
                >
                <div class="flex gap-2 mt-2 border-b pb-4 overflow-x-auto">
                    {#each attestation.attestation as [label, value]}
                        <div
                            class="flex flex-col items-center bg-secondary/50 rounded-md px-3 py-1.5 min-w-[60px]"
                        >
                            <span
                                class="text-[10px] uppercase text-muted-foreground font-semibold"
                                >{label}</span
                            >
                            <span class="text-sm font-bold">{value}</span>
                        </div>
                    {/each}
                </div>
            </Drawer.Header>

            {#snippet content(attendance: Attestation["attendance"])}
                <div class="space-y-2">
                    {#each attendance as { marks, type }}
                        <div>
                            <p class="px-4">{type}</p>
                            <p class="px-4">
                                {_("sum")}: <b>{getSum(marks)}</b>
                            </p>
                            <Marks class="pb-2" {marks} />
                        </div>
                    {/each}
                </div>
            {/snippet}

            {#if platonusLinked && attestation.subject_id}
                <div class="overflow-y-auto px-4 pb-4 space-y-6 min-h-[100px]">
                    {#if platonusQuery?.state === "load" || platonusQuery?.state === "update"}
                        <div class="space-y-4">
                            <Skeleton class="h-32 w-full rounded-xl" />
                            <Skeleton class="h-32 w-full rounded-xl" />
                        </div>
                    {:else if platonusQuery?.data && flattenedMarks.length > 0}
                        {#each flattenedMarks as category}
                            <div class="space-y-2">
                                <div class="flex items-center gap-2">
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                                        {category.name.split("--")[1] ?? category.name}
                                    </span>
                                    <span class="text-sm font-medium text-foreground truncate">
                                        {category.name.split("--")[0]}
                                    </span>
                                </div>
                                {#if category.tutor}
                                    <p class="text-xs text-muted-foreground -mt-1 pl-1">{category.tutor}</p>
                                {/if}

                                {#if category.months.length > 0}
                                    <div
                                        class="overflow-x-auto w-full border border-blue-500/20 rounded-xl shadow-sm"
                                    >
                                        <table
                                            class="w-full text-center text-sm table-fixed min-w-[280px]"
                                        >
                                            <tbody>
                                                <tr class="bg-blue-500/10 dark:bg-blue-500/15">
                                                    <td
                                                        class="font-semibold border-r border-blue-500/20 text-left px-3 py-2 text-blue-700 dark:text-blue-300 w-[72px] text-xs uppercase tracking-wide"
                                                        >Айы</td
                                                    >
                                                    {#each category.months as month}
                                                        <td
                                                            colspan={month.days.length}
                                                            class="border-x border-blue-500/20 px-2 py-2 font-medium text-blue-700 dark:text-blue-300"
                                                        >
                                                            {month.name}
                                                        </td>
                                                    {/each}
                                                </tr>
                                                <tr class="bg-blue-500/5 dark:bg-blue-500/8">
                                                    <td
                                                        class="font-semibold border-r border-blue-500/20 text-left px-3 py-1.5 text-muted-foreground w-[72px] text-xs uppercase tracking-wide"
                                                        >Күн</td
                                                    >
                                                    {#each category.months as month}
                                                        {#each month.days as day}
                                                            <td
                                                                class="border-x border-blue-500/15 px-1 py-1.5 text-xs text-muted-foreground"
                                                                >{day.day}</td
                                                            >
                                                        {/each}
                                                    {/each}
                                                </tr>
                                                <tr class="bg-background">
                                                    <td
                                                        class="font-semibold border-r border-blue-500/20 text-left px-3 py-2 text-muted-foreground w-[72px] text-xs uppercase tracking-wide"
                                                        >Баға</td
                                                    >
                                                    {#each category.months as month}
                                                        {#each month.days as day}
                                                            <td
                                                                class="border-x border-blue-500/15 px-1 py-2 font-bold text-blue-600 dark:text-blue-400"
                                                            >
                                                                {day.mark}
                                                            </td>
                                                        {/each}
                                                    {/each}
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                {:else}
                                    <div
                                        class="text-xs text-muted-foreground italic bg-secondary/10 p-3 rounded-lg text-center"
                                    >
                                        {_("no-data")}
                                    </div>
                                {/if}
                            </div>
                        {/each}
                    {:else if platonusQuery?.state === "ready" && flattenedMarks.length === 0}
                        <div
                            class="flex flex-col items-center justify-center py-10 text-muted-foreground"
                        >
                            <p>{_("no-data")}</p>
                        </div>
                    {:else}
                        <div class="space-y-4">
                            <Skeleton class="h-32 w-full rounded-xl" />
                            <Skeleton class="h-32 w-full rounded-xl" />
                        </div>
                    {/if}
                </div>
            {:else if groups.size > 1}
                <Tabs.Root class="overflow-y-auto" value={activeTab}>
                    {#each groups.entries() as [key, value]}
                        <Tabs.Content class="mt-0" value={key}>
                            {@render content(value)}
                        </Tabs.Content>
                    {/each}
                    <Drawer.Footer class="px-4 pt-2">
                        <Tabs.List>
                            {#each groups as [key]}
                                <Tabs.Trigger class="flex-1" value={key}
                                    >{key}</Tabs.Trigger
                                >
                            {/each}
                        </Tabs.List>
                    </Drawer.Footer>
                </Tabs.Root>
            {:else}
                <div class="overflow-y-auto">
                    {#each groups as [_, value]}
                        {@render content(value)}
                    {/each}
                    <div
                        class="mx-4 mb-4 mt-2 bg-foreground text-background flex h-10 items-center justify-center rounded-md p-1"
                    >
                        {#each groups as [key]}
                            {key}
                        {/each}
                    </div>
                </div>
            {/if}
        {:else}
            {_("no-data")}
        {/if}
    </Drawer.Content>
</Drawer.Root>
