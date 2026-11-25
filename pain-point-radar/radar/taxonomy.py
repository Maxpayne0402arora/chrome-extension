"""Pain-point taxonomy: which *area of the business* a piece of feedback is about.

Each area maps to regex keyword patterns. A review can hit several areas.
CORE applies to every consumer company; sector packs add or refine areas.
Edit freely - this file is where your domain judgement goes, and a tighter
taxonomy beats a smarter model. Anything that matches no area is still mined
for "emerging themes" in the report, so you can see what the taxonomy misses.
"""

CORE = {
    "App performance & bugs": [
        r"\bcrash\w*", r"\bbug\w*", r"\bglitch\w*", r"\bhang(s|ing)?\b", r"\bslow\b", r"\blag\w*",
        r"not (working|loading|opening)", r"\bfreez\w*", r"\berror\b", r"\bstuck\b", r"blank screen",
        r"keeps? (closing|crashing)", r"\bloading\b", r"server (down|issue)", r"\bupdate\b.*(worse|broke|ruin)",
    ],
    "Login, OTP & account": [
        r"\botp\b", r"\blog ?in\b", r"\bsign ?(in|up)\b", r"\bpassword\b", r"\baccount (blocked|suspended|locked|deleted|hacked)",
        r"\bverif\w+", r"\bkyc\b", r"can'?t (log|sign)",
    ],
    "Customer support": [
        r"customer (care|service|support)", r"\bsupport\b", r"\bhelpline\b", r"\bchat ?bot\b", r"\bexecutive\b",
        r"no (response|reply)", r"\bnobody\b.*(help|respond)", r"\bticket\b", r"\bescalat\w*", r"\bcomplain\w*",
        r"(call|mail|email)(ed)? (them|multiple|many)", r"\bbot\b", r"human agent", r"\bunresponsive\b",
    ],
    "Payments & checkout": [
        r"\bpayment\w*", r"\bcheckout\b", r"\bupi\b", r"\bcard\b", r"\bcod\b", r"cash on delivery",
        r"money (deducted|debited|cut)", r"amount (deducted|debited)", r"\btransaction\w*", r"\bwallet\b",
        r"\bdeducted\b", r"\bdebited\b", r"\bcharged\b",
    ],
    "Refunds & returns": [
        r"\brefund\w*", r"\breturn\w*", r"\breplace\w*", r"\bexchange\b", r"money back", r"\breverse pickup\b",
    ],
    "Delivery & logistics": [
        r"\bdelivery\b", r"\b(not|never|wasn'?t|isn'?t) (been )?delivered\b", r"\bundelivered\b", r"\bdelivered late\b", r"\bcourier\b", r"\bshipping\b", r"\bshipment\b", r"\bdispatch\w*", r"\bdelay\w*",
        r"\blate\b", r"\btracking\b", r"\bpincode\b", r"\bnot received\b", r"\bnever (arrived|received|came)",
        r"\bdelivery (boy|guy|partner|agent)\b", r"\bfake (delivery|attempt)",
    ],
    "Order cancellation": [
        r"\bcancel\w*",
    ],
    "Pricing, fees & offers": [
        r"\bpric\w*", r"\bexpensive\b", r"\bcostly\b", r"\boverpriced\b", r"\bfee\b", r"\bcharges?\b",
        r"\bdiscount\w*", r"\boffer\w*", r"\bcoupon\w*", r"\bdeal\w*", r"\bcashback\b", r"\bhidden\b",
        r"\bsale\b", r"\bsurge\b", r"\bplatform fee\b", r"\bdelivery fee\b", r"\bsubscription\b",
    ],
    "Product quality & authenticity": [
        r"\bfake\b", r"\bduplicate\b", r"\bcounterfeit\b", r"\bgenuine\b", r"\bauthentic\w*", r"\boriginal\b",
        r"\bdamaged?\b", r"\bdefective\b", r"\bbroken\b", r"\bexpired\b", r"\bused product\b", r"\bwrong (item|product|size|colou?r)",
        r"\bquality\b", r"\bmissing (item|product)",
    ],
    "UX, search & navigation": [
        r"\bui\b", r"\bux\b", r"\binterface\b", r"\bconfusing\b", r"\bnavigat\w*", r"\bsearch\b", r"\bfilter\w*",
        r"\bdifficult to (find|use)\b", r"\bhard to (find|use)\b", r"\bclutter\w*", r"\bdesign\b", r"\buser friendly\b",
    ],
    "Ads, spam & notifications": [
        r"\bads?\b", r"\badvertis\w*", r"\bspam\w*", r"\bnotification\w*", r"\bpromotional\b", r"\btoo many (mails|sms|messages|calls)",
        r"\bpop ?ups?\b",
    ],
    "Trust, privacy & security": [
        r"\bscam\w*", r"\bfraud\w*", r"\bcheat\w*", r"\bprivacy\b", r"\bdata (leak|breach|sold)\b", r"\bhack\w*",
        r"\bsecurity\b", r"\bpermissions?\b", r"\btrust\b",
    ],
}

