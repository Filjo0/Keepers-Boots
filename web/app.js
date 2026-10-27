"use strict";

const $ = (id) => document.getElementById(id);
const labels = { "short-right": "Short right", "switch-left": "Switch left", "clear-long": "Clear long" };
const buttons = [...document.querySelectorAll("[data-option]")];
let run, decision, evidence, continuation;
let phase = "loading", mode = "fan", time = 0, animation = 0, lastTick = 0;
let busy = false;
let pollTimer = 0;
let pollExpired = false;
const phonePitch = matchMedia("(max-width: 780px)");
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");

function bringIntoView(id) {
  $(id).focus({ preventScroll: true });
  $(id).scrollIntoView({ block: "start", behavior: "auto" });
}

function optionArrow(origin, target) {
  const dx = Math.sign(target[0] - origin[0]), dy = Math.sign(target[1] - origin[1]);
  return ({ "1,1": "↘", "1,-1": "↗", "1,0": "→", "-1,1": "↙", "-1,-1": "↖", "-1,0": "←", "0,1": "↓", "0,-1": "↑" })[[dx, dy].join(",")] || "•";
}

function groupedRoutes(options) {
  const groups = new Map();
  options.forEach((option, index) => {
    const key = JSON.stringify([option.kind, option.target_m]);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push({ option, number: index + 1 });
  });
  return [...groups.values()];
}

async function request(path, body) {
  const response = await fetch(path, body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed.");
  return data;
}

function endpoint(operation) { return `/api/sessions/${run.session_id}/${operation}`; }
function message(text) { $("status").textContent = text; }
function error(error) { $("error").textContent = error.message; $("error").hidden = false; }
function stop() { cancelAnimationFrame(animation); animation = 0; lastTick = 0; }
function node(tag, text, className) {
  const item = document.createElement(tag);
  if (text !== undefined) item.textContent = text;
  if (className) item.className = className;
  return item;
}
function svg(tag, attrs, text) {
  const item = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attrs)) item.setAttribute(key, value);
  if (text !== undefined) item.textContent = text;
  return item;
}

function controls() {
  for (const button of buttons) {
    button.disabled = phase !== "awaiting_choice" || busy;
    button.classList.toggle("chosen", evidence?.choice === button.dataset.option);
  }
  const canReplay = ["evidence_ready", "insufficient_evidence", "recap"].includes(phase);
  $("play").disabled = busy || (!canReplay && !["ready", "playing", "paused", "revealed", "reveal_paused"].includes(phase));
  $("play").textContent = ["playing", "revealed"].includes(phase) ? "Pause" : continuation ? phase === "recap" ? "Replay continuation" : "Play continuation" : evidence ? "Replay build-up" : "Play sequence";
  $("skip").disabled = busy || (!canReplay && !["ready", "playing", "paused", "revealed", "reveal_paused"].includes(phase));
  $("skip").textContent = continuation ? "Skip to recap" : "Skip to decision";
  $("restart").disabled = busy;
  $("scenario").disabled = busy;
  $("fan-view").disabled = busy || !evidence;
  $("analyst-view").disabled = busy || !evidence;
  $("reveal").hidden = !evidence || !!continuation;
  $("reveal").disabled = busy;
  $("revisit").hidden = !continuation;
  $("revisit").disabled = busy;
}

function frameAt(frames, t) {
  let index = 0;
  while (index + 1 < frames.length && frames[index + 1].t_ms <= t) index++;
  const a = frames[index], b = frames[Math.min(index + 1, frames.length - 1)];
  const f = a.t_ms === b.t_ms ? 0 : Math.max(0, Math.min(1, (t - a.t_ms) / (b.t_ms - a.t_ms)));
  const blend = (p, q) => p.map((value, axis) => value + f * (q[axis] - value));
  const next = new Map(b.players.map((item) => [item.player_id, item.position_m]));
  return { players: a.players.map((item) => ({ player_id: item.player_id, position_m: blend(item.position_m, next.get(item.player_id)) })),
    ball: { position_m: blend(a.ball.position_m, b.ball.position_m) } };
}

