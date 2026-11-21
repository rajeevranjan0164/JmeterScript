# VoltCart JMeter Learning Pack (Day 27 → 39)

Built from your BlazeMeter `voltCart-1.jmx` flows (**login → place order → cancel**) and mapped to **every JMeter example** in the class notes.

**Start here to understand everything:** **[LEARNING_GUIDE.md](LEARNING_GUIDE.md)**  
**Interview (local vs cloud monitoring):** [LEARNING_GUIDE.md §17](LEARNING_GUIDE.md#17-interview-guide--jmeter--prometheus--cloud)  
Day-by-day checklist: **[COVERAGE.md](COVERAGE.md)**

## Before you run

1. Start VoltCart on `http://127.0.0.1:8000`
2. JMeter → **File → Open** a `.jmx`
3. Demo users: `aarav@voltcart.demo` / `Demo@123`, `priya@voltcart.demo` / `Demo@123`

## Scripts (run in this order)

| # | File | Class topics |
|---|------|----------------|
| 01 | `01_Day29_Basics_Smoke.jmx` | Test Plan, Thread Group, HTTP, Header/Cookie/Cache, Tree + Summary, place-order asserts |
| 02 | `02_Day32_Users_ThinkTime.jmx` | Users + loops, Constant Timer (think time), Average / Throughput / Error% |
| 03 | `03_Day33_CSV_Parameterization.jmx` | CSV Data Set, `${email}` `${password}`, recycle/stop |
| 04 | `04_Day34_Correlation_Assertions.jmx` | JSON Extractor (match 0), order id correlation, If Controller, Debug Sampler |
| 05 | `05_Day36_Controllers_TokenLog.jmx` | Loop + Throughput Controllers 70/30, Constant Throughput Timer |
| 06 | `06_Day36_37_JSR223_Verify_Token_Prometheus.jmx` | **JSR223 Assertion** (Groovy response verify), token CSV, failures CSV, Prometheus demo |
| 07 | `07_Day34_Two_ThreadGroups.jmx` | Registration TG (disabled) + Place-order TG (enabled) |
| 08 | `08_Day35_Timers_Workload.jmx` | Constant Timer vs Constant Throughput Timer side by side |
| 09 | `09_Day36_Synchronizing_Timer_Spike.jmx` | Synchronizing Timer spike release |

## JSR223 response verification (class Day 36)

On place-order, scripts now include a **JSR223 Assertion (Groovy)** that:

- Parses the JSON body
- Checks `Order placed successfully`, `entities.order.status == Confirmed`, `trace.outcome == success`
- Checks `place_order` action `ok == true`, `cancellable`, order id `ORD-…`
- Fails the sample with a clear message if any rule fails (HTTP 200 alone is not enough)
- Sets `c_order_id`, token/cost/latency vars for later cancel + logs

Also:

- **JSR223 PostProcessor** → `data/token_log.csv`
- **JSR223 failures only** → `data/failures_only.csv`
- **Prometheus demo file** → `data/prometheus_push_demo.txt` (Day 37; live Pushgateway push is commented in the script)

## Place-order assertion stack

1. Response Assertion (text)  
2. JSON Path Assertion  
3. **JSR223 Assertion (Groovy)** ← what the notes covered for scripted verification  
4. Duration Assertion (180s learning SLA)  
5. Token / failure / prometheus post-processors  

## Data files

- `data/users.csv`
- `data/token_log.csv` (created on run)
- `data/failures_only.csv` (created on failure)
- `data/prometheus_push_demo.txt` (created on run)

## Regenerate

```text
python build_scripts.py
```
