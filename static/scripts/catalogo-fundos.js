(() => {
    const resultsSelector = "#catalog-results";
    let currentRequest = null;

    function updateBulkBar() {
        const available = [...document.querySelectorAll(".fund-selection:not(:disabled)")];
        const selected = available.filter((checkbox) => checkbox.checked);
        const count = document.querySelector("#bulk-selected-count");
        const button = document.querySelector("#bulk-add-button");
        const selectAll = document.querySelector("#select-visible-funds");
        if (count) count.textContent = selected.length;
        if (button) button.disabled = selected.length === 0;
        if (selectAll) {
            selectAll.checked = available.length > 0 && selected.length === available.length;
            selectAll.indeterminate = selected.length > 0 && selected.length < available.length;
            selectAll.disabled = available.length === 0;
        }
    }

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
            updateBulkBar();
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
            const selection = form.closest("tr")?.querySelector(".fund-selection");
            if (selection) {
                selection.checked = result.added;
                selection.disabled = result.added;
                selection.title = result.added ? "Já está na sua carteira" : "";
            }
            const counter = document.querySelector("#portfolio-count");
            if (counter) counter.textContent = result.portfolio_count;
            updateBulkBar();
        } catch (error) {
            form.submit();
        } finally {
            button.disabled = false;
        }
    });

    document.addEventListener("change", (event) => {
        if (event.target.matches("#select-visible-funds")) {
            document.querySelectorAll(".fund-selection:not(:disabled)").forEach((checkbox) => {
                checkbox.checked = event.target.checked;
            });
        }
        if (event.target.matches("#select-visible-funds, .fund-selection")) updateBulkBar();
    });

    document.addEventListener("submit", async (event) => {
        const form = event.target.closest("#bulk-portfolio-form");
        if (!form) return;
        event.preventDefault();

        const button = form.querySelector("button[type='submit']");
        const originalText = button.textContent;
        button.disabled = true;
        button.textContent = "Adicionando...";
        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const result = await response.json();
            const counter = document.querySelector("#portfolio-count");
            if (counter) counter.textContent = result.portfolio_count;
            await loadResults(window.location.href, false);
        } catch (error) {
            form.submit();
        } finally {
            button.textContent = originalText;
            updateBulkBar();
        }
    });

    window.addEventListener("popstate", () => loadResults(window.location.href, false));
    updateBulkBar();
})();
