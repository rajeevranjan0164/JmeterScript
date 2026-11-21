# VoltCart JMeter Learning Guide

This document explains **everything** that was built in the `Day27-Learning` folder: what each script teaches, what each JMeter element does, how the VoltCart API flow works, and how to read pass/fail.

Use this while you open each `.jmx` in JMeter and click through the tree on the left.

---

## 1. What this pack is for

You recorded a flow with the BlazeMeter Chrome extension:

1. Login  
2. Place order (AI chat)  
3. Cancel order (AI chat)  

That recording was a **raw** script (hard-coded email, product, order id).  
This pack turns it into **learning scripts** that match your class notes (Day 27 → 39): parameterization, correlation, assertions, timers, controllers, JSR223, and token logging.

**Folder:** `C:\AI LLM Testing\Jmeter\Day27-Learning\`

---

## 2. Before you run anything

1. Start VoltCart so the API is up: `http://127.0.0.1:8000`
2. Open Apache JMeter → **File → Open** → pick a `.jmx`
3. Demo users (already in CSV / User Defined Variables):
   - `aarav@voltcart.demo` / `Demo@123`
   - `priya@voltcart.demo` / `Demo@123`
4. Click the green **Start** button
5. Watch **View Results Tree** (detail) and **Summary Report** (numbers)

AI place/cancel can take **a long time** (often 30–120+ seconds on Ollama). That is normal for this shop.

---

## 3. The business flow (same in almost every script)

```text
Login  →  Product list  →  AI Place order  →  (optional) Verify orders
                                              →  AI Cancel order
                                              →  Verify order is Cancelled
```

| Step | HTTP | Why it matters |
|------|------|----------------|
| Login | `POST /api/auth/login` | Creates session cookie. Without this, later calls fail. |
| Products | `GET /api/products?limit=5` | Normal API. Also used to **correlate** a product name. |
| Place order | `POST /api/chat` | **AI path**. Slow. Creates `ORD-…` |
| Orders list | `GET /api/orders` | Proves order exists / status in DB |
| Cancel | `POST /api/chat` | **AI path**. Cancels that order id |
| Verify Cancelled | `GET /api/orders` | **Hard proof** status = `Cancelled` (not model wording) |

---

## 4. JMeter building blocks (learn these names)

Everything sits under a **Test Plan**.

### 4.1 Config elements (usually at Test Plan level)

| Element | What it does in our scripts |
|---------|-----------------------------|
| **User Defined Variables** | `host`, `port`, `p_email`, `p_password`. Change once; all requests use `${host}` etc. |
| **HTTP Request Defaults** | Default server = `127.0.0.1:8000` so each sampler need not repeat host. |
| **HTTP Header Manager** | Sends `Content-Type: application/json` and `Accept`. |
| **HTTP Cookie Manager** | Keeps login cookie (`voltcart_session`). **Clear each iteration** = next loop is a “fresh” user. |
| **HTTP Cache Manager** | Clears cache each iteration so you measure a first visit (class Day 33). |

### 4.2 Thread Group

Controls the **crowd**:

- **Number of Threads** = virtual users  
- **Ramp-up** = how long to start all users  
- **Loop Count** = how many times each user runs the flow  
- **Duration** (scheduler) = run for N seconds (used with infinite loop)

Example: 3 users, ramp 3s, loop 2 → about 6 full passes (if nothing fails early).

### 4.3 Samplers

**HTTP Request** = one call to the server.  
Body Data for login/chat is raw JSON.

### 4.4 Logic controllers

| Controller | Meaning |
|------------|---------|
| **Transaction Controller** | Groups steps (Login > Place > Cancel) as one row in Summary if “Generate parent sample” is on. |
| **Loop Controller** | Repeat children N times (e.g. login once style). |
| **If Controller** | Run children only if condition true (e.g. order id was extracted). |
| **Throughput Controller** | Split traffic (e.g. 70% place+cancel, 30% browse only). |

### 4.5 Timers

| Timer | Meaning |
|-------|---------|
| **Constant Timer** | Fixed think time (user pause). **Not** server time. Lowers throughput. |
| **Constant Throughput Timer** | Aims for a target rate (e.g. N requests/minute). JMeter inserts delay to approach it. |
| **Synchronizing Timer** | Users wait, then start together (spike). Not for every normal load test. |

### 4.6 Post-processors (after a response)

