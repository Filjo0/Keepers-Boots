/** Real Chrome smoke check, using Node 22+ built-ins only. Start the local API first. */
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { access, mkdir, mkdtemp, readFile, writeFile, rm } from "node:fs/promises";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const artifacts = join(root, "local-artifacts");
const url = new URL(process.argv[2] || "http://127.0.0.1:8000");
assert(["127.0.0.1", "localhost"].includes(url.hostname) && url.protocol === "http:", "Use a local HTTP target.");
const candidates = [process.argv[3], "C:/Program Files/Google/Chrome/Application/chrome.exe", "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"].filter(Boolean);
let executable;
for (const candidate of candidates) { try { await access(candidate); executable = candidate; break; } catch {} }
assert(executable, "Supply an installed Chromium browser path as the second argument.");
await mkdir(artifacts, { recursive: true });
const profile = await mkdtemp(join(artifacts, "keeper-browser-"));
const child = spawn(executable, ["--headless=new", "--disable-gpu", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "--no-first-run", "--no-default-browser-check", "--disable-background-networking", "--disable-component-update", "--disable-sync", "about:blank"], { stdio: ["ignore", "ignore", "pipe"], windowsHide: true });
let browserLog = "";
child.stderr.on("data", (chunk) => { browserLog = (browserLog + chunk).slice(-8000); });
const pause = (ms) => new Promise((done) => setTimeout(done, ms));
let socket, closed = false, nextId = 0, session;
const pending = new Map(), failures = [], responses = [], requests = [];
child.on("exit", () => { closed = true; });
child.on("error", (error) => failures.push(error.message));

async function waitFor(check, label, timeout = 10000) {
  const until = Date.now() + timeout;
  while (Date.now() < until) { if (await check()) return; await pause(50); }
  throw new Error(`Timed out: ${label}`);
}
function send(method, params = {}, target = session) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`Timeout: ${method}`)); }, 10000);
    pending.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params, ...(target ? { sessionId: target } : {}) }));
  });
}
async function evaluate(expression) {
  const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}
async function click(selector) {
  const point = await evaluate(`(() => { const el = document.querySelector(${JSON.stringify(selector)}); if (!el || el.disabled || !el.getClientRects().length) throw new Error('Unavailable control'); el.scrollIntoView({block: 'center'}); const rect = el.getBoundingClientRect(); return {x: rect.x + rect.width / 2, y: rect.y + rect.height / 2}; })()`);
  await send("Input.dispatchMouseEvent", { type: "mousePressed", ...point, button: "left", clickCount: 1 });
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", ...point, button: "left", clickCount: 1 });
}
async function visible(selector) { return evaluate(`!!document.querySelector(${JSON.stringify(selector)})?.getClientRects().length`); }
async function text(selector) { return evaluate(`document.querySelector(${JSON.stringify(selector)})?.textContent`); }
async function screenshot(name) {
  const result = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  await writeFile(join(artifacts, name), Buffer.from(result.data, "base64"));
}
async function noOverflow() {
  assert(await evaluate("document.documentElement.scrollWidth <= innerWidth"), "Page must not overflow horizontally.");
}

async function revealAndPlay() {
  await click("#reveal");
  await waitFor(async () => !(await visible("#reveal")), "continuation revealed");
  if (await evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")) {
    assert.equal(await text("#play"), "Play continuation");
    assert((await text("#status")).includes("Continuation ready"));
    await click("#play");
  }
  await waitFor(async () => (await text("#play")) === "Pause", "continuation playing");
}

