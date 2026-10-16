import csv, json
from collections import defaultdict

rows = list(csv.DictReader(open('food_bank_trends_california_dma.csv')))
data = {}
for r in rows:
    name = r['dma_name']
    if name not in data:
        data[name] = {'code': r['dma_code'], 'weeks': []}
    data[name]['weeks'].append({
        's': r['week_start'][:10],
        'v': int(r['search_interest']),
        'sv': int(r['scaled_search_interest'])
    })

print("Stats per DMA:")
for name, v in data.items():
    vals = [w['v'] for w in v['weeks']]
    recent = sum(vals[-13:])
    prior = sum(vals[-26:-13])
    yoy = ((recent - prior) / prior * 100) if prior > 0 else 0
    peak_idx = vals.index(max(vals))
    peak_date = v['weeks'][peak_idx]['s']
    print(f"  {name}: total={sum(vals):,} max={max(vals):,} yoy={yoy:+.1f}% peak={peak_date}")

weeks = [r['week_start'][:10] for r in rows if r['dma_name'] == 'San Francisco-Oakland-San Jose']
print(f"\nWeeks: {weeks[0]} to {weeks[-1]} (n={len(weeks)})")

# Write JSON for embedding
with open('embedded_data.json', 'w') as f:
    json.dump({'dmas': data}, f, separators=(',', ':'))
print("JSON written.")