| Element | Meaning |
|---------|---------|
| **JSON Extractor** | Pull a field from JSON into a variable, e.g. `c_order_id` from `$.entities.order.id`. |
| **Regex Extractor** | Backup extract, e.g. `ORD-20261018-7A672` from body text. |
| **JSR223 PostProcessor** | Groovy script after the sample (log tokens, write CSV, Prometheus file). |

**Naming tip from class:**

- `p_` = parameterized (from CSV / UDV)  
- `c_` = correlated (from a previous response)

### 4.7 Assertions (pass/fail rules)

| Assertion | Meaning |
|-----------|---------|
| **Response Assertion** | Body/code must contain text (e.g. `Order placed successfully`). |
| **JSON Assertion** | JSONPath equals / exists (e.g. `$.entities.order.status` = `Confirmed`). |
| **Duration Assertion** | Fail if sample took longer than N ms (we use 180s as a learning SLA). |
| **JSR223 Assertion** | Groovy parses JSON and applies business rules; fails with a clear message. |

**Class rule (Day 35):** HTTP **200 is not business success**. An AI can return 200 and still ask “Which product?”.

### 4.8 Listeners

| Listener | Use |
|----------|-----|
| **View Results Tree** | See request/response while learning. Turn OFF for big load (uses memory). |
| **Summary Report** | Average, throughput, error %. Keep this. |
| **Debug Sampler** | Prints variables for this loop. Turn OFF for real load. |

---

## 5. Script-by-script guide (run in this order)

### `01_Day29_Basics_Smoke.jmx`

**Learn:** first full script — Test Plan, Thread Group, HTTP, Cookie, listeners.

**Users:** 1 user, 1 loop (smoke).

**What happens:** login → products → place order (full asserts) → verify orders → cancel → verify Cancelled.

**Look at:** green/red in View Results Tree; place-order time vs login time (AI is slow).

---

### `02_Day32_Users_ThinkTime.jmx`

**Learn:** more users + **Constant Timer** (think time).

**Idea from class:** more users should raise **throughput**. Think time lowers the rate and is **not** part of server response time.

**Look at:** Summary Report → Average, Throughput, Error %.

---

### `03_Day33_CSV_Parameterization.jmx`

**Learn:** **CSV Data Set Config**.

File: `data/users.csv`

```text
email,password,name
aarav@voltcart.demo,Demo@123,Aarav
priya@voltcart.demo,Demo@123,Priya
```

Login body uses `${email}` and `${password}` instead of hard-coded values.

**Class settings we use:**

- Recycle on EOF = false (for one-pass style) or true when reusing for load  
- Stop thread on EOF = true when you want one pass through the file  

**Look at:** Request body in Results Tree — email should match a CSV row.

---

### `04_Day34_Correlation_Assertions.jmx`

**Learn:** correlation + If Controller + Debug Sampler.

1. Product list → JSON Extractor → `c_product_name` (**match number 0** = random product each loop)  
2. Place order message uses `Place an order for 1 x ${c_product_name}`  
3. Extract `c_order_id` from place-order response  
4. Cancel uses `Cancel order ${c_order_id}`  
5. If order id is missing (`default`), cancel block can be skipped by If Controller  

**Look at:** Debug Sampler → variables `c_product_name`, `c_order_id` (must not stay `default`).

---

### `05_Day36_Controllers_TokenLog.jmx`

**Learn:** Loop Controller, Throughput Controller (~70% / 30%), Constant Throughput Timer, token logging.

**Idea:** not every user does the same mix. Workload model decides percentages.

---

### `06_Day36_37_JSR223_Verify_Token_Prometheus.jmx`

**Learn:** **JSR223** deeply.

On place-order, Groovy:

1. Parses JSON  
2. Checks business rules (success text, Confirmed, outcome, tool ok, ORD- id)  
3. Sets variables: tokens, cost, latency, order id  
4. Writes:
   - `data/token_log.csv`  
   - `data/failures_only.csv` (only failures)  
   - `data/prometheus_push_demo.txt` (Day 37 demo metrics file)

**This is the “scripted verification” from class**, not only checkbox assertions.

---

### `07_Day34_Two_ThreadGroups.jmx`

**Learn:** two Thread Groups in one plan.

- **Registration TG** → disabled (users already exist)  
- **Place-order TG** → enabled  

Right-click a Thread Group → Enable/Disable. Disabled groups do not run.

---

