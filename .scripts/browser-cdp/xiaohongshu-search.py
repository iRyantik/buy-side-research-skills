# Search Xiaohongshu for a topic
import time

goto_url("https://www.xiaohongshu.com/search_result?keyword=AI%E8%82%A1%E7%A5%A8&type=51")
wait_for_load()
time.sleep(3)

# Scroll to load more
js("window.scrollBy(0, 800)")
time.sleep(1)

info = page_info()
print("URL:", info["url"])
print("Title:", info["title"])

# Extract note titles
notes = js("""
(function() {
    var items = document.querySelectorAll('.note-item, [class*="note"], .feeds-page > *');
    var results = [];
    items.forEach(function(item, i) {
        if (i < 6) {
            var title = item.querySelector('.title, [class*="title"], .note-title, [data-v-] span') || item;
            var text = title.textContent.trim();
            if (text.length > 5 && text.length < 200) {
                results.push(text);
            }
        }
    });
    if (results.length === 0) {
        // Fallback: get any visible text chunks
        var all = document.querySelectorAll('span, p, .desc, [class*="desc"]');
        all.forEach(function(el, i) {
            if (i < 10) {
                var t = el.textContent.trim();
                if (t.length > 10) results.push(t.substring(0, 150));
            }
        });
    }
    return JSON.stringify(results.slice(0, 6));
})()
""")
print("Notes found:", notes)
