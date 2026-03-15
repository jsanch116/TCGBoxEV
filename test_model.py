import io
import sys
import unittest

from model import (
    TCGCard,
    TCGSet,
    TCGDistribution,
    TCGBoosterPack,
    TCGBoosterPackSlot,
)


class TestModel(unittest.TestCase):
    def test_variant_foil_zero_probability(self):
        # one foil variant card and distribution with generic foil mass
        card = TCGCard("Foo", "Mythic", price=5.0, foil_type="normal", variant="Fable")
        tcg_set = TCGSet("S", [card], bulk_price={"Mythic Foil": 1.0})
        # slot: generic mythic foil probability 1.0, but variant-specific key present with 0
        slot = TCGBoosterPackSlot("slot", {"Mythic Fable Foil": "0.0", "Mythic Foil": "1.0"})
        pack = TCGBoosterPack(tcg_set, slot.to_distributions())
        # EV should not include the card price
        self.assertAlmostEqual(pack.expected_value(), 0.0)

    def test_bulk_price_lookup(self):
        # ensure value_for_card falls back to bulk price correctly
        c = TCGCard("C", "Uncommon")
        s = TCGSet("S", [c], bulk_price={"Uncommon": 0.5})
        self.assertEqual(s.value_for_card(c), 0.5)

    def test_bulk_price_no_foil_match(self):
        # if no foil match, should fall back to non-foil category price
        c = TCGCard("C", "Uncommon", foil_type="normal", variant="Fable")
        c1 = TCGCard("C1", "Uncommon", foil_type="normal", variant="Fable", price=1.0)
        card_list = [c, c1]
        s = TCGSet("S", card_list, bulk_price={"Uncommon": 0.5})
        self.assertEqual(s.value_for_card(c), 0.5)
        self.assertEqual(s.value_for_card(c1), 1.0)

    def test_bulk_price_no_category_match(self):
        # if no category match, should return 0.0
        c = TCGCard("C", "Uncommon")
        s = TCGSet("S", [c], bulk_price={"Common": 0.1})
        self.assertEqual(s.value_for_card(c), 0.0)

    def test_expected_value_with_bulk(self):
        # card with price and category with bulk price; EV should include both
        c1 = TCGCard("C1", "Uncommon", price=1.0)
        c2 = TCGCard("C2", "Uncommon")  # no individual price
        s = TCGSet("S", [c1, c2], bulk_price={"Uncommon": 0.5})
        slot = TCGBoosterPackSlot("slot", {"Uncommon": "1.0"})
        pack = TCGBoosterPack(s, slot.to_distributions())
        # EV should be 1.0 for c1 + 0.5 for c2
        self.assertAlmostEqual(pack.expected_value(), 1.0 * 0.5 + 0.5 * 0.5)

    def test_expected_value_with_bulk_and_minimum_cards(self):
        # category with bulk price but fewer cards than total probability; should not error and should include bulk value for remaining probability
        c1 = TCGCard("C1", "Uncommon", price=1.0)
        c2 = TCGCard("C2", "Uncommon")  # no individual price
        c3 = TCGCard("C3", "Common", price=0.5)
        s = TCGSet("S", [c1, c2, c3], bulk_price={"Uncommon": 0.05}, cards_per_rarity={"Uncommon": 200, "Common": 100})
        slots = [TCGBoosterPackSlot("slot1", {"Uncommon": "0.7", "Common": "0.3"}),
                 TCGBoosterPackSlot("slot2", {"Uncommon": "0.3", "Common": "0.7"}),
                 TCGBoosterPackSlot("slot3", {"Common": "1.0"})]
        pack = TCGBoosterPack.from_slots(s, slots)
        # EV should be:
        # slot1: 0.7 * (1/200 * 1.0 + 199/200 * 0.05) + 0.3 * (1/100 * 0.5)
        # slot2: 0.3 * (1/200 * 1.0 + 199/200 * 0.05) + 0.7 * (1/100 * 0.5)
        # slot3: 1.0 * (1/100 * 0.5)
        expected_ev = (0.7 * (1/200 * 1.0 + 199/200 * 0.05) + 0.3 * (1/100 * 0.5)) + (0.3 * (1/200 * 1.0 + 199/200 * 0.05) + 0.7 * (1/100 * 0.5)) + (1.0 * (1/100 * 0.5))
        self.assertAlmostEqual(pack.expected_value(), expected_ev)

    def test_expected_value_with_zero_bulk_price(self):
        # category with zero bulk price should not contribute to EV
        c1 = TCGCard("C1", "Uncommon", price=1.0)
        c2 = TCGCard("C2", "Uncommon")  # no individual price
        s = TCGSet("S", [c1, c2], bulk_price={"Uncommon": 0.0})
        slot = TCGBoosterPackSlot("slot", {"Uncommon": "1.0"})
        pack = TCGBoosterPack(s, slot.to_distributions())
        # EV should be 1.0 for c1 + 0.0 for c2
        self.assertAlmostEqual(pack.expected_value(), 1.0 * 0.5 + 0.0 * 0.5)

    def test_expected_value_with_zero_bulk_price_and_no_individual_prices(self):
        # category with zero bulk price and no individual prices should have EV of 0
        c1 = TCGCard("C1", "Uncommon")  # no individual price
        c2 = TCGCard("C2", "Uncommon")  # no individual price
        s = TCGSet("S", [c1, c2], bulk_price={"Uncommon": 0.0})
        slot = TCGBoosterPackSlot("slot", {"Uncommon": "1.0"})
        pack = TCGBoosterPack(s, slot.to_distributions())
        # EV should be 0.0 for both cards
        self.assertAlmostEqual(pack.expected_value(), 0.0)

