# -*- coding: utf-8 -*-
"""Generate VoltCart Day27-39 JMeter learning scripts (class notes coverage)."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent
DATA = OUT / "data"
CSV_USERS = str(DATA / "users.csv").replace("\\", "/")
FAIL_LOG = str(DATA / "failures_only.csv").replace("\\", "/")
TOKEN_LOG = str(DATA / "token_log.csv").replace("\\", "/")
PROM_FILE = str(DATA / "prometheus_push_demo.txt").replace("\\", "/")


def esc(text: str) -> str:
    return escape(text, {"\"": "&quot;"})


def raw_body(json_text: str) -> str:
    return f"""            <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
              <collectionProp name="Arguments.arguments">
                <elementProp name="" elementType="HTTPArgument">
                  <boolProp name="HTTPArgument.always_encode">false</boolProp>
                  <stringProp name="Argument.value">{esc(json_text)}</stringProp>
                  <stringProp name="Argument.metadata">=</stringProp>
                </elementProp>
              </collectionProp>
            </elementProp>
            <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>"""


def query_args(pairs: list[tuple[str, str]]) -> str:
    items = []
    for name, value in pairs:
        items.append(
            f"""                <elementProp name="{esc(name)}" elementType="HTTPArgument">
                  <boolProp name="HTTPArgument.always_encode">false</boolProp>
                  <stringProp name="Argument.name">{esc(name)}</stringProp>
                  <stringProp name="Argument.value">{esc(value)}</stringProp>
                  <stringProp name="Argument.metadata">=</stringProp>
                </elementProp>"""
        )
    return f"""            <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
              <collectionProp name="Arguments.arguments">
{chr(10).join(items)}
              </collectionProp>
            </elementProp>"""


def empty_args() -> str:
    return """            <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
              <collectionProp name="Arguments.arguments"/>
            </elementProp>"""


def http(
    name: str,
    method: str,
    path: str,
    body: str | None = None,
    query: list[tuple[str, str]] | None = None,
    children: str = "",
    response_timeout_ms: str = "60000",
) -> str:
    if body is not None:
        args = raw_body(body)
    elif query:
        args = query_args(query)
    else:
        args = empty_args()
    return f"""          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{esc(name)}" enabled="true">
{args}
            <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
            <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
            <stringProp name="HTTPSampler.protocol">http</stringProp>
            <stringProp name="HTTPSampler.domain">${{host}}</stringProp>
            <stringProp name="HTTPSampler.port">${{port}}</stringProp>
            <stringProp name="HTTPSampler.path">{esc(path)}</stringProp>
            <stringProp name="HTTPSampler.method">{method}</stringProp>
            <stringProp name="HTTPSampler.connect_timeout">10000</stringProp>
            <stringProp name="HTTPSampler.response_timeout">{esc(response_timeout_ms)}</stringProp>
          </HTTPSamplerProxy>
          <hashTree>
{children}
          </hashTree>"""


def json_extractor(ref: str, path: str, match: str = "1", default: str = "default") -> str:
    return f"""            <JSONPostProcessor guiclass="JSONPostProcessorGui" testclass="JSONPostProcessor" testname="JSON Extractor - {esc(ref)}" enabled="true">
              <stringProp name="JSONPostProcessor.referenceNames">{esc(ref)}</stringProp>
              <stringProp name="JSONPostProcessor.jsonPathExprs">{esc(path)}</stringProp>
              <stringProp name="JSONPostProcessor.match_numbers">{esc(match)}</stringProp>
              <stringProp name="JSONPostProcessor.defaultValues">{esc(default)}</stringProp>
            </JSONPostProcessor>
            <hashTree/>"""


def regex_extractor(ref: str, regex: str, template: str = "$1$", match: str = "1", default: str = "default") -> str:
    return f"""            <RegexExtractor guiclass="RegexExtractorGui" testclass="RegexExtractor" testname="Regex Extractor - {esc(ref)}" enabled="true">
              <stringProp name="RegexExtractor.refname">{esc(ref)}</stringProp>
              <stringProp name="RegexExtractor.regex">{esc(regex)}</stringProp>
              <stringProp name="RegexExtractor.template">{esc(template)}</stringProp>
              <stringProp name="RegexExtractor.default">{esc(default)}</stringProp>
              <stringProp name="RegexExtractor.match_number">{esc(match)}</stringProp>
              <boolProp name="RegexExtractor.default_empty_value">false</boolProp>
              <stringProp name="Sample.scope">all</stringProp>
            </RegexExtractor>
            <hashTree/>"""


def response_assertion(name: str, contains: str, test_field: str = "Assertion.response_data") -> str:
    return f"""            <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="{esc(name)}" enabled="true">
              <collectionProp name="Asserion.test_strings">
                <stringProp name="{abs(hash(contains)) % 10_000_000}">{esc(contains)}</stringProp>
              </collectionProp>
              <stringProp name="Assertion.custom_message"></stringProp>
              <stringProp name="Assertion.test_field">{test_field}</stringProp>
              <boolProp name="Assertion.assume_success">false</boolProp>
              <intProp name="Assertion.test_type">2</intProp>
            </ResponseAssertion>
            <hashTree/>"""


def response_assertion_multi(name: str, contains_list: list[str], test_field: str = "Assertion.response_data") -> str:
    """AND of several Contains checks (test_type 2 = contains, multiple strings = all must match)."""
    items = "\n".join(
        f'                <stringProp name="{abs(hash(s)) % 10_000_000}">{esc(s)}</stringProp>'
        for s in contains_list
    )
    return f"""            <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="{esc(name)}" enabled="true">
              <collectionProp name="Asserion.test_strings">
{items}
              </collectionProp>
              <stringProp name="Assertion.custom_message"></stringProp>
              <stringProp name="Assertion.test_field">{test_field}</stringProp>
              <boolProp name="Assertion.assume_success">false</boolProp>
              <intProp name="Assertion.test_type">2</intProp>
            </ResponseAssertion>
            <hashTree/>"""


def response_code_assertion(name: str = "Assert HTTP 200") -> str:
    return f"""            <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="{esc(name)}" enabled="true">
              <collectionProp name="Asserion.test_strings">
                <stringProp name="49586">200</stringProp>
              </collectionProp>
              <stringProp name="Assertion.custom_message"></stringProp>
              <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
              <boolProp name="Assertion.assume_success">false</boolProp>
              <intProp name="Assertion.test_type">8</intProp>
            </ResponseAssertion>
            <hashTree/>"""


def json_path_assertion(name: str, json_path: str, expected: str, validation: str = "EQUALS") -> str:
    """JSON Assertion — validates one JSONPath value from the real VoltCart chat response."""
    return f"""            <JSONPathAssertion guiclass="JSONPathAssertionGui" testclass="JSONPathAssertion" testname="{esc(name)}" enabled="true">
              <stringProp name="JSON_PATH">{esc(json_path)}</stringProp>
              <stringProp name="EXPECTED_VALUE">{esc(expected)}</stringProp>
              <boolProp name="JSONVALIDATION">true</boolProp>
              <boolProp name="EXPECT_NULL">false</boolProp>
              <boolProp name="INVERT">false</boolProp>
              <boolProp name="ISREGEX">false</boolProp>
              <stringProp name="TEST_VALIDATION">{esc(validation)}</stringProp>
            </JSONPathAssertion>
            <hashTree/>"""


def json_path_exists(name: str, json_path: str) -> str:
    return f"""            <JSONPathAssertion guiclass="JSONPathAssertionGui" testclass="JSONPathAssertion" testname="{esc(name)}" enabled="true">
              <stringProp name="JSON_PATH">{esc(json_path)}</stringProp>
              <stringProp name="EXPECTED_VALUE"></stringProp>
              <boolProp name="JSONVALIDATION">false</boolProp>
              <boolProp name="EXPECT_NULL">false</boolProp>
              <boolProp name="INVERT">false</boolProp>
              <boolProp name="ISREGEX">false</boolProp>
            </JSONPathAssertion>
            <hashTree/>"""


def jsr223_assert_place_order() -> str:
    """Day 36-style response verification with JSR223/Groovy (not only Response Assertion)."""
    script = r"""
