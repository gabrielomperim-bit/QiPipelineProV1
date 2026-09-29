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

    document.addEventListener("submit", async (event) => {
        const form = event.target.closest(".portfolio-toggle-form");
        if (!form) return;
        event.preventDefault();

        const button = form.querySelector("button");
        button.disabled = true;
        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const result = await response.json();
            button.classList.toggle("is-selected", result.added);
            button.setAttribute("aria-pressed", result.added ? "true" : "false");
            button.textContent = result.added ? "✓ Na carteira" : "+ Adicionar";
            const counter = document.querySelector("#portfolio-count");
            if (counter) counter.textContent = result.portfolio_count;
        } catch (error) {
            form.submit();
        } finally {
            button.disabled = false;
        }
    });

    window.addEventListener("popstate", () => loadResults(window.location.href, false));
})();