### `08_Day35_Timers_Workload.jmx`

**Learn:** difference between timers.

| Thread Group | Timer | Meaning |
|--------------|-------|---------|
| A | Constant Timer | Fixed pause (think time) |
| B | Constant Throughput Timer | Target rate |

Compare Summary Report for A vs B.

**Little’s Law** (planning math, not a JMeter button):

```text
Users ≈ Throughput × (response time + think time) / transactions per cycle
```

Keep units consistent (seconds with per-second, or minutes with per-minute).

---

### `09_Day36_Synchronizing_Timer_Spike.jmx`

**Learn:** Synchronizing Timer — users wait, then hit together (spike).

Use for spike tests, not every normal load run.

---

## 6. Place-order response — what we validate

From your real API response, a good place-order looks like:

- `message` contains **Order placed successfully**  
- `entities.order.id` like `ORD-20261018-8D0D7`  
- `entities.order.status` = **Confirmed**  
- `entities.order.cancellable` = true  
- `actions` includes tool **place_order** with `ok: true`  
- `trace.outcome` = **success**  
- `trace.input_tokens` / `output_tokens` / `latency_ms` / `estimated_cost_usd`

### Assertion stack (layered on purpose)

1. HTTP 200 (transport only)  
2. Response Assertion (important text)  
3. JSON Path Assertion (structured fields)  
4. **JSR223 Assertion** (full business logic in Groovy)  
5. Duration Assertion (180s learning limit)  
6. PostProcessors → CSV / Prometheus file  

If the bot asks a clarifying question, HTTP may still be 200 — assertions should **fail**. That is correct.

---

## 7. Cancel — what went wrong and what we fixed

### What you saw

```text
message was: reply
cancel_order action=missing
entities.order.status=missing
```

Meaning: the model returned filler text and **did not cancel**.

### Why place worked but cancel failed

VoltCart already had a **fallback** for place-order when a small model skips the tool.  
Cancel did **not** have that fallback at first (app fix was added in `agent_service.py`).

### What JMeter does now for cancel

1. Send: `Cancel order ${c_order_id}` (same style as BlazeMeter recording)  
2. Reuse the same `${c_session_id}` as place-order  
3. Soft-check the chat response (don’t fail only on English wording)  
4. **Hard check:** `GET /api/orders` → that order’s status must be **Cancelled**

So pass/fail for cancel is based on **database/API truth**, not whether the model said the word “cancelled”.

**Restart VoltCart** after the app fix so cancel fallback is active.

---

## 8. Important variables you will see

| Variable | Source | Used for |
|----------|--------|----------|
| `${host}` `${port}` | User Defined Variables | Server address |
| `${p_email}` `${p_password}` | UDV | Default login |
| `${email}` `${password}` | CSV columns | CSV login |
| `${c_session_id}` | JSR223 once per flow | Shared chat session |
| `${c_product_name}` | JSON Extractor from products | Place-order message |
| `${c_order_id}` | JSON/JSR223 from place-order | Cancel + verify |
| `${c_input_tokens}` etc. | Place-order / JSR223 | Token log / Prometheus demo |
| `${c_trace_id}` | Place-order trace | Investigation / LangSmith link later |

If a correlated value fails, extractors often set **`default`**. Seeing `default` in Debug Sampler means extract failed.

---

## 9. Files created when you run

| File | Created by | Purpose |
|------|------------|---------|
| `data/users.csv` | You/pack | Login data |
| `data/token_log.csv` | JSR223 | Tokens, cost, latency, order id per place-order |
| `data/failures_only.csv` | JSR223 | Only failed samples (serial + message) |
| `data/prometheus_push_demo.txt` | JSR223 | Day 37-style metrics text (Pushgateway optional) |

---

## 10. How to read results like class

In **Summary Report**:

| Column | Meaning |
|--------|---------|
| Average | Mean response time |
| Throughput | How many samples finished per unit time |
| Error % | Failed samples (assertions count as errors) |

In **View Results Tree**:

- Green = sample + assertions passed  
- Red = failed (open **Assertion Results** and **Response data**)  
- Compare login (~ms) vs place-order (many seconds) — AI path is the slow one  

---

## 11. Class day → script map (short)