import groovy.json.JsonSlurper

def body = prev.getResponseDataAsString()
def fails = []
if (!body) {
  AssertionResult.setFailure(true)
  AssertionResult.setFailureMessage('Empty place-order response body')
  return
}

def json
try {
  json = new JsonSlurper().parseText(body)
} catch (Exception e) {
  AssertionResult.setFailure(true)
  AssertionResult.setFailureMessage('Response is not JSON: ' + e.message)
  return
}

// Day 35: HTTP 200 is not business success
if (!(json.message?.toString()?.contains('Order placed successfully'))) {
  fails << 'message must contain \"Order placed successfully\" (got: ' + json.message + ')'
}
if (json.trace?.clarification == true) {
  fails << 'trace.clarification must be false (agent asked a question instead of ordering)'
}
if (json.trace?.outcome?.toString() != 'success') {
  fails << 'trace.outcome must be success (got: ' + json.trace?.outcome + ')'
}

def order = json.entities?.order
if (order == null) {
  fails << 'entities.order missing'
} else {
  if (!(order.id?.toString()?.startsWith('ORD-'))) fails << 'entities.order.id missing/invalid'
  if (order.status?.toString() != 'Confirmed') fails << 'entities.order.status must be Confirmed'
  if (order.cancellable != true) fails << 'entities.order.cancellable must be true'
  if (order.total == null) fails << 'entities.order.total missing'
  vars.put('c_order_id', order.id?.toString() ?: 'default')
  vars.put('c_order_status', order.status?.toString() ?: 'default')
  vars.put('c_order_total', order.total?.toString() ?: '0')
}

def product = json.entities?.product
if (product?.name == null) {
  fails << 'entities.product.name missing'
} else {
  vars.put('c_product_ordered', product.name.toString())
}

def place = json.actions?.find { it.tool == 'place_order' }
if (place == null) {
  fails << 'actions must include tool place_order'
} else if (place.result?.ok != true) {
  fails << 'place_order.result.ok must be true'
}

// Token / cost / latency capture (Day 36)
def t = json.trace ?: [:]
vars.put('c_input_tokens', (t.input_tokens ?: 0).toString())
vars.put('c_output_tokens', (t.output_tokens ?: 0).toString())
vars.put('c_total_tokens', (t.total_tokens ?: 0).toString())
vars.put('c_cost', (t.estimated_cost_usd ?: 0).toString())
vars.put('c_latency_ms', (t.latency_ms ?: 0).toString())
vars.put('c_outcome', (t.outcome ?: 'default').toString())
vars.put('c_trace_id', (t.id ?: '').toString())

// Outlier hint (class: most ~2k tokens, some 8k) — warn in log only
try {
  def totalTok = (t.total_tokens ?: 0) as int
  if (totalTok >= 8000) {
    log.warn('TOKEN OUTLIER total_tokens=' + totalTok + ' order=' + vars.get('c_order_id'))
  }
} catch (ignored) {}

if (fails) {
  AssertionResult.setFailure(true)
  AssertionResult.setFailureMessage('JSR223 place-order failed:\\n - ' + fails.join('\\n - '))
} else {
  AssertionResult.setFailure(false)
}
""".strip()
    return f"""            <JSR223Assertion guiclass="TestBeanGUI" testclass="JSR223Assertion" testname="JSR223 Assert place-order (Groovy)" enabled="true">
              <stringProp name="scriptLanguage">groovy</stringProp>
              <stringProp name="parameters"></stringProp>
              <stringProp name="filename"></stringProp>
              <stringProp name="cacheKey">true</stringProp>
              <stringProp name="script">{esc(script)}</stringProp>
            </JSR223Assertion>
            <hashTree/>"""


def jsr223_set_session() -> str:
    """One session_id for place+cancel (helps the agent; order id still required)."""
    script = r"""
if (!vars.get('c_session_id')) {
  vars.put('c_session_id', 'jmeter-' + UUID.randomUUID().toString())
}
""".strip()
    return f"""            <JSR223PreProcessor guiclass="TestBeanGUI" testclass="JSR223PreProcessor" testname="JSR223 set session_id once" enabled="true">
              <stringProp name="scriptLanguage">groovy</stringProp>
              <stringProp name="cacheKey">true</stringProp>
              <stringProp name="script">{esc(script)}</stringProp>
            </JSR223PreProcessor>
            <hashTree/>"""


def jsr223_assert_cancel_chat_soft() -> str:
    """
    Soft check on AI cancel chat: capture tool/status if present.
    Do NOT fail only because model wording is odd (e.g. message='reply').
    Hard proof is jsr223_assert_order_cancelled_in_list on GET /api/orders.
    """
    script = r"""
import groovy.json.JsonSlurper

def body = prev.getResponseDataAsString() ?: ''
vars.put('c_cancel_raw_snip', body.take(400).replace('\\n',' '))
if (!body) {
  AssertionResult.setFailure(true)
  AssertionResult.setFailureMessage('Empty cancel chat response')
  return
}
def json
try {
  json = new JsonSlurper().parseText(body)
} catch (Exception e) {
  AssertionResult.setFailure(true)
  AssertionResult.setFailureMessage('Cancel chat not JSON: ' + e.message + ' body=' + body.take(200))
  return
}

