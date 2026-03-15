import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import pprint

def _parse_prob(x):
    """Accept numeric, string '0.18' or fractional '54/55' and return float."""
    if isinstance(x, (int, float)):
        return float(x)
    if not isinstance(x, str):
        raise TypeError("probability must be number or string")
    s = x.strip()
    if "/" in s:
        num, den = s.split("/", 1)
        return float(num) / float(den)
    return float(s)


# validate category labels like:
# "Common", "Common Fable", "Rare Borderless Nonland Foil", "Special Guest", etc.
_BASE_RARITY_PATTERN = re.compile(
    r"^(Common|Uncommon|Rare|Mythic|Special|Basic)(?:\s+.+?)?(?:\s+Foil)?$"
)


def _validate_category_label(label: str):
    if not isinstance(label, str) or not label.strip():
        raise ValueError("category label must be a non-empty string")
    if not _BASE_RARITY_PATTERN.match(label):
        raise ValueError(f"invalid category label '{label}' — "
                         "must start with one of: Common, Uncommon, Rare, Mythic, Special, Basic; "
                         "may include variant text and optional trailing 'Foil'")
class TCGCard:
    def __init__(self, name, rarity, price=None, foil_type=None, variant=None):
        """
        rarity        : 'Common', 'Uncommon', 'Rare', 'Mythic', 'Basic Land',
                        'Special'
        foil_type     : None | string (presence == foil)
        variant       : None | string describing a subgroup ('Special Guest',
                        'Fable', …)

        category label format: "[rarity][ ' ' + variant][ ' Foil' if foil]"
        """
        self.name = name
        self.rarity = rarity
        self.price = price
        self.foil_type = foil_type
        self.variant = variant

    @property
    def is_foil(self):
        return self.foil_type is not None

    @property
    def category(self):
        parts = [self.rarity]
        if self.variant:
            parts.append(self.variant)
        base = " ".join(parts)
        if self.is_foil:
            return f"{base} Foil"
        return base

    def parse_category(self):
        """Parse category into components; inverse of category property."""
        m = _BASE_RARITY_PATTERN.match(self.category)
        if not m:
            raise ValueError(f"invalid category '{self.category}' for card '{self.name}'")
        rarity = m.group(1)
        variant = None
        foil_type = None
        rest = self.category[len(rarity):].strip()
        if rest.endswith("Foil"):
            foil_type = "normal"
            rest = rest[:-len("Foil")].strip()
        if rest:
            variant = rest
        return rarity, variant, foil_type

    def __str__(self):
        price = f"${self.price:.2f}" if isinstance(self.price, (int, float)) else "N/A"
        parts = [f"name='{self.name}'", f"rarity='{self.rarity}'"]
        if self.variant:
            parts.append(f"variant='{self.variant}'")
        if self.foil_type:
            parts.append(f"foil={self.foil_type}")
        return f"TCGCard({', '.join(parts)}, price={price})"

    __repr__ = __str__


