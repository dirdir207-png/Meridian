"""Conservative merchant-sector rules; never item-level purchase evidence.

Aliases are anchored identities, not arbitrary substrings. Mixed retailers,
pharmacies and fuel/convenience stores deliberately remain reviewable.
Scores are rule priorities for the existing review gate, not calibrated probabilities.
"""
import re
import unicodedata

CATEGORIES = (
    "Groceries", "Dining", "Gas", "Transport", "Shopping", "Entertainment",
    "Travel", "Utilities", "Internet", "Phone", "Rent", "Subscriptions",
    "Health", "Fitness", "Insurance", "Transfers", "Personal Care", "Home",
    "Education", "Fees", "Pets", "Gifts", "Charity", "Taxes", "Income",
    "Refunds", "Reimbursements", "Savings", "Other",
)

# (stable ID, category, accepted identities). Longer aliases take precedence.
MERCHANT_RULES = (
    ("whole-foods", "Groceries", ("whole foods", "whole foods market")),
    ("trader-joes", "Groceries", ("trader joes",)),
    ("aldi", "Groceries", ("aldi",)),
    ("lidl", "Groceries", ("lidl",)),
    ("kroger", "Groceries", ("kroger",)),
    ("publix", "Groceries", ("publix",)),
    ("safeway", "Groceries", ("safeway",)),
    ("wegmans", "Groceries", ("wegmans",)),
    ("food-lion", "Groceries", ("food lion",)),
    ("harris-teeter", "Groceries", ("harris teeter",)),
    ("heb", "Groceries", ("h e b", "heb")),
    ("wendys", "Dining", ("wendys",)),
    ("mcdonalds", "Dining", ("mcdonalds",)),
    ("burger-king", "Dining", ("burger king",)),
    ("taco-bell", "Dining", ("taco bell",)),
    ("chipotle", "Dining", ("chipotle", "chipotle mexican grill")),
    ("chick-fil-a", "Dining", ("chick fil a",)),
    ("kfc", "Dining", ("kfc", "kentucky fried chicken")),
    ("popeyes", "Dining", ("popeyes",)),
    ("panera", "Dining", ("panera", "panera bread")),
    ("starbucks", "Dining", ("starbucks",)),
    ("dunkin", "Dining", ("dunkin", "dunkin donuts")),
    ("dominos", "Dining", ("dominos", "dominos pizza")),
    ("pizza-hut", "Dining", ("pizza hut",)),
    ("papa-johns", "Dining", ("papa johns",)),
    ("subway", "Dining", ("subway",)),
    ("uber-eats", "Dining", ("uber eats", "ubereats")),
    ("grubhub", "Dining", ("grubhub",)),
    ("netflix", "Entertainment", ("netflix", "netflix com")),
    ("spotify", "Entertainment", ("spotify", "spotify usa")),
    ("hulu", "Entertainment", ("hulu",)),
    ("disney-plus", "Entertainment", ("disney plus", "disneyplus")),
    ("steam", "Entertainment", ("steam", "steampowered com")),
    ("lyft", "Transport", ("lyft", "lyft ride")),
    ("amtrak", "Transport", ("amtrak",)),
    ("greyhound", "Transport", ("greyhound",)),
    ("xfinity", "Internet", ("xfinity", "comcast cable")),
    ("spectrum", "Internet", ("spectrum", "charter communications")),
    ("tmobile", "Phone", ("t mobile", "tmobile")),
    ("verizon-wireless", "Phone", ("verizon wireless", "vzwrlss")),
    ("mint-mobile", "Phone", ("mint mobile",)),
    ("cricket", "Phone", ("cricket wireless",)),
    ("keyme", "Home", ("keyme", "keyme locksmiths")),
    ("planet-fitness", "Fitness", ("planet fitness",)),
    ("anytime-fitness", "Fitness", ("anytime fitness",)),
    ("la-fitness", "Fitness", ("la fitness",)),
    ("chewy", "Pets", ("chewy", "chewy com")),
    ("petsmart", "Pets", ("petsmart",)),
    ("petco", "Pets", ("petco",)),
    ("coursera", "Education", ("coursera",)),
    ("udemy", "Education", ("udemy",)),
)


def normalize_merchant(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = value.replace("’", "").replace("'", "")
    # Strip only recognized leading payment wrappers, never words inside a name.
    value = re.sub(r"^(?:(?:sq|tst|pp|paypal)\s*\*\s*|(?:pos purchase|debit card purchase|card purchase|checkcard)\s+)", "", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def known_merchant_category(merchant: str | None, description: str = ""):
    """Return (category, stable rule ID, alias), or None for ambiguous identity."""
    identity = normalize_merchant(merchant or description)
    matches = []
    for rule_id, category, aliases in MERCHANT_RULES:
        for alias in aliases:
            if identity == alias or re.match(r"^" + re.escape(alias) + r" (?:store )?\d+\b", identity):
                matches.append((len(alias), category, "merchant:" + rule_id, alias))
    if not matches:
        return None
    _, category, rule_id, alias = max(matches)
    return category, rule_id, alias