function drawRoutes() {
  $("routes").replaceChildren();
  if (!decision || ["ready", "playing", "paused", "revealed", "reveal_paused", "recap"].includes(phase)) return;
  const [x, y] = decision.ball.position_m;
  for (const item of evidence?.assessment.uncertainty_regions || []) {
    $("routes").append(svg("circle", { cx: item.position_m[0] + 4, cy: item.position_m[1] + 4, r: item.radius_m, class: "uncertainty" }));
  }
  groupedRoutes(decision.options).forEach((group) => {
    const { option } = group[0];
    const [tx, ty] = option.target_m;
    const chosen = group.some((item) => evidence?.choice === item.option.option_id);
    const aerial = option.kind === "aerial";
    const route = svg("path", { d: aerial ? `M${x + 4} ${y + 4} Q${(x + tx) / 2 + 4} ${(y + ty) / 2 - 10} ${tx + 4} ${ty + 4}` : `M${x + 4} ${y + 4} L${tx + 4} ${ty + 4}`, class: `route${chosen ? " selected" : ""}${aerial ? " aerial" : ""}` });
    route.append(svg("title", {}, `${group.map((item) => labels[item.option.option_id]).join(" / ")}${aerial ? ": aerial flight not modelled" : ""}`));
    $("routes").append(route);
    $("routes").append(svg("text", { x: (x + tx) / 2 + 4, y: (y + ty) / 2 + (aerial ? -4 : 3), class: "route-number" }, group.map((item) => item.number).join(" / ")));
  });
}

function draw() {
  if (!run) return;
  $("pitch").setAttribute("viewBox", phonePitch.matches ? "0 5 55 51" : "0 0 113 76");
  $("pitch-zoom").hidden = !phonePitch.matches;
  const oldObservations = decision.observations.filter((item) => item.observed_at_ms < run.decision_t_ms);
  const showingReveal = continuation && ["revealed", "reveal_paused", "recap"].includes(phase);
  $("revealed-positions").hidden = !showingReveal || !oldObservations.length;
  const captionText = showingReveal ? oldObservations.map((item) => `${item.player_id}'s actual position is revealed in this continuation; it was not visible at the decision.`).join(" ") : "";
  if ($("revealed-positions").textContent !== captionText) $("revealed-positions").textContent = captionText;
  const frames = continuation ? [...run.frames, ...continuation.frames] : run.frames;
  const frame = frameAt(frames, time);
  const teams = new Map(run.roster.map((item) => [item.player_id, item.team]));
  $("players").replaceChildren();
  for (const player of frame.players) {
    const [x, y] = player.position_m;
    const home = teams.get(player.player_id) === "H";
    const group = svg("g", { transform: `translate(${x + 4} ${y + 4})` });
    group.append(svg("title", {}, `${player.player_id}: ${x.toFixed(1)}, ${y.toFixed(1)} metres`));
    group.append(home ? svg("circle", { r: 1.3, class: "player-home" }) : svg("rect", { x: -1.3, y: -1.3, width: 2.6, height: 2.6, rx: .25, class: "player-away" }));
    if (player.player_id === "H01") group.append(svg("circle", { r: 1.75, class: "keeper-ring" }));
    group.append(svg("text", { class: "player-number" }, player.player_id.slice(1)));
    const observation = decision.observations.find((item) => item.player_id === player.player_id);
    if ((!continuation || time <= run.decision_t_ms) && observation.observed_at_ms < time) {
      group.append(svg("text", { x: 0, y: -2.6, class: "last-seen" }, "last seen"));
    }
    $("players").append(group);
  }
  $("ball").setAttribute("cx", frame.ball.position_m[0] + 4);
  $("ball").setAttribute("cy", frame.ball.position_m[1] + 4);
  $("elapsed").textContent = `${(time / 1000).toFixed(1)} s`;
  const seconds = Math.floor(run.match_context.match_clock_s + (time - run.decision_t_ms) / 1000);
  $("clock").textContent = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  $("progress").max = frames[frames.length - 1].t_ms;
  $("progress").value = time;
  drawRoutes();
}