class TestBulkValueLookup(unittest.TestCase):
    def test_bulk_value_lookup(self):
        variant_foil = "Uncommon Fable Foil"
        rare = "Rare"
        uncommon = "Uncommon"
        rare_foil = "Rare Foil"
        uncommon_foil = "Uncommon Foil"
        bulk_prices = {
            variant_foil: 2.0,
            rare: 1.0,
            uncommon: 0.5,
            rare_foil: 2.5,
            uncommon_foil: 1.0
        }
        cardlist = [
            TCGCard("TestRFF1", "Rare", foil_type="normal", variant="Fable"),
            TCGCard("TestUF1", "Uncommon", foil_type="normal", variant="Fable"),
            TCGCard("TestUF2", "Uncommon", foil_type="normal", variant="Fable", price=1.5),
            TCGCard("TestR1", "Rare", price=5.0),
            TCGCard("TestU1", "Uncommon", price=0.8),
            TCGCard("TestRF1", "Rare", foil_type="normal", price=3.0),
            TCGCard("TestUF1", "Uncommon", foil_type="normal", price=1.0),
            TCGCard("TestUnknown", "Mythic", price=10.0),
            TCGCard("TestU2", "Uncommon", price=3.0),
            TCGCard("TestR2", "Rare"),
            TCGCard("TestRF2", "Rare", foil_type="normal")
        ]
        cards_per_rarity = {
            "Rare": 20,
            "Rare Foil": 20,
            "Rare Fable Foil": 10,
            "Rare Fable": 10,
            "Uncommon Fable Foil": 20,
            "Uncommon Fable": 20,
            "Uncommon Foil": 50,
            "Uncommon": 50,
        }
        test_set = TCGSet("TestSet", cardlist, bulk_price=bulk_prices, cards_per_rarity=cards_per_rarity)
        # Test each card against the expected bulk price lookup order
        self.assertEqual(test_set.value_for_card(cardlist[0]), 2.5) # should match "Rare Foil" after "Rare Fable Foil" for bulk price
        self.assertEqual(test_set.value_for_card(cardlist[1]), 2.0)
        self.assertEqual(test_set.value_for_card(cardlist[2]), 1.5)  # individual price should take precedence
        self.assertEqual(test_set.value_for_card(cardlist[3]), 5.0)
        self.assertEqual(test_set.value_for_card(cardlist[4]), 0.8)
        self.assertEqual(test_set.value_for_card(cardlist[5]), 3.0)
        self.assertEqual(test_set.value_for_card(cardlist[6]), 1.0)  # should match "Uncommon Foil" after "Uncommon Fable Foil" for bulk price
        self.assertEqual(test_set.value_for_card(cardlist[7]), 10.0)

        test_pack_slots =[
            TCGBoosterPackSlot("slot1", {"Rare Fable Foil": "0.1", "Rare Foil": "0.2", "Rare": "0.3", "Uncommon": "0.4"}),
            TCGBoosterPackSlot("slot2", {"Uncommon Foil": "0.2", "Uncommon": "0.7", "Common": "0.1"}),
            TCGBoosterPackSlot("slot3", {"Common": "1.0"}),
            TCGBoosterPackSlot("slot4", {"Rare Fable Foil": "0.05", "Rare Foil": "0.15", "Rare": "0.25", "Uncommon": "0.55"}),
        ]
        test_pack = TCGBoosterPack.from_slots(test_set, test_pack_slots)
        # EV should be:
        slot1_fable_foil_ev = 0.1 * (1/10 * 2.5 + 9/10 * 2.5)  # matches "Rare Foil" bulk price
        slot1_rare_foil_ev = 0.2 * (1/20 * 3.0 + 19/20 * 2.5)
        slot1_rare_ev = 0.3 * (1/20 * 5.0 + 19/20 * 1.0)
        slot1_uncommon_ev = 0.4 * (1/50 * 0.8 + 1/50 * 3.0 + 48/50 * 0.5)

        slot2_uncommon_foil_ev = 0.2 * (1/50 * 1.0 + 49/50 * 1.0)
        slot2_uncommon_ev = 0.7 * (1/50 * 0.8 + 1/50 * 3.0 + 48/50 * 0.5)
        slot2_common_ev = 0.1 * 0.0  # no common
        expected_ev = slot1_fable_foil_ev + slot1_rare_foil_ev + slot1_rare_ev + slot1_uncommon_ev + slot2_uncommon_foil_ev + slot2_uncommon_ev + slot2_common_ev
        
        slot3_ev = 1.0 * 0.0  # no common
        expected_ev += slot3_ev

        slot_4_ev = 0.05 * (1/10 * 2.5 + 9/10 * 2.5) + 0.15 * (1/20 * 3.0 + 19/20 * 2.5) + 0.25 * (1/20 * 5.0 + 19/20 * 1.0) + 0.55 * (1/50 * 0.8 + 1/50 * 3.0 + 48/50 * 0.5)
        expected_ev += slot_4_ev

        self.assertAlmostEqual(test_pack.expected_value(), expected_ev)

if __name__ == "__main__":
    unittest.main()#
