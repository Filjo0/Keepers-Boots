"""Structured interpretation contract and deterministic guards before display."""
import re
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, create_model


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    claim_id: str = Field(pattern=r"^c[0-9]{1,2}$")
    evidence_ids: list[str] = Field(min_length=1, max_length=4)
    principle_ids: list[str] = Field(max_length=3)
    text: str = Field(min_length=1, max_length=500)


class Draft(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    snapshot_id: str
    claims: list[Claim] = Field(min_length=1, max_length=5)
    fan: str = Field(min_length=1, max_length=900)
    analyst: str = Field(min_length=1, max_length=1600)
    missing_information: list[str] = Field(max_length=4)
    ranking: None


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    status: str = Field(pattern=r"^(accept|revise|insufficient_evidence)$")
    rejected_claim_ids: list[str] = Field(max_length=5)
    reasons: list[str] = Field(max_length=6)


def available_evidence_ids(assessment):
    identifiers = {item["evidence_id"] for item in assessment["options"]} | {"pressure:arrival"}
    identifiers.update(item["evidence_id"] for item in assessment.get("comparisons", []))
    if assessment["status"] == "insufficient_evidence":
        identifiers.add("observations:age")
    return identifiers


def draft_schema(snapshot, assessment):
    """Bind generation's citation/hash choices to this frozen evidence packet."""
    evidence_type = Literal[tuple(sorted(available_evidence_ids(assessment)))]
    principle_type = Literal["K03", "K04", "K09", "K11", "K12"]
    identifiers = [item["player_id"] for item in snapshot.read()["observations"]]
    identifiers += [f"K{number:02}" for number in range(1, 13)]
    prose_atom = r'^(?:[^0-9"\\\x00-\x1f]|' + "|".join(re.escape(item) for item in identifiers) + ")"

    def prose_pattern(max_atoms):
        # Decoder patterns must exclude JSON delimiters/escapes and bound their own
        # repetition. Each permitted identifier consumes at most three characters.
        return prose_atom + "{1," + str(max_atoms) + "}$"
    bounded_claim = create_model(
        "EvidenceClaim", __base__=Claim,
        evidence_ids=(list[evidence_type], Field(min_length=1, max_length=4)),
        principle_ids=(list[principle_type], Field(max_length=3)),
        text=(str, Field(min_length=1, max_length=450, pattern=prose_pattern(150))),
    )
    return create_model(
        "EvidenceDraft", __base__=Draft,
        snapshot_id=(Literal[snapshot.snapshot_id], ...),
        claims=(list[bounded_claim], Field(min_length=1, max_length=1 if assessment["status"] == "insufficient_evidence" else 2)),
        fan=(str, Field(min_length=1, max_length=720, pattern=prose_pattern(240))),
        analyst=(str, Field(min_length=1, max_length=1200, pattern=prose_pattern(400))),
        missing_information=(list[Annotated[str, Field(max_length=270, pattern=prose_pattern(90))]], Field(max_length=2)),
    )


def validate_draft(draft, snapshot, assessment):
    """Numbers stay in code-rendered evidence, never freely transcribed prose."""
    draft = Draft.model_validate(draft)
    state = snapshot.read()
    errors = []
    if draft.snapshot_id != snapshot.snapshot_id or assessment["snapshot_id"] != snapshot.snapshot_id:
        errors.append("snapshot_id_mismatch")
    available = available_evidence_ids(assessment)
    if assessment["status"] == "insufficient_evidence":
        if not draft.missing_information:
            errors.append("missing_abstention_information")
    claim_ids = [claim.claim_id for claim in draft.claims]
    if len(set(claim_ids)) != len(claim_ids):
        errors.append("duplicate_claim_id")
    for claim in draft.claims:
        if not set(claim.evidence_ids) <= available:
            errors.append("unknown_evidence_id:" + claim.claim_id)
        if not set(claim.principle_ids) <= {f"K{number:02}" for number in range(1, 13)}:
            errors.append("unknown_principle_id:" + claim.claim_id)
        if (assessment["status"] != "insufficient_evidence"
                and re.search(r"\b(?:release[- ]before[- ]pressure|release time before pressure|pressure arrival)\b", claim.text, re.I)
                and "pressure:arrival" not in claim.evidence_ids):
            errors.append("pressure_evidence_required:" + claim.claim_id + ":pressure:arrival")
        for fact in assessment.get("comparisons", []):
            if fact["relation"] != "ordered":
                continue
            higher, lower = fact["larger_margin_option_id"], fact["smaller_margin_option_id"]
            for first, second, wrong_direction in [(higher, lower, "smaller|lower|shorter"), (lower, higher, "larger|higher|greater|longer")]:
                pattern = (r"\b" + re.escape(first) + r"\b[^.!?]{0,80}\b(?:" + wrong_direction +
                           r")\b[^.!?]{0,40}\b(?:minimum )?(?:sampled )?interception margin\b[^.!?]{0,30}\bthan\b[^.!?]{0,30}\b" + re.escape(second) + r"\b")
                match = re.search(pattern, claim.text, re.I)
                negation = (r"\b(?:no|not|never)\s+(?:(?:have|show|indicate|produce|a|an|the|necessarily)\s+){0,3}(?:" + wrong_direction + r")\b")
                if match and not re.search(negation, match.group(), re.I):
                    errors.append("comparison_direction_mismatch:" + claim.claim_id)
    texts = [draft.fan, draft.analyst, *draft.missing_information, *(claim.text for claim in draft.claims)]
    prose = [("fan", draft.fan), ("analyst", draft.analyst), *((claim.claim_id, claim.text) for claim in draft.claims)]
    for field, text in prose:
        if not text.rstrip().endswith((".", "!", "?")):
            errors.append("incomplete_prose:" + field)
    players = {item["player_id"] for item in state["observations"]}
    principles = {f"K{number:02}" for number in range(1, 13)}
    for text in texts:
        if re.search(r"\bbefore (?:the )?keeper arrives\b", text, re.I):
            errors.append("pressure_arrival_subject_mismatch")
        polarity = re.search(r"\b(?:both|all) ground (?:options|routes) (?:show|have) (positive|negative) (?:sampled |interception |sampled interception )?margins\b", text, re.I)
        if polarity:
            sign = polarity.group(1).lower()
            for option in assessment["options"]:
                margins = option.get("minimum_interception_margin_s")
                if margins and ((sign == "positive" and max(margins) <= 0)
                                or (sign == "negative" and min(margins) >= 0)):
                    errors.append("ground_margin_polarity_mismatch:" + sign + ":" + option["option_id"])
        for player in re.findall(r"\b[HV][0-9]{2}\b", text):
            if player not in players:
                errors.append("unknown_player_id")
        for principle in re.findall(r"\bK[0-9]{2}\b", text):
            if principle not in principles:
                errors.append("unknown_principle_id_in_prose")
        stripped = re.sub(r"\b[HVK][0-9]{2}\b", "", text)
        if re.search(r"\d", stripped):
            errors.append("unrendered_number")
        if re.search(r"\b(?:was completed|was intercepted|will score|scored a goal|recorded outcome|recorded pass)\b", text, re.I):
            errors.append("future_or_outcome_claim")
        without_negation = re.sub(
            r"\b(?:does not|doesn't|do not|don't|cannot|can't)\s+"
            r"(?:measure|estimate|calculate|provide|predict|establish|determine)\s+"
            r"(?:(?:a|an|the|any|pass)\s+){0,2}completion probability\b",
            "", text, flags=re.I)
        without_negation = re.sub(
            r"\b(?:not|never|no)\s+(?:(?:a|an|the|overall|universal)\s+){0,3}"
            r"(?:guarantee|guaranteed|probability|optimal|best action|completion probability)\b",
            "", without_negation, flags=re.I)
        if re.search(r"\b(?:guaranteed|optimal|best action|completion probability|coach.approved)\b", without_negation, re.I):
            errors.append("unsupported_scope")
    return draft, sorted(set(errors))
