"""Synthetic personal notes and their labeled retrieval queries."""

MESSY_CANDIDATES = {
    "airport_pickup": """wed / flight pickup. old msg said arrivals upstairs but that's for dropping ppl off
Mira just texted: roadworks, use short stay P2, meet by purple lift on level 1. don't wait on curb
https://example.com/airport/map (map is old, see Mira's voice note)
buy oat milk on way home??? also return blue umbrella to T.""",
    "airport_dropoff": """Airport fri for Jan. Departures upstairs, lane B if open, 10 min max. P2 is for ppl who need to leave the car.
Check terminal on ticket first this time. Old booking was terminal 2; not sure these are even the same airline.""",
    "train_replacement": """sat train thread / screenshot 4. 08.42 on ticket but engineering works this wk only
replacement bus from NORTH car park (not station forecourt). Be there 8.20. bike might need booking separately.
https://example.com/travel/notice-17 — doubled times in app, ignore the 09.12 if going before lunch
bring printout for gran, she never checks messages.""",
    "train_pickup": """pick Sam up sunday train. meet at the forecourt by taxi rank. North carpark too far if they have the big case.
Arrival maybe 08:42 or 08:47, ask them when they board. Cafe card is in car door.""",
    "parcel_label": """chair return / case 438. first email said print label; newer reply says box it and show QR from the SECOND email at parcel shop. staff prints sticker.
use corner shop on Lime St, locker doesn't scan this code. Deadline Thurs (see ticket, maybe midnight?). put screws in bag.
https://example.com/orders/438 — other chair stays here, wrong size was the grey one.""",
    "parcel_collection": """pick up Mum's lamp, Lime St shop same as chair place. Show the collection barcode + ID. This is collection, no box needed. Order 483 not 438.
If it's after work check the shop hours [see screenshot].""",
    "water_isolation": """sink drips again—kitchen this time (bathroom fixed?). little silver valve on cold feed behind cleaning bottles, slot across pipe = closed. Landlord showed me. Only that tap stops.
don't use big stopcock by front door unless whole flat needs water off; upstairs neighbour was confused last time.
ref IMG_2117 / buy bin liners / call back after 6""",
    "water_main": """move-in notes 2024. MAIN water stopcock under hall cupboard by front door. Shuts supply to whole flat. The other little valves are for individual fittings.
key to meter box with spare fuses. Photo https://example.com/flat/meter . radiator note on other page.""",
    "cake_substitution": """Lena bday cake v3 (NOT freezer one). recipe calls for milk but last time used same amount of unswtnd oat milk and batter was fine. Keep butter unless Lena wants dairy-free too — this was only about running out of milk.
Bake 175 ish, check centre. link https://example.com/recipe/p42 . send her the playlist. 6 eggs? that's the double batch.""",
    "cake_allergy": """school cake sale allergy note. kid allergic to oats so no oat drink even if carton says dairy free. Check ingredient label and ask organiser before signing up. This is for school sale, not Lena's party.
bring list of ingrediants, little cards in drawer.""",
    "class_credit": """pottery tues cancelled by studio (kiln busted). email says class credit automatically added, use that credit to rebook another Tuesday, don't pay the checkout again. If it asks for card stop + email Jo.
bumper note: I missed Monday myself last month, different policy. https://example.com/studio/account""",
    "class_missed": """missed Monday pottery because bus. Studio only transfers credit if I cancel 24h before class. Mine was too late so new booking costs normal price. Tues kiln thing was the studio cancelling, read that email separately.
pick up my glazed bowl if open past 5.""",
    "plant_watering": """fern looking sad again. checked soil and its still wet under top layer. skip watering till pot feels lighter, empty the outside pot where water collects. Move it away from heater. Brown tips aren't always thirst.
thing in blue pot is pothos; fern is white pot. send updated pic to Dev""",
    "plant_dry_soil": """pothos (blue pot) drooped after holiday. Soil dry a finger down and pot very light. Water until it drains and tip excess out of tray. Use own note for fern; theirs looked similar but soil was soaked.
leave spare key under doormat? no check with Dev""",
    "invoice_refund": """bike shop charged deposit then final bill incl full amount. reply from Bea: duplicate deposit refund to original card, will show separately from final receipt. don't dispute final payment, bike collected fine.
invoice 218 / refund ref R-82 / check after weekend. receipt pdf https://example.com/receipts/218""",
    "invoice_credit": """bike shop store credit from returning unused mudguard. Voucher code is emailed, not cash back to card. Separate from deposit thing on invoice 218. use by end of summer? ask Bea.
size 45 mm not 35. Find receipt in old messages.""",
}

MESSY_QUERIES = (
    ("Where should I leave the car and meet Mira when I collect her from the airport?", "airport_pickup"),
    ("My Saturday rail ticket still shows a train. Where do I actually board the replacement service?", "train_replacement"),
    ("I need to send back the grey chair and have no printer. What should I take to the shop?", "parcel_label"),
    ("Can I stop the cold supply to the dripping kitchen tap and leave the rest of the flat running?", "water_isolation"),
    ("What did I use in place of milk the last time I baked Lena's cake?", "cake_substitution"),
    ("The studio called off my Tuesday session. How can I book a replacement without paying twice?", "class_credit"),
    ("The white pot is drooping and the soil underneath is damp. Should I give it more water?", "plant_watering"),
    ("Where should I look for the money back from the duplicate bike deposit?", "invoice_refund"),
)
