"""Formal pins must resolve to external instance nodes, with explicit failures."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from voice_kcl_alias_instrument import resolve_pin_alias


class AliasTests(unittest.TestCase):
    DECK='XIC3 QB_COLLECTOR NEG4_REF POS10_V NEG10_V IC3_OUT LM741'

    def test_external_node_and_case(self):
        self.assertEqual(resolve_pin_alias(self.DECK,'1'),'qb_collector')
        self.assertEqual(resolve_pin_alias(self.DECK.lower(),'28'),'ic3_out')

    def test_missing_duplicate_and_wrong_model(self):
        for text in ('',self.DECK+'\n'+self.DECK,self.DECK.replace('LM741','OTHER')):
            with self.assertRaises(ValueError):resolve_pin_alias(text,'1')

    def test_internal_node_is_not_a_formal_pin(self):
        with self.assertRaises(ValueError):resolve_pin_alias(self.DECK,'3')


if __name__=='__main__':unittest.main()
