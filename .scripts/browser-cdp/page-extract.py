# Extract table data from the page
data = js("""
(function() {
    // Try to find table-like structures
    const tables = document.querySelectorAll('table');
    if (tables.length > 0) {
        return 'Found ' + tables.length + ' tables. First table: ' + tables[0].textContent.substring(0, 2000);
    }

    // Try grid/div-based tables
    const grids = document.querySelectorAll('[role="grid"], [role="table"]');
    if (grids.length > 0) {
        return 'Found ' + grids.length + ' grid/table roles. First: ' + grids[0].textContent.substring(0, 2000);
    }

    // Try to find data rows with numbers
    const allDivs = document.querySelectorAll('div');
    const candidates = [];
    for (const d of allDivs) {
        const text = d.textContent.trim();
        if (text.match(/Engine Products|Fastening Systems|Engineered Structures|Forged Wheels/)) {
            // Get parent context
            let parent = d;
            for (let i = 0; i < 3; i++) {
                parent = parent.parentElement;
                if (!parent) break;
                const ptext = parent.textContent.trim();
                if (ptext.length > 100 && ptext.length < 3000) {
                    candidates.push(ptext);
                    break;
                }
            }
        }
    }
    return JSON.stringify(candidates.slice(0, 4));
})()
""")
print("Table data:", data)

# Also try getting the full page text in a target area
full_text = js("""
(function() {
    // Find the main content area
    const main = document.querySelector('main, [role="main"], .main-content');
    if (main) return main.textContent.substring(0, 5000);
    return document.body.textContent.substring(0, 5000);
})()
""")
print("--- Full page excerpt ---")
print(full_text)