def msg = json.message?.toString() ?: ''
def order = json.entities?.order
def cancel = (json.actions ?: []).find { it.tool == 'cancel_order' }
def toolOk = cancel?.result?.ok == true
def statusCancelled = order?.status?.toString()?.equalsIgnoreCase('Cancelled')
vars.put('c_cancel_chat_msg', msg.take(200))
vars.put('c_cancel_tool_ok', toolOk ? 'true' : 'false')
if (order?.status) vars.put('c_cancel_status', order.status.toString())
if (order?.id) vars.put('c_cancel_order_id', order.id.toString())

// Only hard-fail chat when we can prove cancel was rejected by the tool
if (cancel != null && cancel.result?.ok == false) {
  AssertionResult.setFailure(true)
  AssertionResult.setFailureMessage('cancel_order tool returned ok=false: ' + String.valueOf(cancel.result?.error ?: cancel.result))
  return
}

// If tool clearly succeeded, pass here
if (toolOk || statusCancelled) {
  AssertionResult.setFailure(false)
  return
}

// Otherwise pass chat soft — GET /api/orders assertion is the business gate
AssertionResult.setFailure(false)
log.warn('AI cancel chat did not show cancel_order tool. message=' + msg + ' — will verify via GET /api/orders')
""".strip()
    return f"""            <JSR223Assertion guiclass="TestBeanGUI" testclass="JSR223Assertion" testname="JSR223 soft-check cancel chat (proof is GET orders)" enabled="true">
              <stringProp name="scriptLanguage">groovy</stringProp>
              <stringProp name="cacheKey">true</stringProp>
              <stringProp name="script">{esc(script)}</stringProp>
            </JSR223Assertion>
            <hashTree/>"""


def jsr223_assert_order_cancelled_in_list() -> str:
    """Day 34 style: prove cancel in database via GET /api/orders (not model wording)."""
    script = r"""
import groovy.json.JsonSlurper

def wanted = (vars.get('c_order_id') ?: '').trim()
def body = prev.getResponseDataAsString() ?: ''
if (!wanted || wanted == 'default') {
  AssertionResult.setFailure(true)
  AssertionResult.setFailureMessage('c_order_id missing — place-order extract failed earlier')
  return
}
if (!body) {
  AssertionResult.setFailure(true)
  AssertionResult.setFailureMessage('Empty /api/orders response')
  return
}
def json
try {
  json = new JsonSlurper().parseText(body)
} catch (Exception e) {
  AssertionResult.setFailure(true)
  AssertionResult.setFailureMessage('orders list not JSON: ' + e.message)
  return
}

