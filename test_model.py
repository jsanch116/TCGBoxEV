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

if __name__ == "__main__":
    unittest.main()
