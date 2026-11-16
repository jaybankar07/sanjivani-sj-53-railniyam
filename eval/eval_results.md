| Metric | Config A (top_k=2, Tight) | Config B (top_k=4, Broad) | Winner |
|---|:---:|:---:|:---:|
| **Retrieval Hit Rate** | 93.3% | 93.3% | **Config B** |
| **Answer Accuracy** | 100.0% | 100.0% | **Tie (100%)** |
| **Citation Rate** | 100.0% | 100.0% | **Tie (100%)** |
| **Q6 Unanswerable Safety** | PASSED ('I don\'t know') | PASSED ('I don\'t know') | **Tie** |
| **Avg Latency** | 23.96 ms | 16.93 ms | **Config A** |
| **Overall Verdict** | Good for single rules | **Winner: Higher recall & evidence** | **Config B (top_k=4)** |
