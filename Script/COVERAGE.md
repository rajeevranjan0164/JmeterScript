# Class notes → script coverage (Day 27–39)

Your notes cover theory + JMeter. This pack maps **every JMeter example** to a runnable file.

| Day | Topic in notes | Script / where |
|-----|----------------|----------------|
| 27–28 | Response time, throughput, concurrency, RPM (theory) | `README.md` + Summary Report on any script |
| 29 | Test Plan, Thread Group, cURL/HTTP, Header Manager, Cookie Manager, View Results Tree, Summary Report | `01_Day29_Basics_Smoke.jmx` |
| 30 | Azure/model setup (not JMeter) | App `config.py` — not a JMX |
| 31 | Scenarios / critical vs busy TPS / scale-down AI users | Comments in `05`, `07`; keep AI users low |
| 32 | Users raise rate; Constant Timer = think time; Average, Throughput, Error% | `02_Day32_Users_ThinkTime.jmx` |
| 33 | BlazeMeter record, UDV host/port, CSV Data Set, recycle/stop, Cache+Cookie clear each iteration | `03_Day33_CSV_Parameterization.jmx` (+ managers in all plans) |
| 34 | Two Thread Groups; JSON Extractor; match 0 random; Debug Sampler; Response Assertion; correlate order id → cancel | `04_…`, `07_Day34_Two_ThreadGroups.jmx` |
| 35 | HTTP 200 ≠ business success; Response Assertion; Constant Timer vs Constant Throughput Timer; workload %; Little’s Law | Assertions in all place-order scripts; `08_Day35_Timers_Workload.jmx`; Little’s Law in this table |
| 36 | Synchronizing Timer; Loop / If / Throughput Controllers; JSON extract tokens; **BeanShell/JSR223** log; failures-only log | `05_…`, `06_…`, `09_…` |
| 36 | **JSR223 response verification** (Groovy parse JSON, fail sample) | `06_Day36_37_JSR223_Verify_Token_Prometheus.jmx` (+ under every place-order) |
| 37 | JSR223 → Pushgateway → Prometheus metrics (tokens, latency, errors) | `06_…` writes `data/prometheus_push_demo.txt` (live push commented) |
| 38 | Grafana dashboards/alerts | Use file from Day 37 / real Pushgateway — ops steps in notes, not JMX GUI |
| 39 | LangSmith traces | App tracing — use `c_trace_id` from token log |

## Little’s Law (Day 35 — planning, not a JMX element)

`Users ≈ Throughput × (response time + think time) / transactions per cycle`

Keep units consistent (per second with seconds, or per minute with minutes).

## Assertion stack on place-order (what you asked to expand)

1. Response Assertion (text): Order placed successfully, Confirmed, outcome, place_order, cancellable  
2. JSON Path Assertion: `$.entities.order.status`, `$.trace.outcome`, id/total/product exist  
3. **JSR223 Assertion (Groovy)**: parse JSON, validate business rules, set `c_*` vars, fail with clear message  
4. JSR223 PostProcessor: token CSV + failures-only CSV + Prometheus demo file  
5. Duration Assertion: 180s learning SLA (Ollama can be slow)

## Output files

| File | Purpose |
|------|---------|
| `data/users.csv` | Parameterization |
| `data/token_log.csv` | Tokens, cost, latency, order id, trace id |
| `data/failures_only.csv` | Failed samples only |
| `data/prometheus_push_demo.txt` | Day 37 metric exposition demo |

## Run order (recommended)

`01 → 02 → 03 → 04 → 07 → 08 → 05 → 09 → 06`
