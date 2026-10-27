"""Five read-only MCP tools. No world/replay/outcome, files, URLs or execution tools."""
import argparse
import json
from pathlib import Path
from typing import Any

from .analysis import analyse_pressure, analyse_snapshot
from .scenario import build_catalog
from .snapshots import DecisionSnapshot, freeze_snapshot


TOOLS = ("get_decision_state", "analyse_pass_option", "analyse_pressure", "compare_options", "get_principle")


class EvidenceTools:
    def __init__(self, snapshots):
        self._snapshots = {}
        self._reports = {}
        for snapshot in snapshots:
            if not isinstance(snapshot, DecisionSnapshot):
                raise TypeError("Only frozen DecisionSnapshot objects are accepted")
            snapshot.read()
            self._snapshots[snapshot.snapshot_id] = snapshot
            self._reports[snapshot.snapshot_id] = json.dumps(analyse_snapshot(snapshot), allow_nan=False)
        self._principles = {}
        path = Path(__file__).resolve().parents[1] / "docs/knowledge/keeper-principles.md"
        for line in path.read_text(encoding="utf-8").splitlines():
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) == 3 and cells[0] in {f"K{number:02}" for number in range(1, 13)}:
                self._principles[cells[0]] = {"principle_id": cells[0], "situation": cells[1], "text": cells[2], "review_status": "draft", "source": "original project principle"}

    def _snapshot(self, snapshot_id):
        if not isinstance(snapshot_id, str) or snapshot_id not in self._snapshots:
            raise ValueError("Unknown snapshot_id")
        return self._snapshots[snapshot_id]

    def get_decision_state(self, snapshot_id: str) -> dict[str, Any]:
        """Return only the allowlisted frozen state; never the scenario package."""
        return {"snapshot_id": snapshot_id, "decision": self._snapshot(snapshot_id).read()}

    def analyse_pass_option(self, snapshot_id: str, option_id: str) -> dict[str, Any]:
        """Evidence for one fixed option, with explicit unsupported/stale status."""
        state = self._snapshot(snapshot_id).read()
        if option_id not in {item["option_id"] for item in state["options"]}:
            raise ValueError("Unknown option_id")
        report = json.loads(self._reports[snapshot_id])
        if report["status"] == "insufficient_evidence":
            return {**report, "requested_option_id": option_id}
        return {"snapshot_id": snapshot_id, "model_version": report["model_version"],
                "limitations": report["limitations"], "option": next(item for item in report["options"] if item["option_id"] == option_id)}

    def analyse_pressure(self, snapshot_id: str) -> dict[str, Any]:
        """Pressure timing at the keeper, under fixed snapshot assumptions."""
        return analyse_pressure(self._snapshot(snapshot_id))

    def compare_options(self, snapshot_id: str, option_ids: list[str]) -> dict[str, Any]:
        """Compare declared ground-route evidence; never an overall action ranking."""
        state = self._snapshot(snapshot_id).read()
        if not isinstance(option_ids, list) or not 1 <= len(option_ids) <= 3 or any(not isinstance(item, str) for item in option_ids):
            raise ValueError("Provide one to three option IDs")
        if len(set(option_ids)) != len(option_ids) or not set(option_ids) <= {item["option_id"] for item in state["options"]}:
            raise ValueError("Unknown or duplicate option IDs")
        report = json.loads(self._reports[snapshot_id])
        report["options"] = [item for item in report["options"] if item["option_id"] in option_ids]
        report["comparisons"] = [item for item in report["comparisons"] if set(item["option_ids"]) <= set(option_ids)]
        report["comparison_scope"] = "Sampled ground-route timing under fixed assumptions; aerial possession and overall tactical optimality unavailable."
        return report

    def get_principle(self, principle_id: str) -> dict[str, Any]:
        """Original draft review prompt; no external or private Coach KB lookup."""
        if not isinstance(principle_id, str) or principle_id not in self._principles:
            raise ValueError("Unknown principle_id")
        return dict(self._principles[principle_id])


def create_server(tools=None):
    from mcp.server.fastmcp import FastMCP
    tools = tools or EvidenceTools(freeze_snapshot(scenario) for scenario in build_catalog().values())
    server = FastMCP("KeepersBoots", log_level="ERROR")
    for name in TOOLS:
        server.add_tool(getattr(tools, name), name=name)
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
