import time, json

accounts = [
    ("dylan522p", "Dylan Patel"),
    ("munster_gene", "Gene Munster"),
    ("GavinSBaker", "Gavin Baker"),
    ("kobeissiletter", "Kobeissi Letter"),
    ("firstadopter", "Tae Kim"),
]

for handle, name in accounts:
    url = "https://x.com/" + handle
    goto_url(url)
    time.sleep(4)

    # Scroll to trigger lazy loading
    js("window.scrollBy(0, 800)")
    time.sleep(1.5)
    js("window.scrollBy(0, 800)")
    time.sleep(1.5)

    tweets_raw = js("(function(){var tweets=document.querySelectorAll('div[data-testid=\"tweetText\"]');var r=[];tweets.forEach(function(t,i){if(i<3){r.push(t.textContent.trim().substring(0,400));}});if(r.length===0){var alt=document.querySelectorAll('article[data-testid=\"tweet\"] div[lang]');alt.forEach(function(a,i){if(i<3){r.push(a.textContent.trim().substring(0,400));}});}if(r.length===0){r.push('no tweets');}return JSON.stringify(r);})()")

    try:
        tl = json.loads(tweets_raw)
    except:
        tl = [str(tweets_raw)[:300]]

    print("")
    print("=" * 60)
    print(name + " (@" + handle + ")")
    print("=" * 60)
    for j, t in enumerate(tl[:3]):
        if t and t != 'no tweets':
            print("")
            print(t[:400])
    if not tl or all(t == 'no tweets' for t in tl):
        print("(no tweets)")
