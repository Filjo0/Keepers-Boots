# Keeper's Boots working rules

## Start small
- Read README.md, CODEBASE_MAP.md and the relevant task/document only.
- Current state belongs in tasks/01-keeper-loop.md. Update it in place.
- Use one scoped task card per later release or experiment.
- Keep frozen evaluation definitions separate from progress reports.
- Preserve other people's work; use separate worktrees for concurrent edits.
- Do not delegate to subagents unless explicitly requested or needed to isolate noisy output.

## Product invariants
- Three goalkeeper scenarios are the MVP. The midfielder information-age step is conditional.
- Facts are computed in code. Agents interpret and review evidence.
- Assessment uses only frozen available observations at or before the decision.
- World truth, unseen movement, continuation, hidden policies and outcome labels are not agent inputs.
- A completed pass is not automatically a good decision.
- Report scope and uncertainty. Do not invent completion probabilities or ideal-player ratings.
- Original principles are drafts until explicitly reviewed; never claim a coach reviewed them without evidence.
- Real scanning, stamina, calories, nutrition, injury prediction and betting are outside the MVP.

## Data and rights
- Use fictional teams and synthetic data with a documented generator.
- Do not access, copy, embed or upload the private Coach KB, books, embeddings or predictor data.
- Publicly readable material is not automatically licensed for redistribution.
- Link research and write original explanations. Check asset and dependency permissions.
- Never read or print .env secrets, tokens or credentials.
- No live sports providers, Telegram, paid model calls, Azure provisioning, public publishing or registration without task authorization.
- Do not modify generated scenario JSON directly; edit keepers_boots/scenario.py and regenerate.

## Validation
- Check CPU load, available/committed RAM, GPU memory/temperature where available and free disk with tools/check_resources.ps1 before heavy work, every 30-60 seconds during long jobs, and afterwards. For model loading use -Phase start -GpuRequiredMiB with the expected GPU allocation; the script's reserve is additional headroom. Model jobs require GPU metrics; ordinary CPU-only jobs on machines without an NVIDIA provider do not. On this laptop the provider remains present and its limits still apply.
- Defer heavy work on checker exit 2 or unavailable metrics. Task limits: at least 3 GiB available RAM before model loading and 2 GiB during work, below 90% committed memory, at least 5 GiB free disk, GPU below 80 C with reserved headroom, and no sustained CPU load at/above 95%. Stop only verified task processes; never close unrelated user apps. CPU temperature is not available from the configured provider, and these conservative checks cannot guarantee against crashes.
- Use the project virtual environment, not another project's environment.
- Narrow tests first, then the complete small local suite:
  .venv\Scripts\python.exe -m unittest discover -s tests -v
- Run .venv\Scripts\python.exe tools/check_docs.py after documentation changes.
- Run .venv\Scripts\python.exe -m keepers_boots for a real CLI smoke check.
- UI changes require runtime/browser verification. Azure changes require separate deployment evidence.
- Preserve no-hindsight, hidden-information, immutability and symmetry checks.
- Do not weaken assertions to make a changed model pass.
- Verify current Microsoft/MCP docs before selecting SDK versions. Record and pin the chosen versions.

## Completion
Report the outcome, files, validation, remaining limits and next step.
Distinguish implemented, locally tested, runtime verified, staged, deployed and production verified.
Avoid repeating the whole history or loading all Markdown files on every turn.