async function start() {
  clearTimeout(pollTimer);
  stop(); busy = true; phase = "loading"; controls(); $("error").hidden = true;
  try {
    const nextRun = await request("/api/start", { scenario_id: $("scenario").value });
    const nextDecision = await request(`/api/sessions/${nextRun.session_id}/decision`);
    run = nextRun; decision = nextDecision.decision;
    evidence = null; continuation = null; time = 0; phase = "ready"; pollExpired = false;
    Object.assign(labels, run.labels);
    $("scenario-title").textContent = run.title;
    $("scenario-number").textContent = `SCENARIO ${String($("scenario").selectedIndex + 1).padStart(2, "0")} / KEEPER DISTRIBUTION`;
    decision.options.forEach((option, index) => {
      buttons[index].dataset.option = option.option_id;
      buttons[index].querySelector("strong").textContent = labels[option.option_id];
      buttons[index].querySelector("small").textContent = `${option.kind === "ground" ? "Ground pass" : "Aerial clearance"} toward ${option.target_player_id}${option.preparation_delay_s ? " · after another touch" : ""}${option.kind === "aerial" ? " · flight unmodelled" : ""}`;
      buttons[index].querySelector("[aria-hidden]").textContent = optionArrow(decision.ball.position_m, option.target_m);
    });
    for (const id of ["evidence", "recap"]) $(id).hidden = true;
    $("understanding-form").reset(); $("understanding-feedback").textContent = ""; $("understanding").open = false;
    $("home-name").textContent = run.teams.H; $("away-name").textContent = run.teams.V;
    $("score").textContent = `${run.match_context.home_goals} — ${run.match_context.away_goals}`;
    const seconds = run.match_context.match_clock_s;
    $("clock").textContent = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
    $("phase").textContent = "Before the decision";
    $("instruction").textContent = "Watch the approaching press. The sequence freezes before the keeper acts.";
    message("Play the sequence or skip to the decision."); draw();
  } catch (problem) { error(problem); phase = "error"; }
  finally { busy = false; controls(); }
}

function freeze(scroll = false) {
  stop(); time = run.decision_t_ms;
  phase = evidence ? (evidence.assessment.status === "insufficient_evidence" ? "insufficient_evidence" : "evidence_ready") : "awaiting_choice";
  $("phase").textContent = "Frozen · available observations";
  $("instruction").textContent = "The keeper has the ball. Which action would you choose?";
  message(evidence ? `Your first choice remains ${labels[evidence.choice]}. The evidence is unchanged.` : "Choose an action. There is no overall best-action score.");
  controls(); draw();
  if (scroll) bringIntoView("scenario-title");
  else $("scenario-title").focus({ preventScroll: true });
}

function recap() {
  stop(); phase = "recap";
  $("phase").textContent = "Recorded continuation · revealed";
  $("recap").hidden = false;
  for (const [id, field] of [["recorded-outcome", "recorded_outcome"], ["choice-context", "choice_context"], ["assessment-context", "assessment_context"]]) $(id).textContent = continuation.recap[field];
  message("Recorded outcome revealed. Your first assessment stays unchanged."); controls(); draw();
  bringIntoView("recap-title");
}

function tick(timestamp) {
  if (lastTick) time += timestamp - lastTick;
  lastTick = timestamp;
  const end = continuation ? continuation.frames[continuation.frames.length - 1].t_ms : run.decision_t_ms;
  if (time >= end) { time = end; continuation ? recap() : freeze(); return; }
  draw(); animation = requestAnimationFrame(tick);
}

function play() {
  if (["playing", "revealed"].includes(phase)) { stop(); phase = continuation ? "reveal_paused" : "paused"; message("Replay paused."); }
  else {
    if (["evidence_ready", "insufficient_evidence", "recap"].includes(phase)) time = continuation ? run.decision_t_ms : 0;
    phase = continuation ? "revealed" : "playing";
    message(continuation ? "Playing the recorded continuation." : "Watch the approaching press.");
    animation = requestAnimationFrame(tick);
  }
  controls();
}

const range = (values, signed = false) => values.map((value) => `${signed && value > 0 ? "+" : ""}${value.toFixed(3)}`).join(" to ");
function row(body, values) { const tr = node("tr"); for (const value of values) tr.append(node("td", value)); body.append(tr); }