def orders = json.orders ?: []
def match = orders.find { it.id?.toString()?.equalsIgnoreCase(wanted) }
if (match == null) {
  AssertionResult.setFailure(true)
  AssertionResult.setFailureMessage('Order ' + wanted + ' not found in /api/orders. chatMsg=' + (vars.get('c_cancel_chat_msg') ?: ''))
  return
}
def st = match.status?.toString() ?: ''
if (!st.equalsIgnoreCase('Cancelled')) {
  AssertionResult.setFailure(true)
  AssertionResult.setFailureMessage(
    'Order ' + wanted + ' status is \"' + st + '\" (expected Cancelled). ' +
    'AI cancel likely did not call the tool. chatMsg=' + (vars.get('c_cancel_chat_msg') ?: '') +
    ' raw=' + (vars.get('c_cancel_raw_snip') ?: '')
  )
  return
}
AssertionResult.setFailure(false)
vars.put('c_order_status', 'Cancelled')
""".strip()
    return f"""            <JSR223Assertion guiclass="TestBeanGUI" testclass="JSR223Assertion" testname="JSR223 Assert order Cancelled in /api/orders" enabled="true">
              <stringProp name="scriptLanguage">groovy</stringProp>
              <stringProp name="cacheKey">true</stringProp>
              <stringProp name="script">{esc(script)}</stringProp>
            </JSR223Assertion>
            <hashTree/>"""


def jsr223_log_failures_only() -> str:
    """Day 36: write only failures (serial + error message) to CSV."""
    script = (
        "import java.nio.file.*;\n"
        f'String path = "{FAIL_LOG}";\n'
        "Path p = Paths.get(path);\n"
        'if (!Files.exists(p)) { Files.write(p, ("serial,timestamp,label,order_id,code,message\\n").getBytes("UTF-8")); }\n'
        "if (!prev.isSuccessful()) {\n"
        "  String serial = String.valueOf(System.currentTimeMillis());\n"
        '  String line = serial + "," + serial + "," + prev.getSampleLabel().replace(","," ") + "," +\n'
        '    (vars.get("c_order_id") ?: "") + "," + prev.getResponseCode() + "," +\n'
        '    String.valueOf(prev.getResponseMessage()).replace(","," ").replace("\\n"," ") + "\\n";\n'
        '  Files.write(p, line.getBytes("UTF-8"), StandardOpenOption.APPEND);\n'
        "}\n"
    )
    return f"""            <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="JSR223 Log failures only" enabled="true">
              <stringProp name="scriptLanguage">groovy</stringProp>
              <stringProp name="cacheKey">true</stringProp>
              <stringProp name="script">{esc(script)}</stringProp>
            </JSR223PostProcessor>
            <hashTree/>"""


def jsr223_prometheus_demo() -> str:
    """Day 37: write local file AND push to Pushgateway :9091 (Prometheus scrapes gateway)."""
    script = (
        "import java.nio.file.*;\n"
        f'String path = "{PROM_FILE}";\n'
        "def inTok = vars.get('c_input_tokens') ?: '0';\n"
        "def outTok = vars.get('c_output_tokens') ?: '0';\n"
        "def totTok = vars.get('c_total_tokens') ?: '0';\n"
        "def lat = vars.get('c_latency_ms') ?: '0';\n"
        "def err = prev.isSuccessful() ? '0' : '1';\n"
        "String body = '# HELP voltcart_ai_input_tokens Input tokens\\n'\n"
        "  + '# TYPE voltcart_ai_input_tokens gauge\\n'\n"
        "  + 'voltcart_ai_input_tokens ' + inTok + '\\n'\n"
        "  + '# HELP voltcart_ai_output_tokens Output tokens\\n'\n"
        "  + '# TYPE voltcart_ai_output_tokens gauge\\n'\n"
        "  + 'voltcart_ai_output_tokens ' + outTok + '\\n'\n"
        "  + '# HELP voltcart_ai_total_tokens Total tokens\\n'\n"
        "  + '# TYPE voltcart_ai_total_tokens gauge\\n'\n"
        "  + 'voltcart_ai_total_tokens ' + totTok + '\\n'\n"
        "  + '# HELP voltcart_ai_latency_ms Latency ms\\n'\n"
        "  + '# TYPE voltcart_ai_latency_ms gauge\\n'\n"
        "  + 'voltcart_ai_latency_ms ' + lat + '\\n'\n"
        "  + '# HELP voltcart_ai_errors Error flag\\n'\n"
        "  + '# TYPE voltcart_ai_errors gauge\\n'\n"
        "  + 'voltcart_ai_errors ' + err + '\\n';\n"
        'Files.write(Paths.get(path), body.getBytes("UTF-8"));\n'
        "try {\n"
        "  def url = new URL('http://127.0.0.1:9091/metrics/job/voltcart_jmeter');\n"
        "  def conn = url.openConnection();\n"
        "  conn.setDoOutput(true);\n"
        "  conn.setRequestMethod('POST');\n"
        "  conn.setConnectTimeout(3000);\n"
        "  conn.setReadTimeout(5000);\n"
        "  conn.setRequestProperty('Content-Type', 'text/plain; version=0.0.4; charset=utf-8');\n"
        "  conn.getOutputStream().withWriter('UTF-8') { it << body };\n"
        "  def code = conn.getResponseCode();\n"
        "  log.info('Pushgateway response code=' + code + ' total_tokens=' + totTok);\n"
        "  if (code < 200 || code >= 300) { log.warn('Pushgateway push failed HTTP ' + code); }\n"
        "} catch (Exception e) {\n"
        "  log.warn('Pushgateway push error (is :9091 running?): ' + e.message);\n"
        "}\n"
    )
    return f"""            <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="JSR223 Prometheus metrics demo (Day 37)" enabled="true">
              <stringProp name="scriptLanguage">groovy</stringProp>
              <stringProp name="cacheKey">true</stringProp>
              <stringProp name="script">{esc(script)}</stringProp>
            </JSR223PostProcessor>
            <hashTree/>"""


def duration_assertion(name: str, ms: str) -> str:
    return f"""            <DurationAssertion guiclass="DurationAssertionGui" testclass="DurationAssertion" testname="{esc(name)}" enabled="true">
              <stringProp name="DurationAssertion.duration">{esc(ms)}</stringProp>
            </DurationAssertion>
            <hashTree/>"""


def place_order_validations(extract_fields: bool = True, use_jsr223: bool = True) -> str:
    """
    Full class stack for place-order verification:
      Response Assertion + JSON Assertion + JSR223 Assertion (Day 35/36)
    """
    parts = [
        response_code_assertion("Assert HTTP 200 (transport)"),
        response_assertion("Assert message: Order placed successfully", "Order placed successfully"),
        response_assertion("Assert order id prefix ORD-", "ORD-"),
        response_assertion("Assert status Confirmed", '"status": "Confirmed"'),
        response_assertion("Assert trace outcome success", '"outcome": "success"'),
        response_assertion("Assert place_order tool ran", '"tool": "place_order"'),
        response_assertion("Assert place_order ok true", '"ok": true'),
        response_assertion("Assert order cancellable", '"cancellable": true'),
        json_path_assertion("JSON: entities.order.status = Confirmed", "$.entities.order.status", "Confirmed"),
        json_path_assertion("JSON: trace.outcome = success", "$.trace.outcome", "success"),
        json_path_exists("JSON: entities.order.id exists", "$.entities.order.id"),
        json_path_exists("JSON: entities.order.total exists", "$.entities.order.total"),
        json_path_exists("JSON: entities.product.name exists", "$.entities.product.name"),
        json_path_assertion("JSON: clarification is false", "$.trace.clarification", "false"),
        # Learning only — raise if you have a strict SLA; Ollama often > 60s
        duration_assertion("Duration soft check (180s SLA learning)", "180000"),
    ]
    if extract_fields:
        parts.extend(
            [
                json_extractor("c_order_id", "$.entities.order.id", match="1", default="default"),
                regex_extractor("c_order_id_regex", r"(ORD-[0-9]{8}-[A-Z0-9]+)", match="1", default="default"),
                json_extractor("c_order_status", "$.entities.order.status", default="default"),
                json_extractor("c_order_total", "$.entities.order.total", default="0"),
                json_extractor("c_product_ordered", "$.entities.product.name", default="default"),
                json_extractor("c_outcome", "$.trace.outcome", default="default"),
                json_extractor("c_input_tokens", "$.trace.input_tokens", default="0"),
                json_extractor("c_output_tokens", "$.trace.output_tokens", default="0"),
                json_extractor("c_total_tokens", "$.trace.total_tokens", default="0"),
                json_extractor("c_cost", "$.trace.estimated_cost_usd", default="0"),
                json_extractor("c_latency_ms", "$.trace.latency_ms", default="0"),
                json_extractor("c_trace_id", "$.trace.id", default=""),
            ]
        )
    if use_jsr223:
        parts.append(jsr223_assert_place_order())
        parts.append(jsr223_log_failures_only())
        parts.append(jsr223_token_log())
        parts.append(jsr223_prometheus_demo())
    return "\n".join(parts)


def cancel_order_validations(order_var: str = "${c_order_id}") -> str:
    # Chat wording from small models is unreliable (seen: message="reply").
    # Soft-check chat; hard proof is GET /api/orders (separate sampler).
    return "\n".join(
        [
            response_code_assertion("Assert HTTP 200 (transport)"),
            json_extractor("c_cancel_order_id", "$.entities.order.id", default="default"),
            json_extractor("c_cancel_status", "$.entities.order.status", default="default"),
            jsr223_assert_cancel_chat_soft(),
            jsr223_log_failures_only(),
        ]
    )


def verify_cancelled_sampler() -> str:
    children = (
        response_code_assertion()
        + "\n"
        + response_assertion("Assert orders array", "orders")
        + "\n"
        + jsr223_assert_order_cancelled_in_list()
    )
    return http("06 Verify order is Cancelled", "GET", "api/orders", children=children)


def constant_timer(ms: str = "1000") -> str:
    return f"""          <ConstantTimer guiclass="ConstantTimerGui" testclass="ConstantTimer" testname="Think Time {esc(ms)} ms" enabled="true">
            <stringProp name="ConstantTimer.delay">{esc(ms)}</stringProp>
          </ConstantTimer>
          <hashTree/>"""


def debug_sampler(enabled: bool = True) -> str:
    flag = "true" if enabled else "false"
    return f"""          <DebugSampler guiclass="TestBeanGUI" testclass="DebugSampler" testname="Debug Sampler (turn OFF for load)" enabled="{flag}">
            <boolProp name="displayJMeterProperties">false</boolProp>
            <boolProp name="displayJMeterVariables">true</boolProp>
            <boolProp name="displaySystemProperties">false</boolProp>
          </DebugSampler>
          <hashTree/>"""


def transaction(name: str, children: str, parent: bool = True) -> str:
    gen = "true" if parent else "false"
    return f"""        <TransactionController guiclass="TransactionControllerGui" testclass="TransactionController" testname="{esc(name)}" enabled="true">
          <boolProp name="TransactionController.includeTimers">false</boolProp>
          <boolProp name="TransactionController.parent">{gen}</boolProp>
        </TransactionController>
        <hashTree>
{children}
        </hashTree>"""


def thread_group(
    name: str,
    threads: str = "1",
    ramp: str = "1",
    loops: str = "1",
    children: str = "",
    enabled: bool = True,
    forever: bool = False,
    duration: str = "",
) -> str:
    en = "true" if enabled else "false"
    forever_flag = "true" if forever else "false"
    loop_val = "-1" if forever else loops
    scheduler = "true" if duration else "false"
    dur = duration or "0"
    return f"""      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="{esc(name)}" enabled="{en}">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <boolProp name="LoopController.continue_forever">{forever_flag}</boolProp>
          <stringProp name="LoopController.loops">{loop_val}</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">{threads}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">{ramp}</stringProp>
        <boolProp name="ThreadGroup.scheduler">{scheduler}</boolProp>
        <stringProp name="ThreadGroup.duration">{dur}</stringProp>
        <stringProp name="ThreadGroup.delay">0</stringProp>
      </ThreadGroup>
      <hashTree>
{children}
      </hashTree>"""


def csv_config(
    filename: str,
    vars_: str = "email,password,name",
    recycle: bool = False,
    stop: bool = True,
) -> str:
    return f"""          <CSVDataSet guiclass="TestBeanGUI" testclass="CSVDataSet" testname="CSV Data Set Config" enabled="true">
            <stringProp name="filename">{esc(filename)}</stringProp>
            <stringProp name="fileEncoding">UTF-8</stringProp>
            <stringProp name="variableNames">{esc(vars_)}</stringProp>
            <boolProp name="ignoreFirstLine">true</boolProp>
            <stringProp name="delimiter">,</stringProp>
            <boolProp name="quotedData">false</boolProp>
            <boolProp name="recycle">{"true" if recycle else "false"}</boolProp>
            <boolProp name="stopThread">{"true" if stop else "false"}</boolProp>
            <stringProp name="shareMode">shareMode.all</stringProp>
          </CSVDataSet>
          <hashTree/>"""


def common_config(extra_udv: str = "") -> str:
    return f"""      <Arguments guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments">
          <elementProp name="host" elementType="Argument">
            <stringProp name="Argument.name">host</stringProp>
            <stringProp name="Argument.value">127.0.0.1</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="port" elementType="Argument">
            <stringProp name="Argument.name">port</stringProp>
            <stringProp name="Argument.value">8000</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="p_email" elementType="Argument">
            <stringProp name="Argument.name">p_email</stringProp>
            <stringProp name="Argument.value">aarav@voltcart.demo</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="p_password" elementType="Argument">
            <stringProp name="Argument.name">p_password</stringProp>
            <stringProp name="Argument.value">Demo@123</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
{extra_udv}
        </collectionProp>
      </Arguments>
      <hashTree/>
      <ConfigTestElement guiclass="HttpDefaultsGui" testclass="ConfigTestElement" testname="HTTP Request Defaults" enabled="true">
        <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
          <collectionProp name="Arguments.arguments"/>
        </elementProp>
        <stringProp name="HTTPSampler.domain">${{host}}</stringProp>
        <stringProp name="HTTPSampler.port">${{port}}</stringProp>
        <stringProp name="HTTPSampler.protocol">http</stringProp>
        <boolProp name="HTTPSampler.image_parser">false</boolProp>
        <boolProp name="HTTPSampler.concurrentDwn">false</boolProp>
      </ConfigTestElement>
      <hashTree/>
      <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="HTTP Header Manager" enabled="true">
        <collectionProp name="HeaderManager.headers">
          <elementProp name="" elementType="Header">
            <stringProp name="Header.name">Content-Type</stringProp>
            <stringProp name="Header.value">application/json</stringProp>
          </elementProp>
          <elementProp name="" elementType="Header">
            <stringProp name="Header.name">Accept</stringProp>
            <stringProp name="Header.value">application/json</stringProp>
          </elementProp>
        </collectionProp>
      </HeaderManager>
      <hashTree/>
      <CookieManager guiclass="CookiePanel" testclass="CookieManager" testname="HTTP Cookie Manager" enabled="true">
        <collectionProp name="CookieManager.cookies"/>
        <boolProp name="CookieManager.clearEachIteration">true</boolProp>
        <boolProp name="CookieManager.controlledByThreadGroup">false</boolProp>
      </CookieManager>
      <hashTree/>
      <CacheManager guiclass="CacheManagerGui" testclass="CacheManager" testname="HTTP Cache Manager" enabled="true">
        <boolProp name="clearEachIteration">true</boolProp>
        <boolProp name="useExpires">true</boolProp>
      </CacheManager>
      <hashTree/>"""


def listeners() -> str:
    return """      <ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="View Results Tree" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <timestamp>true</timestamp>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <encoding>false</encoding>
            <assertions>true</assertions>
            <subresults>true</subresults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>false</xml>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>true</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave>0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <url>true</url>
            <threadCounts>true</threadCounts>
            <idleTime>true</idleTime>
            <connectTime>true</connectTime>
          </value>
        </objProp>
        <stringProp name="filename"></stringProp>
      </ResultCollector>
      <hashTree/>
      <ResultCollector guiclass="SummaryReport" testclass="ResultCollector" testname="Summary Report" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <timestamp>true</timestamp>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <encoding>false</encoding>
            <assertions>true</assertions>
            <subresults>true</subresults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>false</xml>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>true</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave>0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <url>true</url>
            <threadCounts>true</threadCounts>
            <idleTime>true</idleTime>
            <connectTime>true</connectTime>
          </value>
        </objProp>
        <stringProp name="filename"></stringProp>
      </ResultCollector>
      <hashTree/>"""


def wrap(plan_name: str, comments: str, body: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="{esc(plan_name)}" enabled="true">
      <stringProp name="TestPlan.comments">{esc(comments)}</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" enabled="true">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
    </TestPlan>
    <hashTree>
{common_config()}
{body}
{listeners()}
    </hashTree>
  </hashTree>
</jmeterTestPlan>
"""