| Days | Focus | Script |
|------|--------|--------|
| 27–28 | Performance words (theory) | Any Summary Report |
| 29 | First script + listeners | `01` |
| 32 | Users + think time | `02` |
| 33 | CSV + variables | `03` |
| 34 | Correlation + two TGs | `04`, `07` |
| 35 | Business asserts + timers | asserts in all + `08` |
| 36 | Controllers, sync, JSR223 | `05`, `06`, `09` |
| 37 | Token metrics file | `06` → `prometheus_push_demo.txt` |

Full table: see `COVERAGE.md`.

---

## 12. Recommended study path (one sitting)

1. Open `01` → run → understand Tree + Summary  
2. Open `03` → confirm CSV email in request  
3. Open `04` → Debug Sampler → see `c_product_name` / `c_order_id`  
4. Open `06` → read JSR223 Assertion script in GUI; open `token_log.csv` after run  
5. Open `08` → compare two timer styles  
6. Open `09` → understand spike release  
7. Skim `COVERAGE.md` against your Word notes  

---

## 13. How scripts are generated

File `build_scripts.py` rebuilds all `.jmx` files.

```text
cd "C:\AI LLM Testing\Jmeter\Day27-Learning"
python build_scripts.py
```

You normally only need this if you change the generator. Day-to-day learning = open the `.jmx` files in JMeter.

---

## 14. Common failures and what they mean

| Symptom | Likely meaning |
|---------|----------------|
| Login red | Shop not running, or wrong password |
| Place-order timeout | Ollama/model slow; 180s timeout may still be tight |
| Assert “Order placed successfully” fails | Model asked a question / order not created |
| `c_order_id` = `default` | Extract failed; check place-order response JSON |
| Cancel chat message = `reply` | Model skipped tool (restart app with cancel fallback) |
| Verify Cancelled red | Order still Confirmed in `/api/orders` |
| CSV file not found | Set full path in CSV Data Set Config to `data\users.csv` |

---

## 15. One-page memory card

```text
Record (BlazeMeter)  →  clean script (this pack)
Parameterize        →  CSV / UDV          (${email})
Correlate           →  JSON Extractor     (${c_order_id})
Assert business     →  Response + JSON + JSR223
Think time          →  Constant Timer
Target rate         →  Constant Throughput Timer
Mix flows           →  Throughput Controller
Spike               →  Synchronizing Timer
Log AI cost/time    →  JSR223 → token_log.csv
Prove cancel        →  GET /api/orders status=Cancelled
```

---

## 16. Related files in this folder

