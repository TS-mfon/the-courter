TREASURY_WALLET = "0x5905c9Dea6Ae52AA0947D8F7F218263889eDfC4E"

COURT_FEES_GEN = {
    "public": 2,
    "inner": 5,
    "appeal": 5,
    "shadow_council": 10,
}

CIVIL_DISPUTE_TYPES = {
    "land",
    "property",
    "rental",
    "inheritance",
    "contract",
    "civil_arbitration",
}

CRIMINAL_REJECTION_TERMS = {
    "criminal",
    "murder",
    "assault",
    "theft",
    "fraud charge",
    "imprisonment",
    "jail",
    "violent crime",
}

SUPPORTED_COUNTRIES = {
    "australia",
    "brazil",
    "india",
    "indonesia",
    "kenya",
    "nigeria",
}

SUPPORTED_EVIDENCE_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/plain",
}

PAYMENT_WARNING_RESPONSES = [
    "Payment verification failed for this transaction.",
    "This transaction hash has already been consumed.",
    "The treasury wallet did not receive the expected amount.",
    "The Bradbury receipt does not match the submitted sender wallet.",
    "The transaction is not usable for this dispute submission.",
]