def login_sampler(email_var: str = "${p_email}", password_var: str = "${p_password}") -> str:
    body = f'{{"email":"{email_var}","password":"{password_var}"}}'
    # Keep ${} unescaped in JSON for JMeter variables — build carefully
    body = '{"email":"' + email_var + '","password":"' + password_var + '"}'
    return http(
        "01 Login",
        "POST",
        "api/auth/login",
        body=body,
        children=response_code_assertion() + "\n" + response_assertion("Assert login ok", '"ok": true'),
    )


def products_sampler(with_extract: bool = False, match: str = "0") -> str:
    children = response_code_assertion() + "\n" + response_assertion("Assert products key", "products")
    if with_extract:
        children += "\n" + json_extractor("c_product_name", "$.products[*].name", match=match, default="Pixel 8a 128GB")
        children += "\n" + json_extractor("c_product_id", "$.products[*].id", match=match, default="PHN-104")
    return http("02 Product list", "GET", "api/products", query=[("limit", "5")], children=children)


def place_order_sampler(product_var: str = "${c_product_name}", extract_order: bool = True) -> str:
    # Reuse c_session_id so place + cancel share one agent conversation
    body = (
        '{"message":"Place an order for 1 x '
        + product_var
        + '","session_id":"${c_session_id}","message_id":"msg-${__UUID}"}'
    )
    children = jsr223_set_session() + "\n" + place_order_validations(extract_fields=extract_order)
    # Ollama place-order can exceed 60s (your sample ~112s) — allow 3 minutes
    return http(
        "03 AI Place order",
        "POST",
        "api/chat",
        body=body,
        children=children,
        response_timeout_ms="180000",
    )