function renderSource() {
  if (!evidence) return;
  const interpretation = evidence.interpretation || { status: "deterministic" };
  const recorded = interpretation.source === "recorded_agents";
  const date = recorded ? new Intl.DateTimeFormat("en-AU", { day: "numeric", month: "short", timeZone: "UTC" }).format(new Date(interpretation.recording.saved_at_utc)) : "";
  const fallback = interpretation.reason === "recording_unavailable" ? "Timing explanation · recording unavailable" : interpretation.reason === "review_not_accepted" ? "Timing explanation · AI draft not approved" : "Timing explanation · live AI unavailable";
  let label = "Timing explanation · no AI review";
  if (recorded) label = mode === "fan" ? `AI explanation recorded ${date} · numbers rechecked now` : `Recorded agent output · ${interpretation.model} · ${interpretation.recording.saved_at_utc}`;
  else if (pollExpired) label = "Stopped waiting for AI · timing evidence available";
  else if (interpretation.status === "running") label = "AI explanation in progress · timing evidence available";
  else if (interpretation.source === "local_agents") label = "Live AI explanation · reviewer checked";
  else if (interpretation.status === "fallback") label = fallback;
  $("explanation-source").textContent = label;
  $("recording-disclosure").hidden = !recorded;
  $("recording-disclosure").textContent = !recorded ? "" : mode === "fan" ? "This replays an earlier AI explanation. No new AI explanation is generated during this visit." : `Captured Microsoft analyst/reviewer run; no live agent, model or MCP calls in this mode. Capture saved ${interpretation.recording.saved_at_utc}; original run ${interpretation.elapsed_s.toFixed(3)} s. Numeric evidence is recomputed and matched to the capture.`;
}

function renderPressure(pressure) {
  $("pressure-timeline").replaceChildren();
  const available = pressure?.status === "model_evidence";
  $("pressure-section").hidden = !available;
  if (!available) return;
  const options = pressure.options.filter((item) => decision.options.find((option) => option.option_id === item.option_id)?.kind === "ground");
  const [earliest, latest] = pressure.arrival_after_decision_s;
  const end = Math.max(latest, ...options.map((item) => item.release_after_decision_s)) * 1.15;
  $("pressure-evidence").textContent = mode === "fan"
    ? "The shaded band is when the press could reach the keeper. The blue marker is when the ball leaves. A release before the band still does not guarantee the pass succeeds."
    : `Tested pressure arrival: ${range(pressure.arrival_after_decision_s)} s after the freeze. The shaded band shows that range; the blue marker shows ball release. These timings do not guarantee a completed pass.`;
  for (const item of options) {
    const text = `${labels[item.option_id]}: release at ${item.release_after_decision_s.toFixed(mode === "fan" ? 2 : 3)} s`;
    const entry = node("div", undefined, "pressure-row");
    entry.append(node("p", text));
    const track = node("div", undefined, "pressure-track");
    track.setAttribute("role", "img"); track.setAttribute("aria-label", `${text}; pressure reaches the keeper in ${range(pressure.arrival_after_decision_s)} s.`);
    const band = node("span", undefined, "pressure-band"), release = node("span", undefined, "release-marker");
    band.style.left = `${100 * earliest / end}%`; band.style.width = `${100 * (latest - earliest) / end}%`;
    release.style.left = `${100 * item.release_after_decision_s / end}%`;
    track.append(band, release); entry.append(track); $("pressure-timeline").append(entry);
  }
  $("pressure-timeline").append(node("p", `Same scale for both actions: 0 to ${end.toFixed(2)} s after the freeze.`, "quiet"));
}

function fanFinding(item) {
  if (item.status === "not_modelled") return "This model does not assess the aerial contest. It cannot compare this clearance with the ground passes.";
  if (item.finding === "interception_reachable_in_all_tested_parameter_combinations") return "A defender can get to the passing lane by the time the ball arrives, in every setting we tested. That is a possible interception, not a prediction of what happens next.";
  if (item.finding === "positive_margin_at_sampled_points_in_all_tested_parameter_combinations") return "The ball arrives before defenders at the points we checked, in every setting we tested. This gives it a timing lead in the model, without guaranteeing a completed pass.";
  if (item.finding === "finding_changes_with_assumptions") return "The timing finding changes when we change the tested speeds and reaction delays. This route does not have a consistent result across those settings.";
  return "The model cannot give a timing finding for this route.";
}

