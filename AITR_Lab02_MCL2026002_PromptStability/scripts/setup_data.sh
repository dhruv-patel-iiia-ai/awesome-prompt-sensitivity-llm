#!/usr/bin/env bash
# Download PubMedQA and GSM8K at pinned commits and create the official PQA-L split.
# Run from the repository root:  bash scripts/setup_data.sh
set -euo pipefail

PUBMEDQA_COMMIT=1cbae8e92f72f20c8d3747cbb3bf5bc53554d997   # pubmedqa/pubmedqa master, 2023-04-18
GSM8K_COMMIT=3101c7d5072418e28b9008a6636bde82a006892c      # openai/grade-school-math master, 2021-11-19

mkdir -p data/raw
if [ ! -d data/raw/pubmedqa ]; then
  git clone https://github.com/pubmedqa/pubmedqa.git data/raw/pubmedqa
fi
git -C data/raw/pubmedqa checkout -q "$PUBMEDQA_COMMIT"
echo "pubmedqa at $(git -C data/raw/pubmedqa rev-parse HEAD)"

# Official split: 500 test + 10 CV folds, random.seed(0) inside the script. Run it unchanged.
(cd data/raw/pubmedqa/preprocess && python split_dataset.py pqal)

mkdir -p data/raw/gsm8k
curl -sSL -o data/raw/gsm8k/test.jsonl \
  "https://raw.githubusercontent.com/openai/grade-school-math/${GSM8K_COMMIT}/grade_school_math/data/test.jsonl"
echo "gsm8k test.jsonl: $(wc -l < data/raw/gsm8k/test.jsonl) lines"