async function auditWorkflow() {
  const response = responses.filter((entry) => entry.response.url.endsWith("/choice")).at(-1);
  const { body } = await send("Network.getResponseBody", { requestId: response.requestId });
  const data = JSON.parse(body);
  if (!data.interpretation.trace.length) return;
  await click("#analyst-view");
  assert(await visible("#workflow-trace"));
  if (!(await evaluate("document.querySelector('#workflow-trace').open"))) await click("#workflow-trace > summary");
  if (["local_agents", "recorded_agents"].includes(data.interpretation.source)) {
    assert((await text("#trace-steps")).includes("mcp"));
    assert(await visible("#reviewed-claims"));
    assert.equal(await evaluate("document.querySelectorAll('#claim-list > li').length"), data.interpretation.claims.length);
    await click("#fan-view"); assert.equal(await text("#summary"), data.explanation.summary);
    assert.equal(await visible("#workflow-trace"), false);
    assert(!(await text("#evidence-cards")).includes("Sampled margin:"));
    await click("#analyst-view"); assert.equal(await text("#summary"), data.explanation.analyst_summary);
    assert(await visible("#workflow-trace"));
    assert.notEqual(data.explanation.summary, data.explanation.analyst_summary, "Audience versions must differ.");
    await click("#fan-view");
    if (data.interpretation.source === "recorded_agents") {
      assert(["tempting-short-pass", "press-arrives", "uncertain-outlet"].includes(data.assessment.scenario_id));
      const expected = JSON.parse(await readFile(join(root, "data", "agent-recordings", data.assessment.scenario_id + ".json"), "utf8"));
      for (const field of ["fan", "analyst", "claims", "trace", "model", "elapsed_s", "missing_information"]) {
        assert.deepEqual(data.interpretation[field], expected.interpretation[field], `Served recorded ${field} must match the current fixture.`);
      }
      assert.deepEqual(data.interpretation.recording, expected.recording, "Served capture provenance must match the current fixture.");
      assert((await text("#explanation-source")).includes("AI explanation recorded"));
      assert((await text("#explanation-source")).includes("numbers rechecked now"));
      assert(!(await text("#explanation-source")).includes(data.interpretation.model));
      assert((await text("#recording-disclosure")).includes("No new AI explanation"));
      await click("#analyst-view");
      assert((await text("#explanation-source")).includes("Recorded agent output"));
      assert((await text("#explanation-source")).includes(data.interpretation.recording.saved_at_utc));
      assert((await text("#explanation-source")).includes(data.interpretation.model));
      assert((await text("#recording-disclosure")).includes("no live agent, model or MCP calls"));
      await click("#fan-view");
      assert(await visible("#recording-disclosure"));
      assert.equal(await visible("#recording-notes"), !!data.interpretation.recording.notes.length);
      for (const note of data.interpretation.recording.notes) assert((await text("#recording-notes")).includes(note));
    }
  } else if (data.interpretation.reason === "review_not_accepted") {
    assert((await text("#explanation-source")).includes("draft not approved"));
    assert.equal(await visible("#reviewed-claims"), false);
  }
}

