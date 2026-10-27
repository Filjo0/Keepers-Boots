# Install and operations

The budget is A$0, set by the user on 2026-10-10. Run locally using [README](../README.md). No billable calls, Azure resources or public hosting have been created.

## Dependencies and inference

Python 3.12 runs the deterministic CLI/browser without extra packages. Install requirements.txt into this project's environment for MCP, Microsoft Agent Framework and complete tests. Top-level choices are in requirements.in. Run `python -m pip check`; do not use another project's environment.

Start an existing OpenAI-compatible local inference server separately. `--agents local`, `--model` and `--model-endpoint` enable the Microsoft workflow. Defaults are Gemma via llama.cpp at http://127.0.0.1:8088/v1; an available Qwen server can be selected explicitly. Only anonymous loopback HTTP is permitted. No weights are bundled or automatically downloaded, and no private Coach KB is queried. A source default is not evidence of the last-used model.

Inference is serial across the scenarios, with one cached interpretation each per process. The workflow permits one repair, a 180-second generation deadline and a 90-second provider timeout without retries. Deterministic evidence stays available while queued/running and after failure. Restarting clears sessions and caches. No analytics are sent.
Recorded mode is the recommended inspection path; live inference is experimental. For judges choosing live mode, allow up to three minutes per admitted scenario job, plus serial queue time. Of the last three documented scenario 1 jobs, one completed at 86.031 seconds and two returned ChatClientException fallbacks after 98.516 and 99.204 seconds. These counts span changed prompts and are not an estimated general failure rate. Earlier successful cold observations ranged from 21-86 seconds. Prompt changes, generated output, caching and machine load were not controlled, so no cause or typical wait is established. Recorded mode requires no model calls.

Read-only diagnosis on 13 October found two cancelled requests at the end of the saved model log. The saved API captures contain only the outer ChatClientException class; no nested exception or request-correlated timing was retained. Cancellation is consistent with a timeout but does not establish one, or that prompt length caused it. Before another live trial, capture safe error categories and per-stage timing locally without logging prompts, provider error text, URLs or credentials. Do not simply extend timeouts and claim reliability improved.

The bounded Phi follow-up stopped after three additional scenario 1 jobs (40.484, 57.297 and 50.657 seconds), all ending in review_not_accepted. tools/captured_agent_server.py preserves ordered SDK text/value drafts and reviews before project checks in ignored local-artifacts/phi-trial. Two runs used the unchanged prompt; the third tried an explicit status instruction. Unsupported earlier-release/safety wording remained, despite code-check acceptance. No Phi scenarios 2/3 runs or recording replacement followed; the original Gemma prompt/default remains. These are calibration probes, not quality or latency benchmarks.

## Phone on the same Wi-Fi

Find the laptop's Wi-Fi IPv4 address (for example with ipconfig), then run this from the project root after the resource gate passes. Replace the example address with the actual one:

~~~powershell
.\.venv\Scripts\python.exe tools/run_supervised.py --timeout 900 -- .\.venv\Scripts\python.exe -m keepers_boots.api --agents recorded --lan-ip 192.168.1.248
~~~

Open http://192.168.1.248:8000 on the phone using the same Wi-Fi. The laptop serves the replay and recorded explanations; no model or laptop browser is required. Keep the launcher running during the test, then stop it with Ctrl+C. Its 900-second deadline also closes the owned server. The chosen IP must belong to the laptop, may change after reconnecting, and must be reachable from the phone; guest-network isolation or Windows Firewall can prevent access. No firewall rules, network profiles, router settings or public hosting are changed automatically. Host/Origin protections remain enforced; --lan-ip works only with recorded mode and cannot be combined with --host. Binding 0.0.0.0 alone is not a supported phone path.

## Laptop resource limits

Use the Windows-only supervisor for one workload at a time:

~~~powershell
.\.venv\Scripts\python.exe tools/run_supervised.py --timeout 180 -- .\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools/run_supervised.py --timeout 900 -- .\.venv\Scripts\python.exe -m keepers_boots.api --agents recorded
~~~

Stop the launcher with Ctrl+C after the browser session. It holds Global\KeepersBoots.SupervisedWorkload.v1, a Windows named mutex shared across checkouts and sessions. Access failures refuse the job; no permissions are broadened. Checks run before starting, every 30 seconds while running and after cleanup, with a deadline. A failed/unavailable check stops only its Windows job and descendants. The workload waits for job assignment before starting; closing the supervisor's last job handle also terminates its job. Child processes run below normal priority. No shell is used. Do not run a workload that requires interactive stdin. Model loads additionally require --model --gpu-required-mib with the expected allocation, excluding the checker's reserve, and an explicit --max-memory-mib budget. Running checks use measured GPU usage rather than reserving the allocation twice. Ordinary tests and recorded mode work without an NVIDIA provider; GPU checks remain enforced wherever that provider is present, and model jobs always require it.