class TCGSet:
    def __init__(self, name, card_list, bulk_price, cards_per_rarity=None):
        self.name = name
        self.card_list : list[TCGCard] = card_list or []
        self.bulk_price : dict[str, float] = bulk_price or {}
        self.cards_per_rarity : dict[str, int] = cards_per_rarity or {}

    @classmethod
    def load_from_json(cls, json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        name = data.get("name", "Unnamed Set")
        cards_data = data.get("cards", [])
        card_list = []
        for cd in cards_data:
            card = TCGCard(cd.get("name"),
                           cd.get("rarity"),
                           price=cd.get("price"),
                           foil_type=cd.get("foil_type"),
                           variant=cd.get("variant"))
            card_list.append(card)
        bulk_price = data.get("bulk_price", {})
        cards_per_rarity = data.get("cards_per_rarity", {})
        return cls(name, card_list, bulk_price, cards_per_rarity)

    def get_candidates_for_category(self, category):
        '''Return list of candidate category keys to check for a card with the given category.'''
        rarity, variant, foil_type = TCGCard("", category).parse_category()
        candidates = []
        if foil_type and variant:
            candidates.append(f"{rarity} {variant} Foil")
        if variant:
            candidates.append(f"{rarity} {variant}")
        if foil_type:
            candidates.append(f"{rarity} Foil")
        candidates.append(rarity)
        return candidates

    def value_for_bulk(self, category):
        candidates = self.get_candidates_for_category(category)
        for key in candidates:
            if key in self.bulk_price:
                if float(self.bulk_price[key]) < 1e-12:
                    continue
                return float(self.bulk_price[key])
        return 0.0

    def value_for_card(self, card):
        if card.price is not None:
            return float(card.price)
        return self.value_for_bulk(card.category)

    def __str__(self):
        card_count = len(self.card_list)
        bp = ", ".join(f"{k}:{v:.2f}" for k, v in self.bulk_price.items())
        return f"TCGSet(name='{self.name}', cards={card_count}, bulk_price={{ {bp} }})"

    __repr__ = __str__


class TCGBoosterBox:
    def __init__(self,
                 name: str,
                 tcg_set: TCGSet,
                 cost: float,
                 number_of_boosters: int,
                 booster_pack: Optional['TCGBoosterPack'] = None):
        self.name = name
        self.cost = cost
        self.tcg_set = tcg_set
        self.number_of_boosters = number_of_boosters
        self.booster_pack = booster_pack  # may be attached later

    def expected_value(self) -> float:
        if self.booster_pack is None:
            raise ValueError("booster_pack not set on TCGBoosterBox")
        return self.booster_pack.expected_value() * self.number_of_boosters

    def price_per_booster(self) -> float:
        return self.cost / self.number_of_boosters if self.number_of_boosters else 0.0

    def __str__(self):
        set_name = self.tcg_set.name if self.tcg_set is not None else "None"
        cost = f"${self.cost:.2f}" if isinstance(self.cost, (int, float)) else str(self.cost)
        pb = f", pack_ev=${self.booster_pack.expected_value():.2f}" if self.booster_pack else ""
        return (f"TCGBoosterBox(name='{self.name}', set='{set_name}', cost={cost}, "
                f"boosters={self.number_of_boosters}{pb})")

    __repr__ = __str__


class TCGDistribution:
    """Slot distribution; see module docstring for normalisation rules."""
    def __init__(self, categories: Dict[str, float]):
        if not isinstance(categories, dict):
            raise TypeError("TCGDistribution requires a dict of {category:prob}")
        # validate category keys
        for k in categories.keys():
            _validate_category_label(k)
        self.categories = {k: _parse_prob(v) for k, v in categories.items()}
        total = sum(self.categories.values())
        if total <= 0:
            raise ValueError("distribution must contain positive probabilities")
        if total > 1.0 + 1e-12:
            raise ValueError(f"distribution sum {total} exceeds 1.0")
        if abs(total - 1.0) > 1e-12:
            # get categories with 0 probability 
            zero_chance_categories = [k for k, v in self.categories.items() if abs(v) <= 1e-12]
            self.skip_categories = set(zero_chance_categories)
            remaining = 1.0 - total
            self.categories["less_than_1"] = remaining
    def __str__(self):
        pairs = ", ".join(f"{k}:{v:.6f}" for k, v in self.categories.items())
        return f"TCGDistribution({{{pairs}}})"

    __repr__ = __str__


class TCGBoosterPackSlot:
    """Minimal JSON-driven slot wrapper."""
    def __init__(self, name, categories, quantity=1):
        self.name = name
        self.categories = categories
        self.quantity = int(quantity)

    def to_distributions(self):
        if isinstance(self.categories, dict):
            # validate keys here too (TCGDistribution will also validate)
            for k in self.categories.keys():
                _validate_category_label(k)
            dist = TCGDistribution(self.categories)
            return [dist] * self.quantity
        elif isinstance(self.categories, list):
            if not self.categories:
                raise ValueError("empty categories list")
            for c in self.categories:
                _validate_category_label(c)
            per = 1.0 / len(self.categories)
            dist = TCGDistribution({c: per for c in self.categories})
            return [dist] * self.quantity
        else:
            raise TypeError("categories must be dict or list")


class TCGBoosterPack:
    def __init__(self, tcg_set, slot_distributions):
        self.tcg_set : TCGSet = tcg_set
        self.slot_distributions : List[TCGDistribution] = slot_distributions
        self._cards_by_category : Dict[str, List[TCGCard]] = {}
        for c in tcg_set.card_list:
            self._cards_by_category.setdefault(c.category, []).append(c)
        self._warned_zero_probability = set()
        self._warned_zero_cards = set()

    @classmethod
    def from_slots(cls, tcg_set, slots):
        distributions = []
        for slot in slots:
            distributions.extend(slot.to_distributions())
        return cls(tcg_set, distributions)

    @classmethod
    def from_json(cls, tcg_set, json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        slots = []
        for sd in data.get("slots", []):
            slot = TCGBoosterPackSlot(sd.get("name"),
                                      sd.get("categories"),
                                      quantity=sd.get("quantity", 1))
            slots.extend(slot.to_distributions())
        return cls(tcg_set, slots)

    def expected_value_per_slot(self):
        """Compute EV per slot and return a list of slot EVs."""
        evs = []
        for dist in self.slot_distributions:
            for cat, prob in dist.categories.items():
                if cat == "less_than_1":
                    continue
                if prob <= 0.0:
                    pprint.pprint(f"Warning: category '{cat}' has zero probability in slot '{dist}'; skipping EV contribution.")
                    continue
                cards = self._cards_by_category.get(cat, [])
                total_cards_in_category = self.tcg_set.cards_per_rarity.get(cat, len(cards))
                if total_cards_in_category == 0:
                    pprint.pprint(f"Warning: category '{cat}' has zero total cards in slot '{dist}'; skipping EV contribution.")
                    continue
                assert total_cards_in_category >= len(cards), f"total_cards_in_category {total_cards_in_category} must be >= actual cards {len(cards)} for category '{cat}'"
                prob_per_card = prob / total_cards_in_category
                ev = 0.0
                for card in cards:
                    value = self.tcg_set.value_for_card(card)
                    ev += prob_per_card * value
                remaining_cards = total_cards_in_category - len(cards)
                if remaining_cards > 0:
                    bulk_value = self.tcg_set.value_for_bulk(cat)
                    if abs(bulk_value) < 1e-12:
                        pprint.pprint(f"Warning: category '{cat}' has {remaining_cards} cards without individual prices and no bulk price; skipping EV contribution for those cards.")
                    ev += (prob_per_card * remaining_cards) * bulk_value
                evs.append(ev)
        return evs

    def expected_value(self):
        """Compute EV per pack is sum of EV across slots."""
        return sum(self.expected_value_per_slot())

    def __str__(self):
        return f"TCGBoosterPack(set='{self.tcg_set.name}', slots={len(self.slot_distributions)})"

    __repr__ = __str__



# ---------------------------------------------------------------------------
# example / test code moved into main guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # simple fake set/box
    magic_cards = [
        TCGCard("Dragon2", "Rare", 3),
        TCGCard("Dragon4", "Rare"),
        TCGCard("Dragon3", "Rare"),
        TCGCard("Dragon1", "Rare"),
        TCGCard("Dragon7", "Rare"),
        TCGCard("Dragon6", "Common"),
        TCGCard("Dragon5", "Rare", 3),
        TCGCard("Dragon8", "Rare", 3),
        TCGCard("Dragon9", "Common"),
    ]
    bulk_price = {
        "Common": 0.02,
        "Uncommon": 0.15,
        "Rare": 0.8,
        "Mythic": 3.0,
    }
    fake_set = TCGSet("FakeSet", magic_cards, bulk_price)
    # make a trivial one‑slot pack
    fake_pack = TCGBoosterPack(fake_set, [TCGDistribution({"Rare": 1.0})])
    single_pack_box = TCGBoosterBox("FakeBox", fake_set, 20, 1, booster_pack=fake_pack)
    print(single_pack_box)
    print("price per booster:", single_pack_box.price_per_booster())
    print("box EV:", single_pack_box.expected_value())

    # lorwyn example
    lorwyn_cards = [
        TCGCard("LO1", "Common", 0.05),
        TCGCard("LO2", "Common", 0.04),
        TCGCard("LO3", "Uncommon", 0.20),
        TCGCard("LO4", "Uncommon", 0.18),
        TCGCard("LO5", "Rare", 1.50),
        TCGCard("LO6", "Mythic", 8.00),
        TCGCard("SG1", "Rare", 5.00, variant="Special Guest"),
        TCGCard("UF1", "Uncommon", 0.22, variant="Fable"),
        TCGCard("RF1", "Rare", 2.50, variant="Fable"),
        TCGCard("MFF1", "Mythic", 10.00, foil_type="normal", variant="Fable"),
        TCGCard("BN", "Basic Land", 0.01),
        TCGCard("BF", "Basic Land", 0.10, foil_type="normal"),
        TCGCard("BFa", "Basic Land", 0.02, variant="Full-Art"),
        TCGCard("BFb", "Basic Land", 0.15, foil_type="normal", variant="Full-Art"),
        TCGCard("BNL", "Rare", 3.00, variant="Borderless Nonland"),
        TCGCard("BS", "Rare", 4.00, variant="Borderless Shock"),
    ]

    lorwyn_bulk_price = {
        "Common": 0.04,
        "Uncommon": 0.19,
        "Rare": 1.50,
        "Mythic": 8.00,
        "Uncommon Fable": 0.22,
        "Rare Fable": 2.50,
        "Mythic Fable": 10.00,
        "Rare Borderless Nonland": 3.00,
        "Rare Borderless Shock": 4.00,
        "Basic": 0.01,
        "Common Foil": 0.04,
        "Uncommon Foil": 0.19,
        "Rare Foil": 1.50,
        "Mythic Foil": 8.00,
    }

    lorwyn_set = TCGSet("Lorwyn Eclipsed", lorwyn_cards, lorwyn_bulk_price,
                        cards_per_rarity={
                            "Common": 81,
                            "Uncommon": 110,
                            "Rare": 230,
                            "Rare Fable": 20,
                            "Mythic": 20,
                            "Basic Land": 5,
                        })

    json_path = Path("c:/Users/Joseph/Geeb Software/TCGBoxEV/lorwyn_eclipsed_booster.json")
    if json_path.exists():
        lorwyn_pack = TCGBoosterPack.from_json(lorwyn_set, str(json_path))
        box = TCGBoosterBox("Lorwyn Box", lorwyn_set, 100, 30, booster_pack=lorwyn_pack)
        print(lorwyn_pack)
        print("expected value per booster: $%.2f" % lorwyn_pack.expected_value())
        print("expected value per box (30 boosters): $%.2f" % box.expected_value())
    else:
        print("lorwyn_eclipsed_booster.json not found; create it per project spec.")
