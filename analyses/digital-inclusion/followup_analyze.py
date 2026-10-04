"""Offline exploratory decomposition; fixed Feb–Sep 2025/2026 windows."""
from collections import Counter, defaultdict
from decimal import Decimal
from itertools import product

from api_common import write_json
from pps_analyze import load, CORE_CODES, OUTPUT, metrics, number, plain, write_csv, months
from datetime import date
from mois_analyze import validate_source, select_records, normalize_feature, FEATURES, sha256


def decompose(rows, key, label):
    groups = defaultdict(lambda: {2025: [], 2026: []})
    for row in rows:
        if not row[key].strip():
            raise ValueError(f'Missing grouping key: {key}')
        groups[row[key]][int(row['month'][:4])].append(row)
    result = []
    for identity, years in sorted(groups.items()):
        a, b = years[2025], years[2026]
        ma, mb = metrics(a), metrics(b)
        result.append(dict(
            id=identity, names=' | '.join(sorted({r[label] for r in a + b})),
            presence='both' if a and b else '2025_only' if a else '2026_only',
            rows_2025=len(a), rows_2026=len(b),
            quantity_2025=ma['representative_device_net_quantity'],
            quantity_2026=mb['representative_device_net_quantity'],
            quantity_difference=plain(number(mb['representative_device_net_quantity'])-number(ma['representative_device_net_quantity'])),
            amount_2025=ma['net_request_amount_krw'], amount_2026=mb['net_request_amount_krw'],
            amount_difference=plain(number(mb['net_request_amount_krw'])-number(ma['net_request_amount_krw'])),
        ))
    for year in (2025, 2026):
        expected = metrics([r for r in rows if r['month'].startswith(str(year))])
        for field, metric in [('quantity', 'representative_device_net_quantity'), ('amount', 'net_request_amount_krw')]:
            assert sum(number(r[f'{field}_{year}']) for r in result) == number(expected[metric])
    return sorted(result, key=lambda r: (number(r['quantity_difference']), r['id']))


def feature_pairs(rows):
    counts = Counter((normalize_feature('WHCHR_USER_MNPLT', r['WHCHR_USER_MNPLT']),
                      normalize_feature('TCTL_ELCTNC_MONITOR', r['TCTL_ELCTNC_MONITOR'])) for r in rows)
    return [dict(wheelchair=a, tactile=b, count=counts[a,b], denominator=len(rows))
            for a,b in product(('yes','no','unknown'), repeat=2)]


def main():
    rows, manifest = load('deliveries')
    assert set(months(date(2025,2,1),date(2026,9,30))) <= set(months(date.fromisoformat(manifest['start']),date.fromisoformat(manifest['end'])))
    selected = [r for r in rows if r['dtilPrdctClsfcNo'] in CORE_CODES and r['month'][:4] in ('2025','2026') and 2 <= int(r['month'][5:]) <= 9]
    tables = {}
    for scope, key, label in [('institutions','dminsttCd','dminsttNm'),('products','prdctIdntNo','prdctIdntNoNm')]:
        tables[f'pps_{scope}_comparison.csv'] = decompose(selected,key,label)
    cohorts = []
    for presence in ('both','2025_only','2026_only'):
        group = [r for r in tables['pps_institutions_comparison.csv'] if r['presence']==presence]
        cohorts.append(dict(presence=presence, institutions=len(group), **{
            field: plain(sum((number(r[field]) for r in group),Decimal(0)))
            for field in ('quantity_2025','quantity_2026','quantity_difference','amount_2025','amount_2026','amount_difference')}))
    tables['pps_institution_cohorts.csv'] = cohorts
    source, mois_manifest, manifest_path, integrity = validate_source('2026-10-03')
    used, _, flow = select_records(source)
    pairs = feature_pairs(used)
    assert sum(r['count'] for r in pairs)==len(used)
    tables['mois_feature_pairs_2026-10-03.csv'] = pairs
    patterns = Counter(tuple(normalize_feature(f,r[f]) for f in FEATURES) for r in used)
    tables['mois_feature_patterns_2026-10-03.csv'] = [dict(zip(FEATURES,p),count=n,denominator=len(used)) for p,n in sorted(patterns.items())]
    for name, table in tables.items():
        write_csv(OUTPUT/name,table)
    summary = dict(analysis_type='exploratory_descriptive_not_causal',
        comparison='February–September 2025 vs February–September 2026',
        input_sha256={'pps_deliveries.csv':manifest['csv_sha256'],'mois_devices_2026-10-03.csv':mois_manifest['dataset_sha256'], 'mois_manifest_2026-10-03.json':sha256(manifest_path)},
        mois_integrity=integrity, mois_record_flow=flow, cohorts=cohorts, feature_pairs=pairs,
        limits=['Presence means at least one change record in the selected window, not institutional entry/exit or first purchase.',
                'Zeros for absent groups refer only to the complete queried procurement scope, not all purchases.',
                'Institution IDs and product IDs are not linked across mergers or reassignments; names are retained as observed.',
                'Signed quantity includes only representative items in units of devices; amounts include all selected options/units.',
                'Feature combinations are administrative records, not compliance or usability scores; unknown is separate from no.',
                'No device-level link between procurement rows and MOIS records; no causal effect estimated.'],
        outputs={name:{'rows':len(table),'sha256':sha256(OUTPUT/name)} for name,table in tables.items()})
    write_json(OUTPUT/'followup_summary.json',summary)
    print(summary['cohorts'])
    print(pairs)
    print('Largest declines:',tables['pps_institutions_comparison.csv'][:5])
    print('Largest increases:',tables['pps_institutions_comparison.csv'][-5:])

if __name__ == '__main__':
    main()
