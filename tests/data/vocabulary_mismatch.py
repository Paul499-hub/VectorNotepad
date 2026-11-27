"""Everyday notes with queries that describe the same idea in different words."""

VOCABULARY_CANDIDATES = {
    "airport_pickup": "Mira pickup, short-stay P2. Meet by the purple lift on level 1. Departures curb is for drop-offs only.",
    "parcel_return": "Grey chair return, case 438. Show the QR from the second email at the Lime Street parcel shop. Staff prints the label. Lockers cannot scan it.",
    "mold_prevention": "Bedroom condensation again. Ventilate each morning and pull furniture away from the exterior wall. Run the dehumidifier after laundry dries indoors.",
    "plant_overwatering": "Fern roots sitting in pooled water. Empty the outer planter and postpone irrigation until the potting mix dries. White ceramic container.",
    "bike_brakes": "Rear brake rub after wheel removal. Loosen the caliper bolts, squeeze the lever to center the pads, then retighten.",
    "payment_refund": "Invoice 218: duplicate deposit reimbursed to the original card. Refund reference R-82. Expect a separate credit on the statement.",
    "library_renewal": "Library loans can be renewed online unless another borrower has placed a reservation. Sign in with the barcode on the membership card.",
    "shoe_blisters": "New boots rubbed both heels on the hill walk. Wear thicker socks and put moleskin on hot spots before heading out again.",
    "recipe_scaling": "For six portions instead of four, multiply ingredient quantities by 1.5. Keep the oven temperature the same. Check doneness a little later if the dish is deeper.",
    "meeting_timezone": "The invitation says 15:00 London time. Vilnius is two hours ahead for this date, so add it locally at 17:00.",
    "painter_invoice": "The decorator's estimate excludes materials. Keep the paint receipts and get approval before buying extra supplies.",
    "train_parking": "Leave the car in the north lot by the railway station if waiting for someone. The taxi lane is for quick pickups.",
    "parcel_pickup": "Bring identification to collect the package from the shop. The clerk checks the collection barcode against the order name.",
    "plant_dry_soil": "The pothos has droopy leaves and the soil is dry below the surface. Give it a thorough drink and let the excess drain away.",
    "store_voucher": "The returned mudguard earns a voucher toward a future purchase. The emailed code expires at the end of summer.",
    "library_hold": "If a book is checked out, place a hold in the catalogue. The library will email when the copy is ready to collect.",
}

VOCABULARY_QUERIES = (
    ("Where should I leave my car while I wait for her plane to land?", "airport_pickup"),
    ("How can I send back the seat I ordered if I don't own a printer?", "parcel_return"),
    ("How do I prevent damp patches behind my wardrobe when I hang wet clothes inside?", "mold_prevention"),
    ("My droopy houseplant feels soggy underneath. Should I give it a drink?", "plant_overwatering"),
    ("How do I stop the back disc from scraping since I refitted the tyre?", "bike_brakes"),
    ("Where will I see the money the shop gave me back after it charged me twice?", "payment_refund"),
    ("Can I extend my book's due date if somebody else is waiting for it?", "library_renewal"),
    ("How do I avoid getting blisters in my hiking shoes?", "shoe_blisters"),
    ("How should I adjust the recipe if it feeds 4 people and 6 are coming for dinner?", "recipe_scaling"),
    ("When should I join the afternoon call from Lithuania if the organizer is in Britain?", "meeting_timezone"),
)
