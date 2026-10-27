"""Export the existing live HTTP captures; never invent an agent run or repair."""
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from keepers_boots.analysis import analyse_pressure, analyse_snapshot
from keepers_boots.recordings import DIRECTORY, export_recording
from keepers_boots.scenario import build_catalog
from keepers_boots.snapshots import freeze_snapshot


# Human audit annotations are bound to a particular capture, never prose guards.
CAPTURE_NOTES = {
    "bb9f02ebb059e2aafe5a49aac0ca66684435da33d08d762f12c3519378f8f642": [
        "Known wording flaw in the analyst text and a claim: scenario 1 tests no variation in preparation delay, so it does not establish that delay leaves the margin's width unchanged. This recording uses the prompt from before commit 7ee37ef; the later prompt fix did not regenerate it. Reviewer approval does not establish that inference."
    ]
}


def main():
    recordings = []
    for scenario_id, scenario in build_catalog().items():
        snapshot = freeze_snapshot(scenario)
        source = ROOT / "local-artifacts" / ("runtime-" + scenario_id + ".json")
        captured = json.loads(source.read_text(encoding="utf-8"))
        notes = (["Known wording error in this capture: 'before the keeper arrives' should refer to the pressing opponent reaching the keeper. The reviewer accepted it; approval is not proof of correctness."]
                 if "before the keeper arrives" in captured["interpretation"]["fan"].lower() else [])
        recording = export_recording(source, snapshot, analyse_snapshot(snapshot), analyse_pressure(snapshot), notes)
        recording["recording"]["notes"].extend(CAPTURE_NOTES.get(recording["recording"]["source_sha256"], []))
        recordings.append((scenario_id, recording))
    DIRECTORY.mkdir(exist_ok=True)
    for scenario_id, recording in recordings:
        (DIRECTORY / (scenario_id + ".json")).write_text(
            json.dumps(recording, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        print("Exported accepted capture: " + scenario_id)


if __name__ == "__main__":
    main()
