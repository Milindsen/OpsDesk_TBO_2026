import re
from typing import Any, Dict, List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

INTENTS = [
    "refund",
    "cancellation",
    "amendment",
    "voucher",
    "inventory_sync",
    "payment",
    "special_request",
    "supplier_issue",
    "other",
]

RULES: Dict[str, List[str]] = {
    "refund": ["refund", "money back", "reimburs", "return money"],
    "cancellation": ["cancel", "cancellation", "void booking", "drop reservation"],
    "amendment": ["amend", "change", "modify", "reschedul", "date change"],
    "voucher": ["voucher", "coupon", "credit note", "promo code"],
    "inventory_sync": ["inventory", "sync", "availability", "not showing", "rate mismatch"],
    "payment": ["payment", "invoice", "billing", "charge", "debit", "credit card failure"],
    "special_request": ["special request", "wheelchair", "meal", "early check", "late check", "honeymoon"],
    "supplier_issue": ["supplier", "hotel issue", "airline issue", "property", "hotel denied checkin"],
    "other": ["inquiry", "general question", "support", "help"],
}

TRAINING_DATA: List[Tuple[str, str]] = [
    # refund
    ("I need a refund for my cancelled booking", "refund"),
    ("Please refund the amount to my account", "refund"),
    ("Customer is asking for reimbursement of hotel charges", "refund"),
    ("Can you process a full refund for booking TBO12345?", "refund"),
    ("Refund status check for transaction failed earlier", "refund"),
    ("Where is my money back for the cancelled flight?", "refund"),
    ("Money not returned after cancellation deadline", "refund"),
    ("Requesting urgent reimbursement for duplicate charge", "refund"),
    ("Initiate refund workflow for passenger", "refund"),
    ("Refund approval required from finance team", "refund"),

    # cancellation
    ("Please cancel booking TBO99999 immediately", "cancellation"),
    ("Guest wants to cancel hotel stay due to personal emergency", "cancellation"),
    ("Cancellation of flight ticket requested", "cancellation"),
    ("Need cancellation confirmation for the reservation", "cancellation"),
    ("Cancel this booking before last cancellation date", "cancellation"),
    ("Customer cannot travel, please void the reservation", "cancellation"),
    ("Immediate cancellation requested by client", "cancellation"),
    ("Can we cancel without penalty fees?", "cancellation"),
    ("Booking cancellation request for peak season", "cancellation"),
    ("Drop the reservation in supplier portal", "cancellation"),

    # amendment
    ("I need to change travel dates for booking", "amendment"),
    ("Please modify guest names on the voucher", "amendment"),
    ("Reschedule departure from tomorrow to next week", "amendment"),
    ("Date amendment requested by travel agency", "amendment"),
    ("Amend room category from standard to deluxe", "amendment"),
    ("Correct misspelled passenger name on flight ticket", "amendment"),
    ("Change lead passenger details on hotel booking", "amendment"),
    ("Flight reschedule assistance needed", "amendment"),
    ("Modify checkout date by one extra night", "amendment"),
    ("Amendment of booking dates needed urgently", "amendment"),

    # voucher
    ("Where can I download the hotel confirmation voucher?", "voucher"),
    ("Please send the booking voucher to customer email", "voucher"),
    ("Supplier voucher not generated yet", "voucher"),
    ("Reissue updated travel voucher with agent logo", "voucher"),
    ("Apply credit note or discount coupon to booking", "voucher"),
    ("Voucher bar code is unreadable", "voucher"),
    ("Client needs hotel check-in voucher copy", "voucher"),
    ("Travel voucher missing confirmation code", "voucher"),
    ("Issue credit voucher for cancelled package", "voucher"),
    ("Send airline e-voucher to passenger", "voucher"),

    # inventory_sync
    ("Room rates are not showing in the agency portal", "inventory_sync"),
    ("Inventory sync failure between hotel and system", "inventory_sync"),
    ("Room is showing available on supplier site but sold out on TBO", "inventory_sync"),
    ("API rate mismatch and inventory out of sync", "inventory_sync"),
    ("Inventory update not reflecting on booking engine", "inventory_sync"),
    ("Property availability calendar failed to sync", "inventory_sync"),
    ("Cannot see room allotment in portal", "inventory_sync"),
    ("Real-time availability sync error on flight search", "inventory_sync"),
    ("Hotel inventory cache is stale", "inventory_sync"),
    ("Sync error code 503 on hotel supplier api", "inventory_sync"),

    # payment
    ("Payment deducted from credit card but booking not confirmed", "payment"),
    ("Invoice required for corporate agency billing", "payment"),
    ("Payment gateway error during checkout", "payment"),
    ("Debit card charged twice for single reservation", "payment"),
    ("Send updated billing statement and tax invoice", "payment"),
    ("Credit limit exceeded on agency account", "payment"),
    ("Payment status is pending in accounting portal", "payment"),
    ("Customer bank transaction failed but amount debited", "payment"),
    ("Need GST invoice for hotel booking", "payment"),
    ("Chargeback inquiry for booking transaction", "payment"),

    # special_request
    ("Customer needs wheelchair assistance at airport arrival", "special_request"),
    ("Requesting early check-in at 10 AM for elderly couple", "special_request"),
    ("Vegetarian Jain meal request for all flight sectors", "special_request"),
    ("Late checkout required until 4 PM due to night flight", "special_request"),
    ("High floor quiet room with king bed requested", "special_request"),
    ("Honeymoon cake and floral setup in hotel room", "special_request"),
    ("Baby cot needed for 1-year-old infant in room", "special_request"),
    ("Connecting rooms requested for family travelling together", "special_request"),
    ("Airport shuttle pickup timing confirmation", "special_request"),
    ("Special meal dietary request diabetic meal", "special_request"),

    # supplier_issue
    ("Hotel reception denied checkin claiming booking not received", "supplier_issue"),
    ("Supplier cancelled confirmed hotel room without notice", "supplier_issue"),
    ("Property is closed for maintenance upon guest arrival", "supplier_issue"),
    ("Airline cancelled flight without alternative arrangement", "supplier_issue"),
    ("Supplier representative not answering emergency hotline", "supplier_issue"),
    ("Hotel overbooked and walked guest to substandard property", "supplier_issue"),
    ("Supplier failed to honor agreed contractual room type", "supplier_issue"),
    ("Direct supplier escalation required for stranded passengers", "supplier_issue"),
    ("Local transfer operator did not show up at airport", "supplier_issue"),
    ("Property maintenance issue air conditioning broken in room", "supplier_issue"),

    # other
    ("General inquiry regarding destination visa requirements", "other"),
    ("Operating hours of support desk over weekend", "other"),
    ("Feedback on overall website booking experience", "other"),
    ("Need contact info for local representative office", "other"),
    ("General question regarding baggage allowance policy", "other"),
    ("Agency user training inquiry for portal features", "other"),
    ("Inquiry about corporate partnership terms", "other"),
    ("Miscellaneous query from prospective client", "other"),
]