| File | Role |
|------|------|
| `LEARNING_GUIDE.md` | **This document** — understand everything |
| `README.md` | Short how-to-run |
| `COVERAGE.md` | Day-by-day checklist vs class notes |
| `01` … `09` `.jmx` | Import into JMeter and run |
| `build_scripts.py` | Regenerates the JMX files |
| `data\` | CSV + run outputs |
| **Section 17 below** | Interview answers (local vs cloud monitoring) |

---

## 17. Interview guide — JMeter + Prometheus + cloud

Use these as short spoken answers. Numbers below are **class examples**, not universal SLAs.

### 17.1 One-line architecture (say this first)

“In AI performance testing I simulate users with JMeter, extract tokens and latency from the API response with JSON extractors and JSR223, push numeric metrics to Pushgateway, Prometheus stores the time series, and Grafana shows dashboards and alerts. Traces for tool steps I check in LangSmith or a similar tool.”

```text
JMeter → JSON Extract + JSR223 → Pushgateway → Prometheus → Grafana
```

### 17.2 Local laptop vs cloud — what changes?

| Topic | Local laptop | Cloud |
|-------|--------------|--------|
| Where services run | All on one PC (`localhost`) | Separate VMs/pods/managed services |
| JMeter | Your machine | Load-generator VM / container / BlazeMeter / CI agent |
| Pushgateway | `localhost:9091` | Private host or managed path; HTTPS + auth |
| Prometheus | `localhost:9090` | Managed Prometheus (e.g. Azure Monitor managed Prometheus) or self-hosted |
| Grafana | `localhost:3000` | Managed Grafana / Grafana Cloud |
| Windows/node metrics | Windows exporter on laptop | Exporter/agent on the **server**, not on the tester laptop |
| Network | Loopback | Private VNet / firewall rules / TLS |
| Production traffic | You are not “production” | Real users; **JMeter is not required** for prod monitoring |

**Interview line:**  
“Locally I prove the pipeline end-to-end on one machine. In cloud I keep the same metric path, but split services, put them on a private network with HTTPS, and for production I prefer the application or a sidecar to emit metrics — JMeter is only for generating test load.”

### 17.3 Two cloud patterns (pick the right one)

**Pattern A — Load test (closest to class)**  
JMeter pushes custom AI metrics during the test:

```text
JMeter (cloud agents) → Pushgateway → Prometheus → Grafana
```

**Pattern B — Production monitoring**  
App or sidecar exposes/pushes metrics; no JMeter:

```text
Real users → App → metrics → Prometheus → Grafana
```

**Interview line:**  
“JMeter is a load generator. Prometheus and Grafana can monitor production without JMeter because real traffic creates the metrics.”

### 17.4 How do you know data reached Prometheus? (you just did this)

1. **Targets UP** only means scrape plumbing works (Pushgateway reachable).  
2. Check **Pushgateway** has `voltcart_ai_total_tokens` (or your metric names).  
3. Query Prometheus: `voltcart_ai_total_tokens`  
4. Optional: `push_time_seconds{job="voltcart_jmeter"}` is recent.

**Interview line:**  
“Targets green is necessary but not sufficient. I confirm the metric exists on Pushgateway, then query it in Prometheus. Empty query usually means nothing was pushed yet, not that Prometheus is down.”

### 17.5 What AI metrics do you push?

| Metric | Why |
|--------|-----|
| Input tokens | Context size / cost driver |
| Output tokens | Answer length / cost driver |
| Total tokens | Combined usage |
| Latency (ms) | User wait / SLA |
| Error flag/count | Failures over time |

Order ID / message text stay in **logs/traces**, not as Prom numbers.

**Interview line:**  
“Prometheus stores numeric time series. I push tokens, latency, and errors. For root cause I use order id or trace id in LangSmith or logs.”

### 17.6 Why Pushgateway at all?

“JMeter and short batch jobs are not always good scrape targets. Pushgateway is an intermediate store; Prometheus scrapes the gateway. I use it for test/job metrics, not as a replacement for scraping long-running services.”

### 17.7 How would you configure JMeter for cloud?

1. Put Pushgateway URL in **User Defined Variables** / env (no hard-coded `127.0.0.1`).  
2. Example: `https://pushgateway.mycompany.internal/metrics/job/voltcart_jmeter`  
3. Use HTTPS and credentials if exposed.  
4. Prefer private network between load generators and monitoring.  
5. Keep AI user counts lower than mock perf runs (token cost).

### 17.8 Example Azure-style answer

“I would run JMeter agents in a scale set or container app, push metrics to Pushgateway inside the VNet, scrape with Azure Monitor managed Prometheus or self-hosted Prometheus, and visualize in Azure Managed Grafana. Production metrics would come from the app or OpenTelemetry, not from JMeter.”

(Same idea on AWS/GCP with their managed Prometheus/Grafana equivalents.)

### 17.9 Related AI performance interview lines (class)

**Requirement:**  
“I ask for response time and throughput/user count together. ‘2 seconds’ alone is incomplete.”

**AI vs normal API:**  
“I separate normal APIs (login, product list) from AI calls (place order, cancel). AI is slower because tools run; I don’t blame the model from one number without a trace.”

**HTTP 200:**  
“HTTP 200 is transport success only. I assert business text or JSON fields, and for cancel I prove status Cancelled via GET /api/orders.”

**Correlation vs parameterization:**  
“Parameterization feeds different inputs (CSV users). Correlation takes a value from one response into the next (product name, order id).”

**Scale-down for AI:**  
“Perf team may use a mock model with more users. For AI I use the real model, fewer users, shorter run, because of token cost and staging size.”

**Outliers:**  
“If most calls use ~2k tokens and a few use ~8k, I investigate that request with timestamp, order id, and tool trace — not only the average.”

### 17.10 60-second closing answer (memorize)

“I build JMeter scripts for critical AI paths: login, place order, cancel. I parameterize users, correlate order ids, and assert business success, not only HTTP 200. I extract tokens and latency with JSON/JSR223, push them through Pushgateway into Prometheus, and chart them in Grafana. Locally I validate that pipeline on my laptop. In cloud I keep the same flow on managed or private services, and for production I monitor the application directly — JMeter stays for load tests only. When latency or cost spikes, I use traces to see whether the model, tools, or backend caused it.”

---

If you want, next we can walk **one script only** (for example `04` or `06`) line-by-line inside the JMeter tree.