def verify_orders_sampler() -> str:
    children = (
        response_code_assertion()
        + "\n"
        + response_assertion("Assert order id present in list", "${c_order_id}")
        + "\n"
        + response_assertion("Assert orders array", "orders")
        + "\n"
        + json_extractor("c_latest_order", "$.orders[0].id", default="default")
    )
    return http("04 Verify orders list", "GET", "api/orders", children=children)


def cancel_order_sampler(order_var: str = "${c_order_id}") -> str:
    # Exact class/BlazeMeter style wording — small models often ignore "Please..."
    body = (
        '{"message":"Cancel order '
        + order_var
        + '","session_id":"${c_session_id}","message_id":"msg-${__UUID}"}'
    )
    children = jsr223_set_session() + "\n" + cancel_order_validations(order_var)
    return http(
        "05 AI Cancel order",
        "POST",
        "api/chat",
        body=body,
        children=children,
        response_timeout_ms="180000",
    )


def cancel_then_verify(order_var: str = "${c_order_id}") -> str:
    """AI cancel chat + hard prove Cancelled via GET /api/orders."""
    return cancel_order_sampler(order_var) + "\n" + verify_cancelled_sampler()


def jsr223_token_log() -> str:
    script = (
        "import java.nio.file.*;\n"
        f'String path = "{TOKEN_LOG}";\n'
        "Path p = Paths.get(path);\n"
        'if (!Files.exists(p)) { Files.write(p, ("timestamp,thread,order_id,product,input_tokens,output_tokens,total_tokens,cost,latency_ms,outcome,trace_id\\n").getBytes("UTF-8")); }\n'
        'String line = System.currentTimeMillis() + "," + ctx.getThread().getThreadName() + "," +\n'
        '  (vars.get("c_order_id") ?: "") + "," + (vars.get("c_product_ordered") ?: "") + "," +\n'
        '  (vars.get("c_input_tokens") ?: "0") + "," + (vars.get("c_output_tokens") ?: "0") + "," +\n'
        '  (vars.get("c_total_tokens") ?: "0") + "," + (vars.get("c_cost") ?: "0") + "," +\n'
        '  (vars.get("c_latency_ms") ?: "0") + "," + (vars.get("c_outcome") ?: "") + "," +\n'
        '  (vars.get("c_trace_id") ?: "") + "\\n";\n'
        'Files.write(p, line.getBytes("UTF-8"), StandardOpenOption.APPEND);\n'
    )
    return f"""            <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="JSR223 Token Logger" enabled="true">
              <stringProp name="scriptLanguage">groovy</stringProp>
              <stringProp name="parameters"></stringProp>
              <stringProp name="filename"></stringProp>
              <stringProp name="cacheKey">true</stringProp>
              <stringProp name="script">{esc(script)}</stringProp>
            </JSR223PostProcessor>
            <hashTree/>"""


def build_01() -> None:
    flow = (
        login_sampler()
        + "\n"
        + products_sampler(with_extract=False)
        + "\n"
        + place_order_sampler("Pixel 8a 128GB", extract_order=True)
        + "\n"
        + verify_orders_sampler()
        + "\n"
        + cancel_then_verify("${c_order_id}")
    )
    body = thread_group(
        "Smoke - 1 user 1 loop (Day 29)",
        threads="1",
        ramp="1",
        loops="1",
        children=transaction("Login > Place > Cancel", flow),
    )
    (OUT / "01_Day29_Basics_Smoke.jmx").write_text(
        wrap(
            "01 Day29 Basics Smoke",
            "Day 29 + place-order response validations from real API: Order placed successfully, Confirmed, outcome success, entities.order.id, place_order ok. Timeout 180s for AI.",
            body,
        ),
        encoding="utf-8",
    )


def build_02() -> None:
    flow = (
        constant_timer("1000")
        + "\n"
        + login_sampler()
        + "\n"
        + products_sampler()
        + "\n"
        + place_order_sampler("Pixel 8a 128GB")
    )
    body = thread_group(
        "Users + think time (Day 32)",
        threads="3",
        ramp="3",
        loops="2",
        children=transaction("Browse-ish AI path", flow),
    )
    (OUT / "02_Day32_Users_ThinkTime.jmx").write_text(
        wrap(
            "02 Day32 Users ThinkTime",
            "Day 32: more users should raise throughput; Constant Timer is think time (not server time). Read Average, Throughput, Error% in Summary Report.",
            body,
        ),
        encoding="utf-8",
    )


def build_03() -> None:
    flow = (
        csv_config(CSV_USERS, recycle=False, stop=True)
        + "\n"
        + login_sampler("${email}", "${password}")
        + "\n"
        + products_sampler()
        + "\n"
        + place_order_sampler("Pixel 8a 128GB")
    )
    body = thread_group(
        "CSV driven login (Day 33)",
        threads="2",
        ramp="1",
        loops="1",
        children=transaction("CSV login + place order", flow),
    )
    (OUT / "03_Day33_CSV_Parameterization.jmx").write_text(
        wrap(
            "03 Day33 CSV Parameterization",
            f"Day 33: CSV Data Set Config. Columns email,password,name become ${{email}} etc. Recycle=false StopThread=true. CSV path: {CSV_USERS}",
            body,
        ),
        encoding="utf-8",
    )


