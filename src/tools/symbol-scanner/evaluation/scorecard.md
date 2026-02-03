# Symbol Scanner Evaluation Scorecard

## Summary

This scorecard will be populated after running the evaluation.

Run `make evaluate` to generate results.

## How to Evaluate

```bash
# Run programmatic evaluation
make evaluate

# Run LLM evaluation
make evaluate-llm
```

## Expected Metrics

### Symbol Extraction
- Function detection accuracy
- Class detection accuracy
- Method detection accuracy
- Line number accuracy
- Export detection accuracy

### Call Extraction
- Direct call detection
- Dynamic call detection
- Async call detection
- Caller/callee accuracy

### Import Extraction
- Static import detection
- From import symbol accuracy
- Star import handling
- Dynamic import detection

### Integration
- Path normalization
- Schema compliance
- Envelope structure
