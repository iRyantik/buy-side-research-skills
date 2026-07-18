# Visit key finance accounts directly and get their latest tweets
accounts = [
    ("https://x.com/elerianm", "Mohamed El-Erian"),
    ("https://x.com/LynAldenContact", "Lyn Alden"),
    ("https://x.com/NorthmanTrader", "Sven Henrich"),
    ("https://x.com/zerohedge", "zerohedge"),
]

for url, name in accounts:
    print(f"\n=== {name} ===")
    goto_url(url)
    import time
    time.sleep(2)

    tweets = js("""
    (function() {
        const articles = document.querySelectorAll('article[data-testid="tweet"]');
        const results = [];
        articles.forEach((a, i) => {
            if (i < 2) {
                const text = a.textContent.trim().substring(0, 300);
                results.push(text);
            }
        });
        if (results.length === 0) {
            // Fallback: get timeline text
            const timeline = document.querySelector('[data-testid="primaryColumn"]');
            if (timeline) results.push(timeline.textContent.trim().substring(0, 500));
            else results.push('No tweets found');
        }
        return JSON.stringify(results);
    })()
    """)
    print("Latest:", tweets)
