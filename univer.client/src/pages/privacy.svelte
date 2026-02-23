<script>
    // import { fetchPrivacy } from "$api"
    import Page from "$lib/layouts/page.svelte"
    import { _ } from "$lib/i18n/index.ts"
    import AppBar from "$lib/components/app-bar.svelte"
    import Loader from "$lib/components/loader.svelte"
    import { useApi } from "$api"
    import { ChevronLeft } from "lucide-svelte"
    import { Button } from "$lib/components/ui/button"
    import { useRouter } from "$lib/router"

    const api = useApi()
    const query = api.fetchPrivacy()
    const router = useRouter()
</script>

<Page>
    {#snippet header()}
        <AppBar title={_("privacy-policy")}>
            {#snippet left()}
                <Button
                    variant="ghost"
                    size="icon"
                    onclick={() => router.back()}
                >
                    <ChevronLeft />
                </Button>
            {/snippet}
        </AppBar>
    {/snippet}
    <div class="content max-w-3xl mx-auto p-4">
        {#if query.loading}
            <Loader />
        {:else if query.data}
            {@html query.data}
        {/if}
    </div>
</Page>
