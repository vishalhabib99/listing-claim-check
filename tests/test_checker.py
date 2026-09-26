import pytest

from listing_claim_check import check

PHONE = {"category": "smartphone", "brand": "Apple", "model": "iPhone 13 Pro", "condition": "Used",
         "storage": "128GB", "carrier": "Verizon", "battery_health": 86, "color": "Sierra Blue",
         "includes": ["cable", "original box"]}


def statuses(result):
    return {(c["attribute"], c["claimed"]): c["status"] for c in result["claims"]}


def test_clean_listing_publishes():
    r = check(PHONE, "Apple iPhone 13 Pro 128GB Sierra Blue (Verizon)", "Battery health 86%. Includes cable and original box.")
    assert r["decision"] == "PUBLISH", r


@pytest.mark.parametrize("text,attr", [
    ("Like new condition", "condition"),
    ("Factory unlocked, works on any carrier", "carrier"),
    ("256GB of storage", "storage"),
    ("Battery health 95%", "battery_health"),
    ("iPhone 14 Pro", "model"),
    ("Comes with charger", "includes"),
    ("100% authentic", "authenticity"),
    ("Still under AppleCare+", "warranty"),
    ("Samsung flagship", "brand"),
])
def test_unbacked_high_harm_claim_goes_to_review(text, attr):
    r = check(PHONE, "Phone for sale", text)
    assert r["decision"] == "REVIEW"
    assert any(c["attribute"] == attr and c["status"] != "SUPPORTED" for c in r["claims"]), r["claims"]


@pytest.mark.parametrize("text", ["Charger not included.", "No charger.", "Does not come with a charger.", "Charger sold separately."])
def test_negated_mentions_are_not_claims(text):
    assert check(PHONE, "iPhone 13 Pro", text)["decision"] == "PUBLISH"


def test_negation_stops_at_a_conjunction():
    r = check(PHONE, "iPhone 13 Pro", "No scratches and comes with the charger.")
    assert statuses(r)[("includes", "charger")] == "CONTRADICTED"


def test_unbacked_number_is_flagged_with_context():
    r = check(PHONE, "iPhone 13 Pro", "Bought it in 2023, kept in a case.")
    flags = [c for c in r["claims"] if c["attribute"] == "number"]
    assert r["decision"] == "REVIEW" and flags[0]["claimed"] == "2023" and "2023" in flags[0]["text"]


def test_numbers_backed_by_specifics_pass():
    assert check(PHONE, "iPhone 13 Pro 128GB", "86% battery health.")["decision"] == "PUBLISH"


def test_genuine_leather_is_material_not_authenticity():
    bag = {"category": "handbag", "brand": "Coach", "material": "Leather", "color": "Black", "condition": "Used"}
    r = check(bag, "Coach bag", "Made from genuine black leather.")
    assert r["decision"] == "PUBLISH", r["claims"]


def test_faux_leather_contradicts_leather():
    bag = {"category": "handbag", "brand": "Coach", "material": "Leather"}
    assert check(bag, "Coach bag", "Soft vegan leather.")["decision"] == "REVIEW"


def test_like_new_is_fine_for_refurbished_but_not_used():
    assert check({**PHONE, "condition": "Refurbished"}, "iPhone 13 Pro", "Like-new condition.")["decision"] == "PUBLISH"
    assert check(PHONE, "iPhone 13 Pro", "Like-new condition.")["decision"] == "REVIEW"


def test_empty_listing_goes_to_review():
    assert check(PHONE, "", "")["decision"] == "REVIEW"


def test_every_flag_has_a_reason():
    r = check(PHONE, "iPhone 14 256GB unlocked", "Mint. Includes charger and earbuds. 2 day shipping.")
    assert all(c["reason"] for c in r["claims"])


def test_ram_is_not_storage():
    assert ("storage", "8gb") not in statuses(check(PHONE, "iPhone 13 Pro", "8GB RAM"))