def build_04() -> None:
    fix_order = """            <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="Prefer entity order id else regex" enabled="true">
              <stringProp name="scriptLanguage">groovy</stringProp>
              <stringProp name="cacheKey">true</stringProp>
              <stringProp name="script">def id = vars.get("c_order_id"); if (id == null || id == "default") { def r = vars.get("c_order_id_regex"); if (r != null &amp;&amp; r != "default") { vars.put("c_order_id", r); } }</stringProp>
            </JSR223PostProcessor>
            <hashTree/>"""

    body_json = (
        '{"message":"Place an order for 1 x ${c_product_name}","session_id":"${c_session_id}","message_id":"msg-${__UUID}"}'
    )
    place_children = jsr223_set_session() + "\n" + place_order_validations(extract_fields=True) + "\n" + fix_order
    place = http(
        "03 AI Place order (correlated product)",
        "POST",
        "api/chat",
        body=body_json,
        children=place_children,
        response_timeout_ms="180000",
    )

    if_cancel = f"""          <IfController guiclass="IfControllerPanel" testclass="IfController" testname="If order id extracted" enabled="true">
            <stringProp name="IfController.condition">${{__jexl3(vars.get("c_order_id") != null &amp;&amp; !vars.get("c_order_id").equals("default"))}}</stringProp>
            <boolProp name="IfController.evaluateAll">false</boolProp>
            <boolProp name="IfController.useExpression">true</boolProp>
          </IfController>
          <hashTree>
{verify_orders_sampler()}
{cancel_then_verify("${c_order_id}")}
          </hashTree>"""

    flow = (
        csv_config(CSV_USERS, recycle=True, stop=False)
        + "\n"
        + constant_timer("1000")
        + "\n"
        + login_sampler("${email}", "${password}")
        + "\n"
        + products_sampler(with_extract=True, match="0")
        + "\n"
        + place
        + "\n"
        + if_cancel
        + "\n"
        + debug_sampler(True)
    )
    body = thread_group(
        "Correlation + Assertions (Day 34/35)",
        threads="1",
        ramp="1",
        loops="2",
        children=transaction("Login > correlate product > place > verify > cancel", flow),
    )
    (OUT / "04_Day34_Correlation_Assertions.jmx").write_text(
        wrap(
            "04 Day34 Correlation Assertions",
            "Day 34/35: correlate product + full place-order validations (message, Confirmed, outcome, JSONPath entities.order.*) + cancel with ${c_order_id}.",
            body,
        ),
        encoding="utf-8",
    )


def build_05() -> None:
    login_loop = f"""          <LoopController guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller - login once style" enabled="true">
            <boolProp name="LoopController.continue_forever">false</boolProp>
            <stringProp name="LoopController.loops">1</stringProp>
          </LoopController>
          <hashTree>
{login_sampler("${email}", "${password}")}
          </hashTree>"""

    throughput_browse = f"""          <ThroughputController guiclass="ThroughputControllerGui" testclass="ThroughputController" testname="Throughput 30% - browse only" enabled="true">
            <intProp name="ThroughputController.style">1</intProp>
            <boolProp name="ThroughputController.perThread">true</boolProp>
            <intProp name="ThroughputController.maxThroughput">1</intProp>
            <FloatProperty>
              <name>ThroughputController.percentThroughput</name>
              <value>30.0</value>
              <savedValue>0.0</savedValue>
            </FloatProperty>
          </ThroughputController>
          <hashTree>
{products_sampler(with_extract=True, match="0")}
          </hashTree>"""

    fix_order = """            <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="Prefer entity order id else regex" enabled="true">
              <stringProp name="scriptLanguage">groovy</stringProp>
              <stringProp name="cacheKey">true</stringProp>
              <stringProp name="script">def id = vars.get("c_order_id"); if (id == null || id == "default") { def r = vars.get("c_order_id_regex"); if (r != null &amp;&amp; r != "default") { vars.put("c_order_id", r); } }</stringProp>
            </JSR223PostProcessor>
            <hashTree/>"""
    place_children = jsr223_set_session() + "\n" + place_order_validations(extract_fields=True, use_jsr223=True) + "\n" + fix_order
    place = http(
        "AI Place order",
        "POST",
        "api/chat",
        body='{"message":"Place an order for 1 x ${c_product_name}","session_id":"${c_session_id}","message_id":"msg-${__UUID}"}',
        children=place_children,
        response_timeout_ms="180000",
    )

    throughput_order = f"""          <ThroughputController guiclass="ThroughputControllerGui" testclass="ThroughputController" testname="Throughput 70% - place+cancel" enabled="true">
            <intProp name="ThroughputController.style">1</intProp>
            <boolProp name="ThroughputController.perThread">true</boolProp>
            <intProp name="ThroughputController.maxThroughput">1</intProp>
            <FloatProperty>
              <name>ThroughputController.percentThroughput</name>
              <value>70.0</value>
              <savedValue>0.0</savedValue>
            </FloatProperty>
          </ThroughputController>
          <hashTree>
{products_sampler(with_extract=True, match="0")}
{place}
            <IfController guiclass="IfControllerPanel" testclass="IfController" testname="If order id ok then cancel" enabled="true">
              <stringProp name="IfController.condition">${{__jexl3(vars.get("c_order_id") != null &amp;&amp; !vars.get("c_order_id").equals("default"))}}</stringProp>
              <boolProp name="IfController.evaluateAll">false</boolProp>
              <boolProp name="IfController.useExpression">true</boolProp>
            </IfController>
            <hashTree>
{cancel_then_verify("${c_order_id}")}
            </hashTree>
          </hashTree>"""

    sync_timer = """          <SyncTimer guiclass="TestBeanGUI" testclass="SyncTimer" testname="Synchronizing Timer (spike demo)" enabled="false">
            <intProp name="groupSize">2</intProp>
            <longProp name="timeoutInMs">10000</longProp>
          </SyncTimer>
          <hashTree/>"""

    ctt = """          <ConstantThroughputTimer guiclass="TestBeanGUI" testclass="ConstantThroughputTimer" testname="Constant Throughput Timer ~12/min" enabled="true">
            <intProp name="calcMode">0</intProp>
            <doubleProp>
              <name>throughput</name>
              <value>12.0</value>
              <savedValue>0.0</savedValue>
            </doubleProp>
          </ConstantThroughputTimer>
          <hashTree/>"""

    flow = (
        csv_config(CSV_USERS, recycle=True, stop=False)
        + "\n"
        + sync_timer
        + "\n"
        + ctt
        + "\n"
        + login_loop
        + "\n"
        + throughput_browse
        + "\n"
        + throughput_order
        + "\n"
        + debug_sampler(False)
    )
    body = thread_group(
        "Controllers + token log (Day 36)",
        threads="2",
        ramp="2",
        forever=True,
        duration="60",
        children=flow,
    )
    (OUT / "05_Day36_Controllers_TokenLog.jmx").write_text(
        wrap(
            "05 Day36 Controllers TokenLog",
            "Day 36: Loop Controller, Throughput Controller 70/30, Constant Throughput Timer, Sync Timer (disabled), JSR223 token log to data/token_log.csv. Duration 60s.",
            body,
        ),
        encoding="utf-8",
    )


