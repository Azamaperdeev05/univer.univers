<script>
    // import { fetchPrivacy } from "$api"
    import Page from "$lib/layouts/page.svelte"
    import { _ } from "$lib/i18n/index.ts"
    import AppBar from "$lib/components/app-bar.svelte"
    import Loader from "$lib/components/loader.svelte"
    import { Button } from "$lib/components/ui/button"
    import { useApi } from "$api"

    const api = useApi()
    const query = api.fetchPrivacy()
</script>

<Page>
    {#snippet header()}
        <AppBar title={_("privacy-policy")}></AppBar>
    {/snippet}
    <div class="content max-w-3xl mx-auto p-4">
        {#if query.loading && !query.data}
            <Loader />
        {:else if query.data}
            {@html query.data}
        {:else if !query.loading && !query.data}
            <p class="text-center text-muted-foreground p-10">
                Деректер бос. Күй: {query.state}
                <br />
                <Button
                    variant="outline"
                    onclick={() => query.fetch()}
                    class="mt-4">Қайта жүктеу</Button
                >
            </p>
        {/if}
    </div>
</Page>
