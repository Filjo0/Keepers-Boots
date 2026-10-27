/** Small DOM doubles exercise app behaviour; these do not verify browser layout. */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const html = readFileSync(new URL("../web/index.html", import.meta.url), "utf8");
const source = readFileSync(new URL("../web/app.js", import.meta.url), "utf8");
assert.match(source, /\nstart\(\);\s*$/);
const script = new vm.Script(source.replace(/\nstart\(\);\s*$/, ""));
const scenario = (name) => JSON.parse(readFileSync(new URL(`../data/scenarios/${name}.json`, import.meta.url), "utf8"));

class Element {
  constructor(tag = "div") {
    this.tag = tag; this.children = []; this.attributes = {}; this.style = {}; this.dataset = {};
    this.textContent = ""; this.hidden = false; this.disabled = false;
    this.classList = { toggle() {} };
  }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  addEventListener() {}
  focus() { this.focused = true; }
  scrollIntoView() { this.scrolled = true; }
  querySelector(selector) {
    this.selectors ??= {};
    return this.selectors[selector] ??= new Element(selector);
  }
}

function app(filename = "01-tempting-short-pass") {
  const elements = new Map([...html.matchAll(/\bid="([^"]+)"/g)].map((item) => [item[1], new Element()]));
  const buttons = Array.from({ length: 3 }, () => new Element("button"));
  const document = {
    getElementById(id) { assert(elements.has(id), `Unknown HTML id: ${id}`); return elements.get(id); },
    querySelectorAll() { return buttons; },
    createElement: (tag) => new Element(tag), createElementNS: (_, tag) => new Element(tag), addEventListener() {},
  };
  const context = vm.createContext({ document, console, matchMedia: () => ({ matches: false, addEventListener() {} }),
    requestAnimationFrame() { context.animations++; return 1; }, cancelAnimationFrame() {},
    setTimeout() { context.timers++; return 1; }, clearTimeout() {}, animations: 0, timers: 0,
    fetch() { throw new Error("Unexpected network access in unit test"); },
  });
  script.runInContext(context);
  const data = scenario(filename);
  const run = { ...data, frames: data.world_frames.filter((frame) => frame.t_ms <= data.decision.t_ms),
    decision_t_ms: data.decision.t_ms, match_context: data.decision.match_context };
  const execute = (code) => vm.runInContext(code, context);
  execute(`run = ${JSON.stringify(run)}; decision = ${JSON.stringify(data.decision)}; evidence = null; continuation = null; time = 2000; phase = 'awaiting_choice'; Object.assign(labels, ${JSON.stringify({ "take-touch": "Touch, then pass", "release-short": "Release short" })});`);
  data.decision.options.forEach((option, index) => { buttons[index].dataset.option = option.option_id; });
  return { context, elements, execute, data };
}

const plain = (element) => [element.textContent, ...element.children.map(plain)].join(" ");
const staleEvidence = {
  choice: "switch-left", assessment: { status: "insufficient_evidence", model_version: "point-arrival-v0.1",
    snapshot_id: "test", options: [], comparisons: [], limitations: [], stale_observation_ids: ["V03"],
    uncertainty_regions: [{ player_id: "V03", age_ms: 1000, radius_m: 6.5, position_m: [31, 21] }] },
  explanation: { summary: "An updated observation is needed.", analyst_summary: "Old observation prevents comparison.", options: [] },
  pressure: { status: "insufficient_evidence" }, interpretation: { status: "deterministic", trace: [] },
};

test("arrows follow pitch coordinates, including both identical short routes", () => {
  const { execute } = app();
  assert.equal(execute("optionArrow([8, 34], [19, 46])"), "↘");
  assert.equal(execute("optionArrow([8, 34], [24, 12])"), "↗");
  const press = app("02-the-press-arrives");
  assert.equal(press.execute("decision.options.slice(0, 2).map(item => optionArrow(decision.ball.position_m, item.target_m)).join(' ')"), "↘ ↘");
});

test("coincident actions share one labelled route; aerial route is distinct", () => {
  const { execute, elements } = app("02-the-press-arrives");
  execute("evidence = { choice: 'take-touch', assessment: {} }; drawRoutes()");
  const routes = elements.get("routes").children;
  assert.equal(routes.filter((item) => item.tag === "path").length, 2);
  assert.equal(routes[1].textContent, "1 / 2");
  assert.match(routes[0].attributes.class, /selected/);
  assert.match(routes[2].attributes.d, /Q/);
  assert.match(plain(routes[2]), /not modelled/);
});

test("pressure timeline shares a scale and places the extra touch inside the arrival band", () => {
  const { execute, elements } = app("02-the-press-arrives");
  execute(`mode = 'analyst'; renderPressure({status:'model_evidence', arrival_after_decision_s:[0.7,1.15], options:[
    {option_id:'take-touch',release_after_decision_s:0.95},
    {option_id:'release-short',release_after_decision_s:0.30}]})`);
  const rows = elements.get("pressure-timeline").children;
  const [band, touch] = rows[0].children[1].children;
  const [otherBand, release] = rows[1].children[1].children;
  assert.equal(band.style.left, otherBand.style.left);
  const left = parseFloat(band.style.left), right = left + parseFloat(band.style.width);
  assert(parseFloat(release.style.left) < left);
  assert(parseFloat(touch.style.left) > left && parseFloat(touch.style.left) < right);
  assert.match(plain(rows[0]), /0\.950 s/);
  assert.equal(elements.get("pressure-section").hidden, false);
  const first = app();
  first.execute("renderPressure({status:'model_evidence',arrival_after_decision_s:[1,2],options:[]})");
  assert.equal(first.elements.get("pressure-section").hidden, false, "Scenario 1 must expose its pressure evidence too");
});

test("stale evidence shows age and movement bound instead of an empty audit table", () => {
  const { execute, elements } = app("03-uncertain-outlet");
  execute(`mode = 'analyst'; evidence = ${JSON.stringify(staleEvidence)}; renderEvidence()`);
  assert.match(plain(elements.get("evidence-cards")), /V03.*1\.0 s.*6\.5 m/);
  assert.match(plain(elements.get("evidence-cards")), /keeper still has to act/);
  assert.equal(elements.get("route-audit").hidden, true);
  assert.equal(elements.get("audit-abstention").hidden, false);
  assert.match(elements.get("evidence-ids").textContent, /observations:age/);
  execute("draw()");
  assert.match(plain(elements.get("players")), /last seen/);
});

test("fan recording disclosure is plain; analyst view retains full provenance", () => {
  const { execute, elements } = app();
  execute(`evidence = ${JSON.stringify(staleEvidence)}; evidence.interpretation = {
    source:'recorded_agents',status:'reviewed',model:'example-model',elapsed_s:86,
    recording:{saved_at_utc:'2026-10-12T08:00:00Z'}}; setMode('fan')`);
  assert.match(elements.get("explanation-source").textContent, /recorded 12 Oct.*rechecked now/);
  assert.doesNotMatch(elements.get("explanation-source").textContent, /example-model/);
  assert.doesNotMatch(elements.get("recording-disclosure").textContent, /MCP/);
  execute("setMode('analyst')");
  assert.match(elements.get("explanation-source").textContent, /example-model/);
  assert.match(elements.get("recording-disclosure").textContent, /no live agent, model or MCP calls/);
});

test("audience views change the visible findings and audit without changing the choice or evidence", () => {
  const { execute, elements } = app();
  const detail = {
    ...staleEvidence, choice: "switch-left",
    assessment: { ...staleEvidence.assessment, status: "model_evidence", options: [
      { option_id: "short-right", status: "model_evidence", finding: "interception_reachable_in_all_tested_parameter_combinations",
        route_length_m: 16.279, receipt_after_decision_s: [1.317, 1.657], minimum_interception_margin_s: [-1.163, -0.470] },
      { option_id: "switch-left", status: "model_evidence", finding: "positive_margin_at_sampled_points_in_all_tested_parameter_combinations",
        route_length_m: 27.203, receipt_after_decision_s: [1.660, 2.000], minimum_interception_margin_s: [0.673, 1.719] },
      { option_id: "clear-long", status: "not_modelled", route_length_m: 35.511 },
    ] },
    explanation: { summary: "Unedited fan draft.", analyst_summary: "Unedited analyst draft.", options: [
      { option_id: "short-right", text: "Original short-route technical explanation." },
      { option_id: "switch-left", text: "Original wide-route technical explanation." },
      { option_id: "clear-long", text: "Original unmodelled-route explanation." },
    ] },
    interpretation: { status: "reviewed", source: "local_agents", claims: [], trace: [
      { stage: "reviewer", status: "accepted", detail: "Checked frozen evidence." },
    ] },
  };
  execute(`evidence = ${JSON.stringify(detail)}; renderEvidence()`);
  const frozen = execute("JSON.stringify(evidence)");
  const fanCards = plain(elements.get("evidence-cards"));
  assert.match(fanCards, /defender can get to the passing lane/);
  assert.match(fanCards, /ball arrives before defenders/);
  assert.match(fanCards, /does not assess the aerial contest/);
  assert.doesNotMatch(fanCards, /Sampled margin|0\.673|technical explanation/);
  assert.equal(elements.get("summary").textContent, detail.explanation.summary);
  assert.equal(elements.get("analyst-details").hidden, true);
  assert.equal(elements.get("workflow-trace").hidden, true);
  assert.equal(elements.get("comparison-facts").hidden, true);
  assert.match(elements.get("audience-note").textContent, /Fan view.*quick read/);
  execute("setMode('analyst')");
  assert.match(plain(elements.get("evidence-cards")), /technical explanation.*Sampled margin.*0\.673/);
  assert.equal(elements.get("summary").textContent, detail.explanation.analyst_summary);
  assert.equal(elements.get("analyst-details").hidden, false);
  assert.equal(elements.get("workflow-trace").hidden, false);
  assert.equal(elements.get("comparison-facts").hidden, false);
  assert.match(elements.get("evidence-title").textContent, /Audit/);
  execute("setMode('fan')");
  assert.equal(plain(elements.get("evidence-cards")), fanCards);
  assert.equal(execute("JSON.stringify(evidence)"), frozen);
  assert.equal(execute("evidence.choice"), "switch-left");
  assert.equal(execute("continuation"), null);
});

test("fan uncertainty explains the missing observation while analyst view identifies it precisely", () => {
  const { execute, elements } = app("03-uncertain-outlet");
  execute(`evidence = ${JSON.stringify(staleEvidence)}; renderEvidence()`);
  assert.match(plain(elements.get("evidence-cards")), /Opponent 3.*1\.0 seconds.*6\.5 m/);
  assert.match(plain(elements.get("evidence-cards")), /not where they probably are/);
  assert.match(plain(elements.get("evidence-cards")), /keeper still has to act/);
  execute("setMode('analyst')");
  assert.match(plain(elements.get("evidence-cards")), /V03.*1\.0 s.*6\.5 m movement bound/);
  assert.equal(execute("evidence.assessment.status"), "insufficient_evidence");
  assert.equal(elements.get("route-audit").hidden, true);
});

test("freeze and choice bring their payoff into view; replay retains the first choice", async () => {
  const { execute, elements, context } = app("03-uncertain-outlet");
  execute("freeze(true)");
  assert(elements.get("scenario-title").focused && elements.get("scenario-title").scrolled);
  assert.equal(elements.get("analyst-view").disabled, true);
  context.fetch = async () => ({ ok: true, json: async () => structuredClone(staleEvidence) });
  await execute("choose('switch-left')");
  assert.equal(elements.get("analyst-view").disabled, false);
  assert(elements.get("evidence-title").focused && elements.get("evidence-title").scrolled);
  assert.equal(elements.get("revisit").hidden, true);
  assert.equal(elements.get("play").disabled, false);
  execute("play()");
  assert.equal(execute("time"), 0);
  execute("freeze()");
  assert.equal(execute("evidence.choice"), "switch-left");
  assert.equal(execute("continuation"), null);
});

test("automatic freeze preserves the pitch viewport; explicit navigation scrolls", () => {
  const { execute, elements } = app();
  execute("phase = 'playing'; time = 1900; tick(1000); tick(1200)");
  assert.equal(execute("phase"), "awaiting_choice");
  assert.equal(execute("time"), 2000);
  assert.equal(elements.get("scenario-title").scrolled, undefined);
  assert.equal(elements.get("scenario-title").focused, true);
  execute("freeze(true)");
  assert.equal(elements.get("scenario-title").scrolled, true);
});

test("reduced motion allows explicit playback and pauses reveal without skipping it", async () => {
  const { execute, elements, context, data } = app("03-uncertain-outlet");
  execute("reducedMotion.matches = true; phase = 'ready'; time = 0; play()");
  assert.equal(context.animations, 1);
  assert.equal(execute("phase"), "playing");
  execute("tick(1000); tick(1100)");
  assert.equal(execute("time"), 100);
  assert.equal(execute("phase"), "playing");
  execute(`freeze(); evidence = ${JSON.stringify(staleEvidence)}`);
  context.fetch = async () => ({ ok: true, json: async () => ({ frames: data.world_frames.filter((frame) => frame.t_ms > 2000),
    recap: { recorded_outcome: "Wide pass completed.", choice_context: "Your choice.", assessment_context: "Unchanged." } }) });
  const animationsBeforeReveal = context.animations;
  await execute("reveal()");
  assert.equal(context.animations, animationsBeforeReveal);
  assert.equal(execute("phase"), "reveal_paused");
  assert.equal(execute("time"), 2000);
  assert.equal(elements.get("play").textContent, "Play continuation");
  assert.equal(elements.get("play").disabled, false);
  assert.match(elements.get("status").textContent, /Press Play continuation/);
  execute("play(); tick(1000); tick(1100)");
  assert.equal(execute("phase"), "revealed");
  assert.equal(execute("time"), 2100);
  execute("tick(4200)");
  assert.equal(execute("phase"), "recap");
  assert(elements.get("recap-title").focused && elements.get("recap-title").scrolled);
  assert.equal(elements.get("play").disabled, false);
});

test("unseen-position caption appears only in the revealed continuation", () => {
  const { execute, elements, data } = app("03-uncertain-outlet");
  const caption = elements.get("revealed-positions");
  let captionText = caption.textContent, writes = 0;
  Object.defineProperty(caption, "textContent", {
    get: () => captionText,
    set: (value) => { captionText = value; writes++; },
  });
  execute(`evidence = ${JSON.stringify(staleEvidence)}; draw()`);
  assert.equal(elements.get("revealed-positions").hidden, true);
  assert.equal(elements.get("revealed-positions").textContent, "");
  execute(`continuation = {frames:${JSON.stringify(data.world_frames.filter((frame) => frame.t_ms > 2000))}}; phase = 'reveal_paused'; draw()`);
  assert.equal(elements.get("revealed-positions").hidden, false);
  assert.match(elements.get("revealed-positions").textContent, /V03's actual position.*not visible at the decision/);
  const writesAtReveal = writes;
  execute("time = 2100; draw(); time = 2200; draw()");
  assert.equal(writes, writesAtReveal, "Unchanged live-region text must not be rewritten each frame");
  execute("freeze()");
  assert.equal(elements.get("revealed-positions").hidden, true);
  assert.equal(caption.textContent, "");
  assert.equal(writes, writesAtReveal + 1, "Revisiting clears the caption once");
  execute("draw()");
  assert.equal(writes, writesAtReveal + 1);
});

test("animated reveal scrolls to the pitch, keeping the clip in view", async () => {
  const { execute, elements, context, data } = app("03-uncertain-outlet");
  execute(`evidence = ${JSON.stringify(staleEvidence)}`);
  context.fetch = async () => ({ ok: true, json: async () => ({ frames: data.world_frames.filter((frame) => frame.t_ms > 2000) }) });
  await execute("reveal()");
  assert.equal(context.animations, 1);
  assert(elements.get("replay-view").focused && elements.get("replay-view").scrolled);
  assert.equal(elements.get("controls").scrolled, undefined);
});

test("phone crop contains all choices and the clock follows replay time", () => {
  const { execute, elements, data } = app();
  execute("phonePitch.matches = true; time = 0; draw()");
  assert.equal(elements.get("clock").textContent, "71:58");
  const [x, y, width, height] = elements.get("pitch").attributes.viewBox.split(" ").map(Number);
  for (const point of [data.decision.ball.position_m, ...data.decision.options.map((item) => item.target_m)]) {
    assert(point[0] + 4 > x && point[0] + 4 < x + width);
    assert(point[1] + 4 > y && point[1] + 4 < y + height);
  }
  execute("time = 2000; draw()");
  assert.equal(elements.get("clock").textContent, "72:00");
});

test("exhausted polling visibly stops waiting without starting another request", () => {
  const { execute, elements, context } = app();
  execute("evidence = {interpretation:{status:'running'}}; pollInterpretation('test', 200)");
  assert.equal(context.timers, 0);
  assert.match(elements.get("explanation-source").textContent, /Stopped waiting for AI/);
});