function renderAudienceEvidence() {
  const assessment = evidence.assessment;
  $("summary").textContent = mode === "analyst" ? evidence.explanation.analyst_summary || evidence.explanation.summary : evidence.explanation.summary;
  $("evidence-cards").replaceChildren();
  for (const item of assessment.options) {
    const card = node("article", undefined, `evidence-card${item.option_id === evidence.choice ? " chosen" : ""}`);
    card.append(node("h3", labels[item.option_id]));
    card.append(node("p", mode === "fan" ? fanFinding(item) : evidence.explanation.options.find((entry) => entry.option_id === item.option_id).text));
    if (mode === "analyst" && item.minimum_interception_margin_s) card.append(node("p", `Sampled margin: ${range(item.minimum_interception_margin_s, true)} s`, "quiet"));
    if (item.option_id === evidence.choice) card.append(node("p", "Your choice · retained", "quiet"));
    $("evidence-cards").append(card);
  }
  if (assessment.status === "insufficient_evidence") {
    for (const region of assessment.uncertainty_regions || []) {
      const text = mode === "fan"
        ? `Opponent ${region.player_id.replace(/^V0*/, "")} was last seen ${(region.age_ms / 1000).toFixed(1)} seconds before the freeze. The circle shows how far they could have moved (up to ${region.radius_m.toFixed(1)} m), not where they probably are.`
        : `${region.player_id} was last seen ${(region.age_ms / 1000).toFixed(1)} s before the freeze. The circle shows a ${region.radius_m.toFixed(1)} m movement bound, not a likely position.`;
      $("evidence-cards").append(node("article", text, "evidence-card"));
    }
    $("evidence-cards").append(node("article", "The model declines to compare the current ground routes. An updated opponent observation is needed for that comparison; the keeper still has to act.", "evidence-card"));
  }
  $("comparison-facts").hidden = mode !== "analyst";
  $("workflow-trace").hidden = mode !== "analyst" || !evidence.interpretation?.trace?.length;
  renderPressure(evidence.pressure);
}

function renderEvidence() {
  const assessment = evidence.assessment;
  $("evidence").hidden = false; $("summary").textContent = evidence.explanation.summary;
  const interpretation = evidence.interpretation || { status: "deterministic", trace: [] };
  const recorded = interpretation.source === "recorded_agents";
  const reviewed = recorded || interpretation.source === "local_agents";
  $("recording-notes").replaceChildren();
  for (const note of interpretation.recording?.notes || []) $("recording-notes").append(node("li", note));
  $("recording-notes").hidden = !recorded || !interpretation.recording.notes.length;
  $("workflow-trace").hidden = !interpretation.trace?.length;
  $("workflow-trace").querySelector("summary").textContent = recorded ? "Inspect the captured analyst/reviewer handoff" : "Inspect the analyst/reviewer handoff";
  $("trace-steps").replaceChildren();
  for (const step of interpretation.trace || []) $("trace-steps").append(node("li", `${step.stage} · ${step.status}: ${step.detail}`));
  $("reviewed-claims").hidden = !reviewed;
  $("claim-list").replaceChildren();
  if (reviewed) {
    for (const claim of interpretation.claims) {
      const item = node("li", `${claim.claim_id}: ${claim.text}`);
      item.append(node("p", `Evidence: ${claim.evidence_ids.join(", ")}${claim.principle_ids.length ? ` · Original draft principles: ${claim.principle_ids.join(", ")}` : ""}`, "hash"));
      $("claim-list").append(item);
    }
  }
  $("comparison-facts").textContent = (assessment.comparisons || []).map((item) => {
    let text = item.text;
    for (const optionId of item.option_ids) text = text.replaceAll(optionId, labels[optionId]);
    return `Modelled timing comparison · ${text}${item.margin_difference_s !== undefined ? ` Difference under matched assumptions: ${item.margin_difference_s.toFixed(3)} s.` : ""}`;
  }).join(" ");
  $("timings").replaceChildren(); $("limitations").replaceChildren(); $("observations").replaceChildren();
  for (const item of assessment.options) {
    row($("timings"), [labels[item.option_id], item.route_length_m.toFixed(3), item.receipt_after_decision_s ? range(item.receipt_after_decision_s) : "Not modelled", item.minimum_interception_margin_s ? range(item.minimum_interception_margin_s, true) : "Not modelled"]);
  }
  $("route-audit").hidden = assessment.options.length === 0;
  $("audit-abstention").hidden = assessment.status !== "insufficient_evidence";
  for (const limitation of assessment.limitations) $("limitations").append(node("li", limitation));
  const model = decision.model;
  $("assumptions").textContent = `Model ${assessment.model_version}. Release delay ${model.release_delay_s} s; defender speed ${range(model.defender_speed_mps)} m/s; reaction delay ${range(model.reaction_delay_s)} s; ${model.lane_samples} lane samples. All opponents included. Available observations are listed below.`;
  $("snapshot-id").textContent = `Snapshot: ${assessment.snapshot_id}`;
  $("evidence-ids").textContent = `Evidence: ${[...assessment.options, ...(assessment.comparisons || [])].map((item) => item.evidence_id).join(", ") || "observations:age"}`;
  for (const item of decision.observations) row($("observations"), [item.player_id, item.position_m.join(", "), item.observed_at_ms]);
  setMode(mode);
}

