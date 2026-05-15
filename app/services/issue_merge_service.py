class IssueMergeService:
    def merge(self, ai_payload: dict) -> list[dict]:
        seen = set()
        merged = []
        for issue in ai_payload.get("normalized_issues", []):
            key = (issue.get("page_number"), issue.get("original_text", "").lower(), issue.get("issue_type"))
            if key in seen:
                continue
            seen.add(key)
            issue["code"] = f"E{len(merged) + 1:03d}"
            merged.append(issue)
        return merged
