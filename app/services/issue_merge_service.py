import re
import unicodedata
from difflib import SequenceMatcher

from app.ai.json_guard import normalize_issue


class IssueMergeService:
    severity_order = {"BAIXA": 1, "MEDIA": 2, "CONFERIR": 2, "ALTA": 3, "CRITICA": 4}

    def merge(self, ai_payload: dict, rule_issues: list[dict] | None = None) -> list[dict]:
        merged: list[dict] = []

        for idx, issue in enumerate(rule_issues or [], start=1):
            normalized = normalize_issue({**issue, "source": "RULE"}, idx)
            self._add_or_merge(merged, normalized)

        for issue in ai_payload.get("normalized_issues", []):
            issue = {**issue, "source": "AI"}
            self._add_or_merge(merged, issue)

        self._sort_issues(merged)
        for idx, issue in enumerate(merged, start=1):
            issue["code"] = f"E{idx:03d}"
        return merged

    def _add_or_merge(self, merged: list[dict], incoming: dict) -> None:
        match_index = self._find_match(merged, incoming)
        if match_index is None:
            merged.append(incoming)
            return
        merged[match_index] = self._consolidate(merged[match_index], incoming)

    def _find_match(self, merged: list[dict], incoming: dict) -> int | None:
        for idx, existing in enumerate(merged):
            page_compatible = (
                existing.get("page_number") == incoming.get("page_number")
                or not existing.get("page_number")
                or not incoming.get("page_number")
            )
            if not page_compatible:
                continue
            same_type = existing.get("issue_type") == incoming.get("issue_type")
            similarity = self._similarity(existing.get("original_text", ""), incoming.get("original_text", ""))
            if similarity >= 0.86 or (same_type and similarity >= 0.74):
                return idx
        return None

    def _consolidate(self, existing: dict, incoming: dict) -> dict:
        preferred = self._better_explained(existing, incoming)
        secondary = incoming if preferred is existing else existing
        result = {**preferred}
        result["severity"] = self._max_severity(existing.get("severity"), incoming.get("severity"))
        result["source"] = "BOTH" if existing.get("source") != incoming.get("source") else existing.get("source", "AI")
        result["can_be_highlighted"] = existing.get("can_be_highlighted", True) or incoming.get("can_be_highlighted", True)
        result["located_in_pdf"] = existing.get("located_in_pdf", False) or incoming.get("located_in_pdf", False)
        if not result.get("suggestion") and secondary.get("suggestion"):
            result["suggestion"] = secondary["suggestion"]
        if not result.get("technical_reason") and secondary.get("technical_reason"):
            result["technical_reason"] = secondary["technical_reason"]
        return result

    def _better_explained(self, existing: dict, incoming: dict) -> dict:
        existing_score = self._quality_score(existing)
        incoming_score = self._quality_score(incoming)
        if incoming.get("source") == "AI" and incoming_score >= existing_score * 0.85:
            return incoming
        return incoming if incoming_score > existing_score else existing

    def _quality_score(self, issue: dict) -> int:
        return (
            len(issue.get("explanation", ""))
            + len(issue.get("technical_reason", ""))
            + len(issue.get("recommended_action", ""))
            + (15 if issue.get("suggestion") else 0)
        )

    def _max_severity(self, left: str | None, right: str | None) -> str:
        left = left or "MEDIA"
        right = right or "MEDIA"
        return left if self.severity_order.get(left, 0) >= self.severity_order.get(right, 0) else right

    def _similarity(self, left: str, right: str) -> float:
        left_key = self._match_key(left)
        right_key = self._match_key(right)
        if not left_key or not right_key:
            return 0
        if left_key in right_key or right_key in left_key:
            return 1
        return SequenceMatcher(None, left_key, right_key).ratio()

    def _match_key(self, text: str) -> str:
        text = "".join(
            char for char in unicodedata.normalize("NFD", str(text or ""))
            if unicodedata.category(char) != "Mn"
        )
        text = re.sub(r"[^a-zA-Z0-9§ºª]+", " ", text.lower())
        return re.sub(r"\s+", " ", text).strip()

    def _sort_issues(self, issues: list[dict]) -> None:
        issues.sort(key=lambda item: (item.get("page_number") or 99999, -self.severity_order.get(item.get("severity"), 0), item.get("original_text", "")))
