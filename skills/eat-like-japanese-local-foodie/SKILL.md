---
name: eat-like-japanese-local-foodie
description: Research restaurants the way local Japanese foodies would. Use when Codex needs to find, compare, rank, or document what to eat in Japan for a trip, especially when the user asks for local Japanese recommendations, foodie picks, Tabelog, Hyakumeiten, Michelin Japan, Japanese beef, ramen, coffee, cafes, family-friendly meals, or Japan city/area food surveys.
---

# Eat Like Japanese Local Foodie

Research Japanese restaurants source-first, in Japanese where possible, then convert the result into practical trip decisions.

## Core Workflow

1. Define the eating context:
   - city, station/neighborhood, hotel anchor, travel dates
   - meal type: lunch, dinner, snack, cafe, takeaway
   - constraints: children, smoke-free, budget, reservation, walking distance, luggage, late arrival, dietary needs
   - intent: iconic local food, serious foodie meal, casual family meal, backup near route

2. Search like a local:
   - Use Japanese station + genre searches before English searches.
   - Prefer station/neighborhood over city-level terms.
   - Search both quality and friction terms: `予約`, `行列`, `子連れ`, `禁煙`, `現金のみ`, `売り切れ`, `定休日`.
   - Search negative terms when the candidate matters: `まずい`, `微妙`, `観光客向け`, `高すぎる`.

3. Build the candidate set:
   - Tabelog area rankings and genre rankings.
   - Tabelog Award / 百名店 / Hot Pot 100 / Ramen 100 / genre-specific 100 lists.
   - Michelin for fine dining only; do not treat it as the default local-foodie source.
   - Google Maps for recent logistics, not primary taste ranking.
   - Instagram/X for recency, queues, new openings, specials, and local buzz.
   - Japanese food blogs/local media for context and hidden practical details.
   - Reservation platforms: Tabelog, TableCheck, OMAKASE, Pocket Concierge, restaurant official site.

4. Cross-check each serious candidate:
   - Tabelog score, review count, genre, awards, area ranking.
   - Google Maps rating, review count, latest reviews, language mix.
   - Recent hours/closed days from official site or recent Google/Tabelog data.
   - Menu/pricing: lunch vs dinner, courses, child pricing, cover charge, cash/card.
   - Reservation friction: walk-in, phone-only, online booking, cancellation policy.
   - Physical fit: counter/table/private room, stroller/luggage, smoke-free, child-friendly.
   - Route fit from trip anchor and likely day itinerary.
   - Photos: actual dish quality, menu board, queue, clientele, seating, portion size.

5. Rank for the user’s trip, not abstract quality:
   - `Go`: high confidence and fits itinerary.
   - `Maybe`: good but has friction, cost, distance, or duplicate role.
   - `Backup`: useful near route, lower stakes, logistics-first.
   - `Skip`: weak signal, tourist-trap signal, too far, closed, not child-fit, or redundant.

## Japanese Search Patterns

Use combinations like:

```text
<station> <genre> 名店
<station> <genre> 食べログ
<station> <genre> 百名店
<station> <genre> 子連れ
<station> <genre> 予約
<station> <genre> 行列
<station> <genre> ランチ
<station> <genre> ディナー
<station> <genre> 穴場
<station> <genre> 老舗
<station> <genre> 地元
<restaurant name> 評判
<restaurant name> 口コミ
<restaurant name> 予約困難
<restaurant name> 子連れ
<restaurant name> まずい
<restaurant name> 現金のみ
```

Useful Osaka area terms:

```text
なんば
難波
日本橋
裏なんば
法善寺横丁
千日前
道頓堀
心斎橋
梅田
天満
福島
```

Useful genre terms:

```text
お好み焼き
たこ焼き
うどん
焼肉
ホルモン
すき焼き
しゃぶしゃぶ
串カツ
ラーメン
カレー
寿司
天ぷら
居酒屋
喫茶店
カフェ
和菓子
```

Useful social searches:

```text
#大阪グルメ
#難波グルメ
#裏なんば
#関西グルメ
#大阪ランチ
#大阪ディナー
#大阪カフェ
#食べログ百名店
```

## How Foodies Actually Behave

- They start from a dish or neighborhood, not “best restaurants in Osaka”.
- They keep separate lists for serious meals, casual meals, snacks, backups, and late-night options.
- They care about timing: when queues form, when popular items sell out, lunch value, last order, and closed days.
- They read bad reviews deliberately to understand failure modes.
- They look at reviewer credibility and photo evidence, not just star ratings.
- They use Tabelog for Japanese taste signal and Google Maps for current logistics.
- They know a 3.4 casual shop on Tabelog can be excellent; 3.5+ is strong; 4.0+ is elite.
- They do not assume Michelin equals best local meal; it is more useful for expensive destination dining.
- They check whether a place is popular with locals, tourists, office workers, students, families, or influencers.
- They check the ordering system before going: ticket machine, QR order, course only, one-drink rule, cash-only.
- They choose by route fit. A good restaurant near the plan usually beats a great restaurant that breaks the day.
- They avoid overfitting one ranking. Consensus across Tabelog, recent Japanese reviews, photos, and route fit matters.

## Tourist-Trap Filters

Flag and de-prioritize when several are true:

- Very high Google score but low/flat Tabelog signal.
- Review base dominated by first-time foreign tourists.
- Generic “Kobe beef / wagyu experience” language with weak Japanese local reviews.
- Aggressive multilingual street signage, touting, laminated mega-menu, or all-in-one “Japan food” offer.
- Recent reviews mention rushed service, bait pricing, forced courses, hidden fees, or poor value.
- Photos show style/novelty but not food quality.
- Location is prime tourist corridor with no local-review support.

Do not automatically skip tourist-friendly places. They can be correct when the user needs English, easy booking, predictable child fit, or low friction. Label them honestly.

## Output Shape

For research notes, prefer:

1. Short answer / ranked shortlist.
2. Decision table:
   - priority
   - place
   - area
   - genre
   - signal
   - route/logistics
   - practical read
3. Detail cards only for serious candidates:
   - why go
   - what to order
   - avoid/risks
   - reservation/queue
   - child/logistics
   - map link
   - source links
4. “How to use this list” section:
   - where to book
   - which day/route it fits
   - what to do if queue is bad
   - which candidates are backups

When saving into a trip repo, put the note near the relevant trip folder and link it from the trip index. Keep source links in the note.

## Source Standards

- Browse for current restaurant data. Hours, rankings, closures, prices, and reviews change.
- Prefer official restaurant/Tabelog/TableCheck pages for hours, pricing, reservations, and closures.
- Use Reddit/social/blogs as color, not sole evidence.
- Never invent exact prices, opening hours, awards, or closed days.
- If a signal is conflicting, state the conflict and mark it for verification.
- Do not quote long reviews. Summarize patterns and link sources.
