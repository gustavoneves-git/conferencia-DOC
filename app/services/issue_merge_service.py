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
            if not normalized:
                continue
            self._add_or_merge(merged, normalized)

        for issue in ai_payload.get("normalized_issues", []):
            issue = {**issue, "source": "AI"}
            self._add_or_merge(merged, issue)

        merged = self._dedupe_final(merged)
        self._mark_repeated_occurrences(merged)
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
            same_type = existing.get("issue_type") == incoming.get("issue_type")
            similarity = self._similarity(existing.get("original_text", ""), incoming.get("original_text", ""))
            overlap = self._overlap(existing.get("original_text", ""), incoming.get("original_text", ""))
            if self._must_keep_separate(existing, incoming):
                continue
            if not self._page_compatible(existing.get("page_number"), incoming.get("page_number"), similarity, overlap):
                continue
            if similarity >= 0.86 or overlap >= 0.72 or (same_type and (similarity >= 0.70 or overlap >= 0.55)):
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

    def _must_keep_separate(self, existing: dict, incoming: dict) -> bool:
        left = self._match_key(existing.get("original_text", ""))
        right = self._match_key(incoming.get("original_text", ""))
        protected = {
            "mandado judicial",
            "art 1 072 § 3º",
            "casado no regime comunhao parcial de bens",
            "casada no regime comunhao parcial de bens",
        }
        left_protected = left in protected
        right_protected = right in protected
        if left_protected and right_protected and left != right:
            return True
        if left_protected != right_protected:
            shorter, longer = (left, right) if left_protected else (right, left)
            if shorter in longer and len(longer.split()) > len(shorter.split()) + 4:
                return True
        return False

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

    def _overlap(self, left: str, right: str) -> float:
        left_words = set(self._match_key(left).split())
        right_words = set(self._match_key(right).split())
        if not left_words or not right_words:
            return 0
        return len(left_words & right_words) / min(len(left_words), len(right_words))

    def _page_compatible(self, left_page, right_page, similarity: float, overlap: float) -> bool:
        if not left_page or not right_page or left_page == right_page:
            return True
        try:
            distance = abs(int(left_page) - int(right_page))
        except (TypeError, ValueError):
            return False
        return distance == 1 and (similarity >= 0.86 or overlap >= 0.72)

    def _dedupe_final(self, issues: list[dict]) -> list[dict]:
        result: list[dict] = []
        for issue in issues:
            match_index = self._find_match(result, issue)
            if match_index is None:
                result.append(issue)
            else:
                result[match_index] = self._consolidate(result[match_index], issue)
        return result

    def _match_key(self, text: str) -> str:
        text = "".join(
            char for char in unicodedata.normalize("NFD", str(text or ""))
            if unicodedata.category(char) != "Mn"
        )
        text = re.sub(r"[^a-zA-Z0-9§ºª]+", " ", text.lower())
        return re.sub(r"\s+", " ", text).strip()

    def _sort_issues(self, issues: list[dict]) -> None:
        issues.sort(key=lambda item: (item.get("page_number") or 99999, -self.severity_order.get(item.get("severity"), 0), item.get("original_text", "")))

    def _mark_repeated_occurrences(self, issues: list[dict]) -> None:
        groups: dict[str, list[dict]] = {}
        for issue in issues:
            key = self._repeat_key(issue)
            if key:
                groups.setdefault(key, []).append(issue)
        group_index = 1
        for items in groups.values():
            pages = {item.get("page_number") for item in items}
            if len(items) < 2 or len(pages) < 2:
                continue
            group_id = f"R{group_index:03d}"
            group_index += 1
            for item in items:
                item["repeated_group_id"] = group_id
                item["repeated_count"] = len(items)

    def _repeat_key(self, issue: dict) -> str:
        text = self._match_key(issue.get("original_text", ""))
        if not text:
            return ""
        known = {
            "clausula adjudicia e a extra",
            "contas corrente",
            "ordenar titulos de creditos para protesto",
        }
        if text in known:
            return text
        if len(text.split()) <= 8:
            return f"{issue.get('issue_type')}|{text}"
        return ""
