"""Generate SYNTHETIC feedback so the pipeline can be tested offline.
These are made-up sentences, not real reviews of any company.
Usage: python tests/make_fixture.py [seed] [rival_name] > fixture.csv"""
import csv, random, sys
from datetime import date, timedelta
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
rival = sys.argv[2] if len(sys.argv) > 2 else "Purplle"
random.seed(seed)
NEG = [
 "Refund not received even after {n} days, customer care keeps saying wait",
 "Delivery delayed again, tracking shows out for delivery for {n} days",
 "Received a fake product, the seal was broken. Never ordering again",
 "App keeps crashing after the latest update, can't even open my cart",
 "Money deducted via UPI but order not placed, no response from support",
 "OTP not received so I can't log in to my account",
 "Return pickup cancelled {n} times without reason",
 "Too many notifications and promotional SMS every day, very annoying",
 "Prices are higher than other sites and coupons never apply at checkout",
 "Wrong shade delivered and exchange is not allowed, worst experience",
 "Chatbot is useless, there is no way to talk to a human agent",
 "Customer support closed my ticket without resolution, same copy paste reply every time",
 "Called customer care {n} times, they promised a call back but nobody called",
 "Support agent was rude and hung up on me when I asked about my refund",
 "Raised a complaint with customer support, still waiting for a response after {n} days",
 "Order got cancelled automatically after payment, refund still pending",
 "Uninstalling, switched to {rival}, their delivery is faster",
 "Search results are irrelevant and filters reset every time",
 "Expired product delivered, skin rash after using it",
 "Payment failed but amount debited from my bank, customer care says wait 7 days",
]
POS = ["Great offers and fast delivery, love the app", "Genuine products and smooth checkout",
 "Easy returns, refund came in {n} days", "Nice interface, easy to find products",
 "Customer support resolved my issue quickly, very polite agent",
 "Support team called back within an hour and fixed my order",
 "Live chat agent was helpful and processed my refund the same day"]
REQ = ["Please add an option to schedule delivery", "Would be great if I could compare shades side by side",
 "Wish there was a wishlist price drop alert"]
w = csv.writer(sys.stdout); w.writerow(["date","rating","text","source"])
start = date(2026,1,1)
for i in range(1200):
    d = start + timedelta(days=random.randint(0,320))
    late = d > date(2026,9,15)
    r = random.random(); n = random.randint(2, 20)
    if r < 0.55:
        t = random.choice(NEG)
        if late and random.random() < 0.3: t = NEG[3]   # simulate a regression
        w.writerow([d, random.choice([1,1,2]), t.format(n=n, rival=rival), random.choice(["trustpilot","play_store_export"])])
    elif r < 0.9:
        w.writerow([d, random.choice([4,5,5]), random.choice(POS).format(n=n), "trustpilot"])
    else:
        w.writerow([d, 3, random.choice(REQ), "survey"])