SECTOR_PACKS = {
    "ecommerce": {
        "Catalogue, stock & sizing": [
            r"\bout of stock\b", r"\bunavailable\b", r"\bsize\w*\b", r"\bfit(ting)?\b", r"\bsize chart\b",
            r"\bcatalog\w*", r"\bvariety\b", r"\bselection\b", r"\bnot as (shown|described|pictured)\b",
        ],
        "Seller & marketplace issues": [r"\bseller\w*", r"\bvendor\w*", r"\bthird[- ]party\b"],
    },
    "beauty": {
        "Shade, skin & product match": [
            r"\bshade\w*", r"\bskin\b", r"\ballerg\w*", r"\brash\w*", r"\bbreak ?out\w*", r"\btone\b", r"\btexture\b",
        ],
        "Freebies, samples & loyalty": [r"\bfree(bie)?s?\b", r"\bsample\w*", r"\bgift\w*", r"\bloyalty\b", r"\breward\w*", r"\bpoints\b", r"\bprive\b"],
        "Catalogue, stock & sizing": [r"\bout of stock\b", r"\bunavailable\b", r"\bnot as (shown|described|pictured)\b"],
    },
    "food_delivery": {
        "Food quality & order accuracy": [r"\bcold\b", r"\bstale\b", r"\btaste\w*", r"\bspill\w*", r"\bmissing\b", r"\bportion\w*", r"\bhygien\w*"],
        "Restaurant & partner behaviour": [r"\brestaurant\w*", r"\brider\w*", r"\brude\b", r"\btip\w*"],
    },
    "fintech": {
        "Transactions & settlement": [r"\bfailed\b", r"\bpending\b", r"\bsettle\w*", r"\bbank\b", r"\bkyc\b", r"\bcredit\b", r"\bloan\w*", r"\binterest\b"],
        "Rewards & cashback": [r"\breward\w*", r"\bcashback\b", r"\bscratch card\b", r"\bpoints\b"],
    },
    "tech": {
        "Feature removal & product changes": [r"\bremoved\b", r"\bdeprecat\w*", r"\bkilled\b", r"\bshut ?down\b", r"\bsunset\w*", r"\bgraveyard\b"],
        "Search & result quality": [r"\bsearch results?\b", r"\bseo\b", r"\bsponsored\b", r"\brelevan\w*", r"\bai overview\w*"],
        "Developer experience & docs": [r"\bapi\b", r"\bdocs?\b", r"\bdocumentation\b", r"\bsdk\b", r"\bconsole\b", r"\bquota\w*", r"\bbilling\b"],
    },
}

# Signals that tell you more than sentiment does.
CHURN = [
    r"\buninstall\w*", r"\bdelet(ed|ing) (the|this) app\b", r"\bnever (again|order|buy|use)\b", r"\bswitch(ed|ing)? to\b",
    r"\bmov(ed|ing) to\b", r"\bgoing back to\b", r"\blast time\b", r"\bnot (going to|gonna) (use|order|buy)\b",
    r"\bclos(e|ed|ing) (my )?account\b", r"\bbetter (alternative|option)s?\b",
]
FEATURE_REQUEST = [
    r"\bplease add\b", r"\bwish (there|it|you)\b", r"\bwould be (great|nice|better)\b", r"\bshould (have|add|allow)\b",
    r"\bneed (an?|the) option\b", r"\bfeature request\b", r"\bwhy (can'?t|don'?t) (i|you|we)\b", r"\bif only\b",
    r"\bit would help\b", r"\bkindly add\b", r"\bplease (bring|introduce|allow|make)\b",
]


def build(sector: str | None):
    tax = {k: list(v) for k, v in CORE.items()}
    for s in (sector or "").split(","):
        s = s.strip()
        if not s:
            continue
        if s not in SECTOR_PACKS:
            raise SystemExit(f"Unknown sector '{s}'. Choose from: {', '.join(SECTOR_PACKS)}")
        for k, v in SECTOR_PACKS[s].items():
            tax.setdefault(k, []).extend(v)
    return tax