class IntentClassifier:
    _instance: Optional["IntentClassifier"] = None

    def __init__(self) -> None:
        self.pipeline: Pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
                ("clf", LogisticRegression(max_iter=1000, random_state=42)),
            ]
        )
        self._train()

    def _train(self) -> None:
        texts = [x[0] for x in TRAINING_DATA]
        labels = [x[1] for x in TRAINING_DATA]
        self.pipeline.fit(texts, labels)

    def _rule_match(self, text: str) -> List[Dict[str, Any]]:
        text_lower = text.lower()
        scored: List[Tuple[str, float]] = []
        for intent, kws in RULES.items():
            matches = sum(1 for kw in kws if re.search(r"\b" + re.escape(kw) + r"\b", text_lower))
            if matches > 0:
                conf = min(0.95, 0.45 + (matches * 0.2))
                scored.append((intent, conf))
        scored.sort(key=lambda x: x[1], reverse=True)
        if scored:
            return [{"intent": i, "confidence": round(c, 4)} for i, c in scored[:3]]
        return [{"intent": "other", "confidence": 0.5}]

    def suggest(self, text: str, description: str = "") -> List[Dict[str, Any]]:
        combined = f"{text} {description}".strip()
        if not combined:
            return [{"intent": "other", "confidence": 0.5}]

        probs = self.pipeline.predict_proba([combined])[0]
        classes = self.pipeline.classes_

        class_probs = list(zip(classes, probs))
        class_probs.sort(key=lambda x: x[1], reverse=True)

        top_class, top_conf = class_probs[0]

        # If confidence is low, fall back to rule-based matching
        if top_conf < 0.4:
            rule_results = self._rule_match(combined)
            if rule_results and rule_results[0]["confidence"] > top_conf:
                return rule_results

        return [
            {"intent": str(c), "confidence": round(float(p), 4)}
            for c, p in class_probs[:3]
        ]


_classifier_instance: Optional[IntentClassifier] = None


def get_intent_classifier() -> IntentClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntentClassifier()
    return _classifier_instance