try {
  let port;
  await waitFor(async () => {
    try { port = Number((await readFile(join(profile, "DevToolsActivePort"), "utf8")).split("\n")[0]); return !!port; }
    catch { return false; }
  }, "browser startup", 15000);
  const version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
  socket = new WebSocket(version.webSocketDebuggerUrl);
  await new Promise((done, reject) => { socket.addEventListener("open", done, { once: true }); socket.addEventListener("error", reject, { once: true }); });
  socket.addEventListener("message", ({ data }) => {
    const message = JSON.parse(data);
    if (message.id) {
      const waiter = pending.get(message.id);
      if (waiter) { clearTimeout(waiter.timer); pending.delete(message.id); message.error ? waiter.reject(new Error(message.error.message)) : waiter.resolve(message.result); }
    } else if (message.method === "Runtime.exceptionThrown") failures.push(message.params.exceptionDetails.text);
    else if (message.method === "Log.entryAdded" && message.params.entry.level === "error" && !message.params.entry.url?.endsWith("/favicon.ico")) failures.push(message.params.entry.text);
    else if (message.method === "Network.responseReceived") responses.push(message.params);
    else if (message.method === "Network.requestWillBeSent") requests.push(message.params.request);
  });
  const { targetId } = await send("Target.createTarget", { url: "about:blank" }, null);
  ({ sessionId: session } = await send("Target.attachToTarget", { targetId, flatten: true }, null));
  for (const method of ["Page.enable", "Runtime.enable", "Network.enable", "Log.enable"]) await send(method);
  await send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 960, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: url.href });
  await waitFor(async () => (await text("#status"))?.includes("Play the sequence"), "initial replay");
  assert.equal(await evaluate("document.querySelectorAll('#players > g').length"), 22);
  assert.equal(await visible("#reveal"), false);
  assert(await evaluate("[...document.querySelectorAll('[data-option]')].every(el => el.disabled)"));
  const preludes = responses.filter((entry) => /\/api\/(start|sessions\/.+\/decision)$/.test(entry.response.url));
  assert.equal(preludes.length, 2);
  for (const entry of preludes) {
    const { body } = await send("Network.getResponseBody", { requestId: entry.requestId });
    for (const forbidden of ["continuation", "outcome", "scripted_option_id", "velocity_mps"]) assert(!body.includes(`"${forbidden}"`));
  }
  assert(!requests.some((entry) => entry.url.endsWith("/reveal")), "No early reveal request.");
  await noOverflow();
  await screenshot("keeper-loop-desktop.png");
  await click("#play");
  await waitFor(async () => (await text("#elapsed")) !== "0.0 s", "replay movement");
  await click("#play");
  assert.equal(await text("#status"), "Replay paused.");
  const paused = await text("#elapsed"); await pause(150); assert.equal(await text("#elapsed"), paused);
  await click("#skip");
  assert.equal(await text("#elapsed"), "2.0 s");
  assert(await evaluate("[...document.querySelectorAll('[data-option]')].every(el => !el.disabled)"));
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "2", code: "Digit2", text: "2" });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key: "2", code: "Digit2" });
  await waitFor(() => visible("#evidence"), "keyboard choice evidence");
  assert((await text("#status")).includes("Switch left"));
  assert.equal(await evaluate("document.querySelectorAll('.evidence-card').length"), 3);
  await auditWorkflow();
  await click("#analyst-view");
  assert(await visible("#analyst-details"));
  assert.equal(await evaluate("document.querySelectorAll('#observations tr').length"), 22);
  assert((await text("#timings")).includes("Not modelled"));
  const frozenIdentity = await text("#snapshot-id");
  await evaluate("document.querySelector('#evidence').scrollIntoView({block: 'start'})");
  await screenshot("keeper-loop-evidence.png");
  await click("#fan-view");
  assert.equal(await visible("#analyst-details"), false);
  assert.equal(requests.filter((entry) => entry.url.endsWith("/choice")).length, 1, "View changes must reuse evidence.");
  await revealAndPlay();
  await waitFor(() => visible("#recap"), "recorded continuation and recap");
  assert((await text("#recorded-outcome")).includes("completed"));
  assert((await text("#choice-context")).includes("does not simulate your choice"));
  assert.equal(await text("#snapshot-id"), frozenIdentity);
  await click("#revisit");
  assert.equal(await text("#elapsed"), "2.0 s");
  assert((await text("#status")).includes("unchanged"));
  assert(!(await evaluate("document.querySelector('#play').disabled")));
  await click("#skip");
  await click("#understanding > summary");
  await click('input[name="outcome"][value="separate"]');
  await click('input[name="margin"][value="model"]');
  await click('#understanding-form button[type="submit"]');
  assert((await text("#understanding-feedback")).includes("not a rating of your decision"));
  await click('input[name="outcome"][value="proof"]');
  await click('input[name="margin"][value="guarantee"]');
  await click('#understanding-form button[type="submit"]');
  assert((await text("#understanding-feedback")).includes("not a guarantee"));
  await noOverflow();

  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await click("#restart");
  await waitFor(async () => (await text("#status"))?.includes("Play the sequence"), "mobile new attempt");
  await click("#skip"); await click('[data-option="clear-long"]');
  await waitFor(() => visible("#evidence"), "aerial choice evidence");
  assert((await text("#evidence-cards .chosen")).includes("does not assess the aerial contest"));
  await revealAndPlay();
  await click("#skip"); assert(await visible("#recap"));
  await noOverflow();
  await evaluate("scrollTo(0, 0)"); await screenshot("keeper-loop-mobile.png");
  await click("#restart");
  await waitFor(async () => (await text("#status"))?.includes("Play the sequence"), "short-pass attempt");
  await click("#play");
  await waitFor(async () => (await text("#status"))?.startsWith("Choose an action"), "automatic decision freeze");
  await click('[data-option="short-right"]');
  await waitFor(() => visible("#evidence"), "short-pass evidence");
  await revealAndPlay();
  await click("#skip");
  assert((await text("#choice-context")).includes("shows your chosen action"));

  const choices = [], reveals = [];
  for (const entry of responses.filter((entry) => /\/(choice|reveal)$/.test(entry.response.url))) {
    const { body } = await send("Network.getResponseBody", { requestId: entry.requestId });
    (entry.response.url.endsWith("/choice") ? choices : reveals).push(JSON.parse(body));
  }
  assert.equal(choices.length, 3); assert.equal(reveals.length, 3);
  for (let i = 0; i < 3; i++) assert.deepEqual(choices[i].assessment, reveals[i].assessment);
  assert.equal(requests.filter((entry) => entry.url.endsWith("/reveal")).length, 3);

  for (const [scenario, option] of [["press-arrives", "take-touch"], ["uncertain-outlet", "switch-left"]]) {
    await evaluate(`(() => { const el = document.querySelector('#scenario'); el.value = ${JSON.stringify(scenario)}; el.dispatchEvent(new Event('change', {bubbles: true})); })()`);
    await waitFor(async () => (await text("#status"))?.includes("Play the sequence"), `${scenario} replay`);
    await click("#skip"); await click(`[data-option="${option}"]`);
    await waitFor(() => visible("#evidence"), `${scenario} evidence`);
    await auditWorkflow();
    if (scenario === "uncertain-outlet") {
      assert((await text("#evidence-cards")).includes("declines to compare"));
      assert.equal(await evaluate("document.querySelectorAll('#routes .uncertainty').length"), 1);
      assert((await text("#evidence-cards")).includes("Opponent 3"));
      assert((await text("#evidence-cards")).includes("6.5 m"));
      assert.equal(await visible("#route-audit"), false);
    } else {
      assert((await text("#pressure-evidence")).includes("pressure"));
      assert((await text('[data-option="take-touch"]')).includes("another touch"));
    }
    await noOverflow();
    await screenshot(`keeper-loop-${scenario}.png`);
    await revealAndPlay();
    if (scenario === "uncertain-outlet") {
      assert(await visible("#revealed-positions"));
      assert((await text("#revealed-positions")).includes("V03's actual position"));
      assert((await text("#revealed-positions")).includes("not visible at the decision"));
    }
    await click("#skip"); assert(await visible("#recap"));
  }
  assert(responses.every((entry) => entry.response.status < 400 || (entry.response.url.endsWith("/favicon.ico") && entry.response.status === 404)), "No unexpected HTTP resource failures.");
  assert.deepEqual(failures, [], "No browser exceptions, CSP or resource errors.");
  console.log(`PASS: ${version.Browser}; desktop/mobile, three scenarios, all initial choices, pressure, uncertainty, keyboard, pause/skip, immutable evidence, recap and comprehension feedback.`);
  console.log("Screenshots: local-artifacts/keeper-loop-{desktop,evidence,mobile}.png");
} catch (error) {
  console.error(browserLog.split("\n").filter((line) => /ERROR|FATAL/.test(line)).slice(-10).join("\n"));
  throw error;
} finally {
  if (socket?.readyState === WebSocket.OPEN) { try { await send("Browser.close", {}, null); } catch {} socket.close(); }
  if (!closed) { await pause(300); if (!closed) child.kill(); }
  // Only remove the isolated profile created by this script, after verifying containment.
  const profileRelative = relative(artifacts, resolve(profile));
  assert(profileRelative && !profileRelative.startsWith("..") && !resolve(profile).endsWith(artifacts), "Profile must stay inside local-artifacts.");
  try { await rm(profile, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 }); } catch {}
}
