# Datasets

## phishing_emails_sample.csv
600 emails (300 phishing, 300 legitimate), random sample (seed 42, text length 20–3000 chars)
from [zefang-liu/phishing-email-dataset](https://huggingface.co/datasets/zefang-liu/phishing-email-dataset)
(license: LGPL-3.0; the full set has 18,650 emails, 52 MB). Columns: `text`, `label` (`phishing` | `legitimate`).

## prompt_injections.csv
632 prompts (train + test, rows mentioning Trump removed) from [deepset/prompt-injections](https://huggingface.co/datasets/deepset/prompt-injections)
(license: Apache-2.0). Columns: `text`, `label` (`1` = injection, `0` = benign), `split` (`train` | `test`).
