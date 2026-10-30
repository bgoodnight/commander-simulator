# V19 Oracle snapshot verifier

`verify_cards.py` accepts a locally supplied Scryfall Oracle cards JSON array or JSONL snapshot (plain or gzip), matches the v1.13 list by exact card name, checks each Oracle ID, type line, color identity and Commander legality, and produces an auditable JSON report. Missing records, multiple exact matches, malformed data, cards outside U/R and unknown legality fail closed. The tool does not certify that an arbitrary input was actually downloaded from Scryfall: provenance and snapshot date must be independently established.

```
python simulator/v19_card_data/verify_cards.py oracle-cards.json --output validation-report.json
```

Exact-name matching will flag entries where a decklist uses one face of a double-faced card instead of the full Oracle name; those require explicit verified aliases before they can pass.

The source snapshot is not present in this repository and no actual deck card identities or color identities have been verified by this milestone. The v18 unknown-card restrictions remain in effect; verified type metadata has not yet been integrated into `BudgetTable`. This utility is a preparatory step, not complete card coverage. Tests use synthetic examples only. See [Scryfall API documentation](https://scryfall.com/docs/api/bulk-data) for data format and provenance.
