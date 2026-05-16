# The Courter

The Courter is a GenLayer-powered autonomous civil arbitration dApp. It combines
anonymous identities, GEN payment verification, evidence structuring, legal
retrieval, judge personas, GenLayer verdict generation, appeals, Shadow Council
governance, public transparency, Telegram updates, and OneSignal notifications.

The repository now contains:

- `apps/web`: Next.js route scaffold for every planned page.
- `apps/api`: FastAPI route and service scaffold for the court backend.
- `apps/telegram-bot`: Telegram companion command layer.
- `contracts`: GenLayer intelligent contract files for each court layer.
- `packages/shared`: shared constants, schemas, payment warnings, and judge registry helpers.
- `infra/sql`: PostgreSQL and pgvector schema.
- `laws`: starter country/category legal chunks.
- `judges`: judge persona profiles, including Justice Ratio.

Important: the bundled legal chunks are starter engineering data, not a complete
official legal corpus or legal advice.

## Local Checks

```bash
pytest -q
```

## Runtime Notes

Normal users are walletless and recover accounts by username plus recovery key.
Wallet connection is reserved for whitelisted Shadow Council voters.

Contracts must receive structured evidence, retrieved legal chunks,
contradiction reports, judge profiles, and case metadata only. They must not OCR
files, parse raw legal corpora, or return `undetermined`.
