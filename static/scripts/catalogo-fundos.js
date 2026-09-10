(() => {
    const resultsSelector = "#catalog-results";
    let currentRequest = null;

    async function loadResults(url, updateHistory) {
        const currentResults = document.querySelector(resultsSelector);
        if (!currentResults) return;

        if (currentRequest) currentRequest.abort();
        currentRequest = new AbortController();
        currentResults.classList.add("is-loading");
        currentResults.setAttribute("aria-busy", "true");

        try {
            const response = await fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                signal: currentRequest.signal,
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const html = await response.text();
            const nextDocument = new DOMParser().parseFromString(html, "text/html");
            const nextResults = nextDocument.querySelector(resultsSelector);
            if (!nextResults) throw new Error("Área de resultados não encontrada");

            currentResults.replaceWith(nextResults);
            if (updateHistory) window.history.pushState({}, "", url);
        } catch (error) {
            if (error.name !== "AbortError") window.location.assign(url);
        } finally {
            const visibleResults = document.querySelector(resultsSelector);
            if (visibleResults) {
                visibleResults.classList.remove("is-loading");
                visibleResults.removeAttribute("aria-busy");
            }
            currentRequest = null;
        }
    }

    document.addEventListener("click", (event) => {
        const link = event.target.closest(".pagination-links a");
        if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;

        event.preventDefault();
        loadResults(link.href, true);
    });

    window.addEventListener("popstate", () => loadResults(window.location.href, false));
})();