Use it around the complete workload tree; a second supervised launcher inside it will be refused. Unrelated/manual applications and external service daemons such as Docker are outside its owned tree. --max-memory-mib applies a Windows job-wide committed-memory cap: 1024 MiB by default for ordinary jobs, explicitly chosen for model jobs. Allocation failures can make the workload fail. This is not a cap on total physical RAM, GPU memory or file-backed mapped model weights; sampled CPU/GPU/RAM monitoring and reserved headroom remain necessary. Checks time out after 20 seconds and can delay deadline detection. Logs contain resource readings, not command arguments or environment values. A model's actual RAM footprint must fit in addition to the 3 GiB minimum preflight gate. No model is started by the examples above, and no crash guarantee is claimed. See [Windows job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) and [job committed-memory limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information).

Use tools/check_resources.ps1 before heavy work, during long jobs every 30-60 seconds and afterwards. For a model load, use -Phase start -GpuRequiredMiB with its expected allocation; the checker adds reserved GPU headroom. Defer heavy work for any nonzero exit or unavailable metrics. Conservative task limits are 3 GiB available RAM before loading and 2 GiB during work, under 90% committed memory, 5 GiB free disk, GPU temperature below 80 C, at least 512 MiB GPU reserve before loading and 256 MiB during work, and no CPU load at/above 95% in all three samples. These are task safeguards, not manufacturer limits. CPU temperature is unavailable through the configured provider; utilisation is not a temperature reading.

On 14 October, a check found 0.56 GiB available RAM and 92% committed memory, so heavy work and model restart were deferred. GPU usage was 220/4096 MiB at 73 C, and disk free space was 21.8 GiB. Known task API/model ports were already clear. Current live servers are not assumed to be running; start only after checking resources. A checkpoint or monitor cannot guarantee the laptop will not crash. Never stop unrelated user applications.

A later light check found 2.29 GiB available RAM, 87% committed memory, CPU mean 93%, GPU 226/4096 MiB at 73 C and 21.74 GiB free disk. This clears the running/check RAM floor but remains below the 3 GiB model-loading floor; no model was restarted.

The supervisor prints job_memory with peak_committed_mib, cap_mib and near_cap immediately before closing the owned job. At 90% of the cap or higher it warns of possible allocation pressure without changing the workload exit code. A failed query is labelled unavailable and cannot suppress cleanup or replace the primary stop reason. This is a diagnostic clue, not proof of a cap-triggered failure: a large refused request can leave the peak well below the cap. The reading covers Windows job commitment, not total physical RAM or GPU usage. Do not raise the cap solely to make a failing test pass.

## Portable container preparation

Dockerfile includes dependencies, application code, browser assets, schema, original principles and data/agent-recordings. It defaults to labelled recorded mode as a non-root user with a `/health` check. .dockerignore includes only the recording directory from data; calibration/evaluation data, scenario fixtures, weights, private files, local artifacts and credentials stay excluded. The exception syntax was checked against the [Docker build-context documentation](https://docs.docker.com/build/concepts/context/#dockerignore-files).

~~~powershell
docker build -t keepers-boots:local .
docker run --rm -p 127.0.0.1:8000:8000 keepers-boots:local
~~~

Docker is unavailable here: the definition is prepared, not built or runtime verified. Run those commands and the browser smoke before claiming container verification. Container inference needs a separately designed local network route; do not relax the loopback guard. The default/container Host policy accepts only localhost/127.0.0.1 at the application port. Explicit phone mode accepts only its selected private IPv4 host. Neither is a public deployment configuration.

## Cloud and public release

Azure Container Apps and Foundry can involve charges. Free allocations do not guarantee A$0; no provisioning is authorised under the current budget. A no-charge public route needs separate configuration and runtime evidence.

The user registered. Public repository, video, submission and publication license remain pending. Follow [rights](RIGHTS_AND_SOURCES.md) before release. Public access needs its own host/origin policy and abuse controls. Local tests do not prove deployment.

## Public-repository checks

[The workflow](../.github/workflows/checks.yml) runs on push, pull request and manual dispatch using a standard Windows runner and Python 3.12. Official [checkout](https://github.com/actions/checkout) and [setup-python](https://github.com/actions/setup-python) v7 tags were resolved to pinned commit hashes on 13 October. It uses read-only repository permissions, disables persisted checkout credentials, skips private repositories, has a ten-minute job limit, and uses no model services, caches or artifact uploads. GitHub documents [free standard hosted runners for public repositories](https://docs.github.com/en/billing/concepts/product-billing/github-actions); larger runners are not selected. Local commands passed; no GitHub run is claimed before publication.

## Verification and rollback

Run narrow tests, the full unittest suite, documentation checker, CLI and browser smoke. Record model/SDK versions, status and latency without secrets. Numeric assessment stays immutable across reveal. For a later deployment, record commit, image digest, revision, endpoint health and the real interaction, retaining a working revision for rollback.

## Reproducing the tested inference profile

The current demo uses the already-installed llama.cpp b9037 binary and existing Gemma weights. To reproduce its local profile, select the existing weight file and set alias gemma4:e4b-llama.cpp, host 127.0.0.1, port 8088, context 8192, one slot, q8_0 key/value cache, flash attention, RAM prompt cache/checkpoints disabled and reasoning budget 128 with reasoning enabled. The tested laptop used GPU layers 42 and eight CPU threads. These settings are recorded evidence for that machine, not a guarantee for other hardware.

The app never starts or downloads a model itself. A compatible local service with structured JSON-schema support is a prerequisite for --agents local. The deterministic experience remains usable without it. The separate project's original model launcher/configuration was preserved.
