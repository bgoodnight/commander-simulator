# V19 Oracle snapshot verifier

`verify_cards.py` accepts a locally supplied Scryfall Oracle cards JSON array or JSONL snapshot (plain or gzip), matches the v1.13 list by exact card name, checks each Oracle ID, type line, color identity and Commander legality, and produces an auditable JSON report. Missing records, multiple exact matches, malformed data, cards outside U/R and unknown legality fail closed. The tool does not certify that an arbitrary input was actually downloaded from Scryfall: provenance and snapshot date must be independently established.

```
python simulator/v19_card_data/verify_cards.py oracle-cards.json --output validation-report.json
```

Exact Oracle names are preferred; if no exact match exists, the verifier accepts a unique named face of a double-faced card and fails on ambiguous face matches.

The source snapshot is not bundled in this repository; see v20 for a recorded verification run and snapshot provenance. The v18 unknown-card restrictions remain in effect; verified type metadata has not yet been integrated into `BudgetTable`. This utility is a preparatory step, not complete card coverage. Tests use synthetic examples only. See [Scryfall API documentation](https://scryfall.com/docs/api/bulk-data) for data format and provenance.
