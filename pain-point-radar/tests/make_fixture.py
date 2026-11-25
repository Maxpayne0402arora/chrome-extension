"""Generate SYNTHETIC feedback so the pipeline can be tested offline.
These are made-up sentences, not real reviews of any company."""
import csv, random, sys
from datetime import date, timedelta
random.seed(7)
NEG = [
 "Refund not received even after 15 days, customer care keeps saying wait",
 "Delivery delayed again, tracking shows out for delivery for 3 days",
 "Received a fake product, the seal was broken. Never ordering again",
 "App keeps crashing after the latest update, can't even open my cart",
 "Money deducted via UPI but order not placed, no response from support",
 "OTP never arrives so I can't log in to my account",
 "Return pickup cancelled three times without reason",
 "Too many notifications and promotional SMS every day, very annoying",
 "Prices are higher than other sites and coupons never apply at checkout",
 "Wrong shade delivered and exchange is not allowed, worst experience",
 "Chatbot is useless, there is no way to talk to a human agent",
 "Order got cancelled automatically after payment, refund still pending",
 "Uninstalling, switched to Purplle, their delivery is faster",
 "Search results are irrelevant and filters reset every time",
 "Expired product delivered, skin rash after using it",
]
POS = ["Great offers and fast delivery, love the app", "Genuine products and smooth checkout",
 "Easy returns, refund came in 2 days", "Nice interface, easy to find products",
 "Customer support resolved my issue quickly"]
REQ = ["Please add an option to schedule delivery", "Would be great if I could compare shades side by side",
 "Wish there was a wishlist price drop alert"]
w = csv.writer(sys.stdout); w.writerow(["date","rating","text","source"])
start = date(2026,1,1)
for i in range(900):
    d = start + timedelta(days=random.randint(0,320))
    late = d > date(2026,9,15)
    r = random.random()
    if r < 0.55:
        t = random.choice(NEG)
        if late and random.random() < 0.4: t = NEG[3]   # simulate a regression
        w.writerow([d, random.choice([1,1,2]), t, random.choice(["trustpilot","play_store_export"])])
    elif r < 0.9:
        w.writerow([d, random.choice([4,5,5]), random.choice(POS), "trustpilot"])
    else:
        w.writerow([d, 3, random.choice(REQ), "survey"])
