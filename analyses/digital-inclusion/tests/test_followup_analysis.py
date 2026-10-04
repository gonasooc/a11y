"""Boundaries for signed cohort decomposition and unknown feature values."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from followup_analyze import decompose, feature_pairs


def row(year, institution, quantity, amount, unit='대', option='대표품목'):
    return dict(month=f'{year}-02', dminsttCd=institution, dminsttNm=institution,
                prdctUnit=unit, optnDivCdNm=option, incdecQty=str(quantity),
                incdecAmt=str(amount), dlvrReqNo='request', corpNm='supplier')


class FollowupTests(unittest.TestCase):
    def test_cancellation_presence_and_options(self):
        records = [row(2025,'A',3,300),row(2025,'A',-3,-300),
                   row(2026,'A',2,200),row(2026,'A',9,90,'식','옵션품목'),
                   row(2025,'B',4,400),row(2026,'C',1,100)]
        result={r['id']:r for r in decompose(records,'dminsttCd','dminsttNm')}
        self.assertEqual(result['A']['presence'],'both')
        self.assertEqual(result['A']['quantity_2025'],'0')
        self.assertEqual(result['A']['quantity_difference'],'2')
        self.assertEqual(result['A']['amount_difference'],'290')
        self.assertEqual(result['B']['presence'],'2025_only')
        self.assertEqual(result['C']['presence'],'2026_only')

    def test_missing_identity_rejected(self):
        with self.assertRaises(ValueError):
            decompose([row(2025,'',1,10)],'dminsttCd','dminsttNm')

    def test_unknown_is_not_no(self):
        pairs=feature_pairs([{'WHCHR_USER_MNPLT':'불가능','TCTL_ELCTNC_MONITOR':'미제공'},
                             {'WHCHR_USER_MNPLT':'','TCTL_ELCTNC_MONITOR':'제공'}])
        counts={(r['wheelchair'],r['tactile']):r['count'] for r in pairs}
        self.assertEqual(counts['no','no'],1)
        self.assertEqual(counts['unknown','yes'],1)
        self.assertEqual(sum(counts.values()),2)
