from app.services.rule_review_service import RuleReviewService


def test_detects_inicio_rule():
    issues = RuleReviewService().review([{"page_number": 1, "text": "CLÁUSULA DA INICIO"}])
    assert issues
    assert issues[0]["suggestion"] == "DO INÍCIO"
