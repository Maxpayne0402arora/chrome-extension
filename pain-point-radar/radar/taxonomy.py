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


# --------------------------------------------------------------------------- sub-themes for topic deep dives
# When you zoom into an area, feedback is split into these finer sub-themes.
# Phrases the users actually repeat are mined on top of this, so a topic with
# no entry here (or a custom topic) still gets a "most talked about" breakdown.
SUBTOPICS = {
    "Customer support": {
        "No / slow response": [r"no (response|reply)", r"not (responding|replying)", r"never (respond|repl)\w*",
                               r"still waiting", r"waiting (for|since) \w+ (days|weeks|months)", r"\bno one\b", r"\bnobody\b"],
        "Chatbot only, no human": [r"chat ?bot", r"\bbot\b", r"\bautomated\b", r"\bhuman\b", r"real person", r"talk to (an? )?(agent|person|someone)"],
        "Can't reach them (call/email)": [r"no (call|phone|contact) (option|number)", r"can'?t (reach|contact|call|connect)",
                                          r"\bhelpline\b", r"toll ?free", r"customer care number", r"\bemail(ed)?\b"],
        "Closed without resolution": [r"(ticket|complaint|issue|case) (was |got )?(closed|marked)", r"\bunresolved\b",
                                      r"not (been )?resolved", r"same (reply|response|answer)", r"copy ?paste", r"scripted"],
        "Repeated follow-ups": [r"again and again", r"\b(multiple|many|several|\d+) times\b", r"follow ?ups?", r"every (day|time)",
                                r"\bescalat\w*"],
        "Promised callback never came": [r"call ?back"],
        "Rude / unhelpful agents": [r"\brude\b", r"unprofessional", r"\buseless\b", r"misbehav\w*", r"hung up", r"\barrogant\b",
                                    r"don'?t (care|bother)"],
        "Language / understanding": [r"\bhindi\b", r"\benglish\b", r"\blanguage\b", r"don'?t understand", r"didn'?t understand"],
    },
    "Payments & checkout": {
        "Money debited, order failed": [r"(money|amount|payment) (got |was )?(deducted|debited|cut)", r"(deducted|debited) but",
                                        r"payment (failed|pending|stuck)", r"order (not|wasn'?t) (placed|confirmed)"],
        "UPI problems": [r"\bupi\b", r"\bgpay\b", r"google pay", r"\bphonepe\b", r"\bpaytm\b"],
        "Card / netbanking": [r"\bcards?\b", r"net ?banking", r"\bdeclined\b", r"\bbank\b"],
        "Cash on delivery": [r"\bcod\b", r"cash on delivery", r"pay on delivery"],
        "Coupons not applying": [r"coupons?", r"promo ?code", r"offer (not|wasn'?t|didn'?t) (appl|work)", r"\binvalid\b"],
        "Wallet / coins / gift cards": [r"\bwallet\b", r"\bcoins?\b", r"\bcredits?\b", r"gift ?cards?", r"\bpoints\b"],
        "EMI / pay later": [r"\bemi\b", r"pay ?later", r"\bbnpl\b"],
        "Hidden / extra fees": [r"(platform|handling|convenience|delivery|packaging|cod) (fee|charge)s?", r"\bhidden\b", r"extra (charge|fee)"],
    },
    "Refunds & returns": {
        "Refund delayed": [r"refund\w* (not|still|is|are)? ?(pending|delayed|not (received|credited|processed))",
                           r"(waiting|wait) for (my )?refund", r"no refund", r"refund.{0,30}\b(days|weeks|months)\b"],
        "Refund to wallet, not source": [r"refund\w* (to|in|into) (the )?(wallet|credits?|coins|gift card)", r"store credit"],
        "Return pickup failed": [r"pick ?up", r"reverse pick ?up", r"pickup (cancel|fail|not)\w*"],
        "Return rejected / not eligible": [r"non[- ]?returnable", r"not eligible", r"return (rejected|denied|declined)", r"no return policy"],
        "Damaged / wrong item to return": [r"\bdamaged\b", r"wrong (item|product|size|colou?r|shade)", r"\bdefective\b"],
        "Replacement / exchange issues": [r"\breplace\w*", r"\bexchange\w*"],
    },
    "Delivery & logistics": {
        "Late / delayed": [r"\bdelay\w*", r"\blate\b", r"not (yet )?(delivered|arrived|received)", r"\b\d+ (days|weeks)\b"],
        "Marked delivered, not received": [r"(marked|shows?|showing) (as )?delivered", r"delivered but (not|never)", r"never (received|got)"],
        "Fake delivery attempts": [r"fake (delivery )?attempt", r"(customer|i was) not available", r"attempt(ed)? (failed|delivery)"],
        "Tracking not updated": [r"\btracking\b", r"not (updat|moving)\w*", r"no update"],
        "Delivery agent behaviour": [r"delivery (boy|guy|partner|agent|person|executive)", r"\brude\b", r"asked (for )?(money|extra|otp)"],
        "Pincode / area not serviceable": [r"\bpincode\b", r"not serviceable", r"doesn'?t deliver", r"\bmy area\b"],
        "Packaging / damaged in transit": [r"\bpackag\w*", r"\bopen(ed)? box\b", r"\btampered\b", r"\bleak\w*", r"\bbroken\b"],
    },
    "App performance & bugs": {
        "Crashes": [r"\bcrash\w*", r"keeps? (closing|stopping)", r"force clos\w*"],
        "Slow / loading": [r"\bslow\b", r"\bload\w*", r"\blag\w*", r"\bhang\w*", r"\bstuck\b", r"blank screen"],
        "Broke after update": [r"\bupdat\w*", r"new version", r"latest version"],
        "Errors at checkout / payment": [r"(checkout|payment|cart).{0,20}(error|fail|not working)", r"something went wrong"],
        "Login loop / logout": [r"log(s|ged)? (me )?out", r"keeps? asking", r"\blogin\b.{0,20}(again|loop)"],
        "Storage / battery / heavy app": [r"\bstorage\b", r"\bbattery\b", r"\bheavy\b", r"\bsize\b.{0,10}\bmb\b"],
    },
    "Product quality & authenticity": {
        "Fake / counterfeit": [r"\bfake\b", r"\bduplicate\b", r"\bcounterfeit\b", r"\bfirst copy\b", r"not (genuine|original|authentic)"],
        "Expired / near expiry": [r"\bexpir\w*", r"\bmfg\b", r"manufactur\w* date", r"\bold stock\b"],
        "Damaged / defective": [r"\bdamaged\b", r"\bdefective\b", r"\bbroken\b", r"\bleak\w*"],
        "Wrong / missing item": [r"wrong (item|product|size|colou?r|shade)", r"missing (item|product)", r"\bempty box\b"],
        "Used / opened": [r"\bused\b", r"\bopened\b", r"\bseal\w*", r"\btampered\b"],
        "Not as described": [r"not as (shown|described|pictured)", r"different from (the )?(picture|image|photo)", r"\bmisleading\b"],
    },
    "Login, OTP & account": {
        "OTP not received": [r"\botp\b.{0,20}(not|never|late|didn)", r"(not|never) (getting|receiving|received) (the )?otp"],
        "Account blocked / suspended": [r"account (is |got |was )?(blocked|suspended|locked|disabled|deactivated)"],
        "Can't change number / email": [r"change (my )?(number|mobile|phone|email)", r"old number"],
        "Hacked / unauthorised orders": [r"\bhack\w*", r"unauthori[sz]ed", r"someone (else )?(ordered|used)"],
    },
    "Pricing, fees & offers": {
        "Price higher than elsewhere": [r"(costlier|expensive|higher) than", r"\bcheaper (on|at|elsewhere)\b", r"\boverpriced\b"],
        "Prices raised before sale": [r"(increase|hike|raise)\w* (the )?price", r"fake (discount|sale|offer)", r"\bmrp\b"],
        "Fees & charges": [r"(platform|handling|convenience|delivery|packaging) (fee|charge)s?", r"\bsurge\b"],
        "Coupons / cashback not working": [r"coupons?", r"\bcashback\b", r"promo ?code", r"offer (not|didn'?t)"],
        "Membership / subscription value": [r"\bmembership\b", r"\bsubscription\b", r"\bplus\b", r"\bprime\b", r"\bprive\b"],
    },
    "Order cancellation": {
        "Cancelled by seller/platform": [r"(seller|they|company|flipkart|nykaa|amazon) cancel\w*", r"cancel\w* (automatically|without)",
                                         r"auto[- ]?cancel\w*"],
        "Can't cancel my order": [r"(can'?t|cannot|unable to|not able to) cancel", r"no cancel\w* option"],
        "Cancellation fee": [r"cancel\w* (fee|charge)"],
    },
}
