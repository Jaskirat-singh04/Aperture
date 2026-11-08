# Evals

Not implemented yet. This describes the planned format for the answer-quality eval set,
written before the eval runner exists so the data shape is settled first.

## Planned Format

One eval case per JSON object, one file per eval set (for example `evals/sets/baseline.jsonl`,
one JSON object per line):

```json
{
  "id": "finance-refund-policy-001",
  "question": "What is our refund policy for enterprise customers?",
  "as_user": "alice",
  "expected_answer_contains": ["30 days", "enterprise"],
  "expected_cited_document_ids": ["doc-acme-finance-policy"],
  "forbidden_cited_document_ids": ["doc-acme-alice-private"]
}
```

Fields:

- `id`: stable identifier for the case, used in eval run reports.
- `question`: the question asked.
- `as_user`: which seeded demo user asks it (alice, bob or carol, see
  `deploy/openfga/seed.py`), so permission filtering is part of the eval, not just answer
  quality.
- `expected_answer_contains`: substrings the answer should contain, a minimal proxy for
  correctness until a real Ragas faithfulness/relevancy setup is wired in.
- `expected_cited_document_ids`: document IDs the answer should cite.
- `forbidden_cited_document_ids`: document IDs the answer must never cite for this user,
  this is the eval-set counterpart to the permission-leak tests in `tests/security/`, a
  quality regression here is also a permission regression.

## Planned Runner

Once generation (`aperture.generation.service`) exists, a runner will load a `.jsonl`
eval set, ask each question through the real `/ask` flow as the given user, and score
answers with [Ragas](https://github.com/explodinggradients/ragas) metrics (faithfulness,
answer relevancy) plus the citation checks above. Not built yet, there is nothing to
score until generation exists.