def build_06() -> None:
    """Dedicated Day 36/37: JSR223 response verify + token CSV + Prometheus demo file."""
    flow = (
        login_sampler()
        + "\n"
        + products_sampler(with_extract=True, match="0")
        + "\n"
        + place_order_sampler("${c_product_name}", extract_order=True)
        + "\n"
        + debug_sampler(True)
        + "\n"
        + verify_orders_sampler()
        + "\n"
        + cancel_then_verify("${c_order_id}")
    )
    body = thread_group(
        "JSR223 verify + token + prometheus demo",
        threads="1",
        ramp="1",
        loops="1",
        children=transaction("Full AI path with JSR223", flow),
    )
    (OUT / "06_Day36_37_JSR223_Verify_Token_Prometheus.jmx").write_text(
        wrap(
            "06 Day36-37 JSR223 Verify Token Prometheus",
            "Class Day 36/37: JSR223 Assertion verifies place-order JSON; JSR223 logs tokens + failures; Prometheus text file demo for Pushgateway/Grafana later.",
            body,
        ),
        encoding="utf-8",
    )


def build_07() -> None:
    """Day 34: two thread groups — registration (disabled) + place-order (enabled)."""
    reg = thread_group(
        "01 Registration TG (DISABLED once users exist)",
        threads="1",
        ramp="1",
        loops="1",
        enabled=False,
        children=(
            csv_config(CSV_USERS, recycle=False, stop=True)
            + "\n"
            + http(
                "Register (demo — enable only for new emails)",
                "POST",
                "api/auth/register",
                body='{"name":"${name}","email":"${email}","phone":"9876543210","password":"${password}"}',
                children=response_code_assertion(),
            )
        ),
    )
    place = thread_group(
        "02 Place-order TG (ENABLED)",
        threads="1",
        ramp="1",
        loops="2",
        enabled=True,
        children=(
            csv_config(CSV_USERS, recycle=True, stop=False)
            + "\n"
            + constant_timer("1000")
            + "\n"
            + transaction(
                "login > products > place > verify > cancel",
                login_sampler("${email}", "${password}")
                + "\n"
                + products_sampler(with_extract=True, match="0")
                + "\n"
                + place_order_sampler("${c_product_name}", extract_order=True)
                + "\n"
                + verify_orders_sampler()
                + "\n"
                + cancel_then_verify("${c_order_id}")
                + "\n"
                + debug_sampler(True),
            )
        ),
    )
    (OUT / "07_Day34_Two_ThreadGroups.jmx").write_text(
        wrap(
            "07 Day34 Two Thread Groups",
            "Day 34: Registration TG disabled + Place-order TG enabled; same CSV; right-click TG to enable/disable.",
            reg + "\n" + place,
        ),
        encoding="utf-8",
    )


def build_08() -> None:
    """Day 35: Constant Timer vs Constant Throughput Timer + workload split."""
    ctt = """          <ConstantThroughputTimer guiclass="TestBeanGUI" testclass="ConstantThroughputTimer" testname="Constant Throughput Timer target ~6/min" enabled="true">
            <intProp name="calcMode">0</intProp>
            <doubleProp>
              <name>throughput</name>
              <value>6.0</value>
              <savedValue>0.0</savedValue>
            </doubleProp>
          </ConstantThroughputTimer>
          <hashTree/>"""
    flow_a = thread_group(
        "A - Constant Timer think-time (fixed delay)",
        threads="2",
        ramp="2",
        loops="3",
        children=(
            constant_timer("2000")
            + "\n"
            + login_sampler()
            + "\n"
            + products_sampler()
        ),
    )
    flow_b = thread_group(
        "B - Constant Throughput Timer (target rate)",
        threads="2",
        ramp="2",
        forever=True,
        duration="45",
        children=(
            ctt
            + "\n"
            + login_sampler()
            + "\n"
            + products_sampler()
            + "\n"
            + place_order_sampler("Pixel 8a 128GB", extract_order=True)
        ),
    )
    (OUT / "08_Day35_Timers_Workload.jmx").write_text(
        wrap(
            "08 Day35 Timers Workload",
            "Day 35: TG A uses Constant Timer (think time). TG B uses Constant Throughput Timer (rate). Compare Average vs Throughput in Summary. Little's Law is planning math — see COVERAGE.md.",
            flow_a + "\n" + flow_b,
        ),
        encoding="utf-8",
    )


def build_09_sync_spike() -> None:
    """Day 36 Synchronizing Timer spike pattern."""
    sync = """          <SyncTimer guiclass="TestBeanGUI" testclass="SyncTimer" testname="Synchronizing Timer group=2" enabled="true">
            <intProp name="groupSize">2</intProp>
            <longProp name="timeoutInMs">30000</longProp>
          </SyncTimer>
          <hashTree/>"""
    flow = (
        sync
        + "\n"
        + login_sampler()
        + "\n"
        + products_sampler()
        + "\n"
        + place_order_sampler("Pixel 8a 128GB", extract_order=True)
    )
    body = thread_group(
        "Spike release with Sync Timer (Day 36)",
        threads="2",
        ramp="10",
        loops="1",
        children=transaction("Synced place-order spike", flow),
    )
    (OUT / "09_Day36_Synchronizing_Timer_Spike.jmx").write_text(
        wrap(
            "09 Day36 Synchronizing Timer Spike",
            "Day 36: users wait then release together (spike). Not for every load test — only true simultaneous events.",
            body,
        ),
        encoding="utf-8",
    )


def write_coverage_doc() -> None:
    (OUT / "COVERAGE.md").write_text(
        """# Class notes → script coverage (Day 27–39)

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
""",
        encoding="utf-8",
    )


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    build_01()
    build_02()
    build_03()
    build_04()
    build_05()
    build_06()
    build_07()
    build_08()
    build_09_sync_spike()
    write_coverage_doc()
    print("Wrote JMX scripts + COVERAGE.md to", OUT)


if __name__ == "__main__":
    main()