function setMode(next) {
  mode = next;
  $("fan-view").setAttribute("aria-pressed", mode === "fan"); $("analyst-view").setAttribute("aria-pressed", mode === "analyst");
  $("analyst-details").hidden = mode !== "analyst";
  $("evidence").setAttribute("data-audience", mode);
  $("evidence-title").textContent = mode === "fan" ? "Read the passing lanes" : "Audit the frozen evidence";
  $("audience-note").textContent = mode === "fan"
    ? "Fan view · a quick read of the passing lanes. The cards explain what to notice, without the timing audit."
    : "Analyst view · inspect timing ranges, assumptions, observation ages and the analyst/reviewer handoff. The frozen evidence and your choice stay the same.";
  if (evidence) renderAudienceEvidence();
  renderSource();
}

function pollInterpretation(sessionId, attempts = 0) {
  if (evidence?.interpretation?.status !== "running") return;
  if (attempts >= 200) { pollExpired = true; renderSource(); return; }
  pollTimer = setTimeout(async () => {
    try {
      const next = await request(`/api/sessions/${sessionId}/evidence`);
      if (run.session_id !== sessionId) return;
      evidence = next; renderEvidence(); draw(); pollInterpretation(sessionId, attempts + 1);
    } catch {
      // Retry within the same bounded polling budget; never start another generation job.
      if (run?.session_id === sessionId) pollInterpretation(sessionId, attempts + 1);
    }
  }, 3000);
}

async function choose(optionId) {
  if (phase !== "awaiting_choice" || busy) return;
  busy = true; phase = "assessing"; controls(); message("Calculating evidence from the frozen observations…"); $("error").hidden = true;
  try {
    evidence = await request(endpoint("choice"), { option_id: optionId });
    phase = evidence.assessment.status === "insufficient_evidence" ? "insufficient_evidence" : "evidence_ready";
    renderEvidence(); message(`You chose ${labels[optionId]}. Inspect the evidence before revealing the recording.`); draw();
    pollInterpretation(run.session_id);
    bringIntoView("evidence-title");
  } catch (problem) { error(problem); phase = "awaiting_choice"; }
  finally { busy = false; controls(); }
}

async function reveal() {
  if (busy || !evidence || continuation) return;
  busy = true; controls(); $("error").hidden = true;
  try {
    continuation = await request(endpoint("reveal"), {});
    time = run.decision_t_ms; phase = reducedMotion.matches ? "reveal_paused" : "revealed";
    $("phase").textContent = "Recorded continuation · revealed";
    message(reducedMotion.matches ? "Continuation ready. Press Play continuation to watch it; reduced motion pauses automatic playback." : "Playing the recorded continuation. This is not a simulation of a different choice.");
    draw(); bringIntoView("replay-view");
    if (!reducedMotion.matches) animation = requestAnimationFrame(tick);
  } catch (problem) { error(problem); }
  finally { busy = false; controls(); }
}

$("play").addEventListener("click", play);
$("skip").addEventListener("click", () => { if (continuation) { time = continuation.frames.at(-1).t_ms; recap(); } else freeze(true); });
$("restart").addEventListener("click", start);
$("scenario").addEventListener("change", start);
$("revisit").addEventListener("click", () => freeze(true));
$("reveal").addEventListener("click", reveal);
$("fan-view").addEventListener("click", () => setMode("fan"));
$("analyst-view").addEventListener("click", () => setMode("analyst"));
phonePitch.addEventListener("change", draw);
for (const button of buttons) button.addEventListener("click", () => choose(button.dataset.option));
document.addEventListener("keydown", (event) => {
  if (event.altKey || event.ctrlKey || event.metaKey || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName)) return;
  const index = ["1", "2", "3"].indexOf(event.key);
  if (index >= 0 && phase === "awaiting_choice") { event.preventDefault(); choose(buttons[index].dataset.option); }
});
$("understanding-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const answers = new FormData(event.currentTarget);
  const outcome = answers.get("outcome") === "separate" ? "You separated outcome from evidence." : "Keep outcome and evidence separate.";
  const margin = answers.get("margin") === "model" ? "You kept the timing finding within its model scope." : "A positive margin is a finding at sampled points, not a guarantee.";
  $("understanding-feedback").textContent = `${outcome} A completed pass does not prove the choice was best. ${margin} This is a check of the explanation, not a rating of your decision.`;
});
start();
