# Data Governance Specification

## Schema Contracts
Every ingested dataset is assigned an inferred column contract. Contracts specify logical data types, nullability, uniqueness, primary key designation, and sensitive data classification.

## Quality Gate Policies
- `block_on_failure`: Critical quality failures prevent dataset publication.
- `warn_only`: Warnings and failures are logged but publication proceeds.
- `manual_review`: Requires manual confirmation before dataset publishing.

## Sensitive Column Redaction
Columns detected or marked as sensitive (e.g. SSN, email, credit card) are automatically redacted before sending sample rows to AI engines.
