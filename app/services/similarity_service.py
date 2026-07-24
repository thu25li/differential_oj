import ast
import difflib
import os
from typing import List, Tuple
from app.repositories.similarity_repository import similarity_repository
from app.repositories.submission_repository import submission_repository
from app.utils.errors import NotFoundError
from app.utils.time import now_utc
DEFAULT_THRESHOLD = float(os.environ.get("OJ_SIMILARITY_THRESHOLD", "0.7"))
def normalize_code(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ""
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            node.id = "VAR"
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            node.name = "FUNC"
        elif isinstance(node, ast.ClassDef):
            node.name = "CLASS"
        elif isinstance(node, ast.arg):
            node.arg = "ARG"
        elif isinstance(node, ast.keyword):
            if node.arg:
                node.arg = "KW"
    return ast.dump(tree, annotate_fields=False, include_attributes=False)
def compute_similarity(code_a: str, code_b: str) -> float:
    norm_a = normalize_code(code_a)
    norm_b = normalize_code(code_b)
    if not norm_a or not norm_b:
        return 0.0
    return difflib.SequenceMatcher(None, norm_a, norm_b).ratio()
class SimilarityService:
    async def check(self, problem_id: str, current_user: dict, threshold: float = DEFAULT_THRESHOLD) -> dict:
        subs = await submission_repository.list_sources_by_problem(problem_id)
        reports = []
        n = len(subs)
        for i in range(n):
            for j in range(i + 1, n):
                if subs[i]["user_id"] == subs[j]["user_id"]:
                    continue
                sim = compute_similarity(subs[i]["source_code"], subs[j]["source_code"])
                if sim >= threshold:
                    reports.append({
                        "problem_id": problem_id,
                        "submission_a": subs[i]["id"],
                        "submission_b": subs[j]["id"],
                        "similarity": round(sim, 4),
                        "method": "ast",
                        "created_at": now_utc(),
                    })
        await similarity_repository.delete_by_problem(problem_id)
        await similarity_repository.create_batch(reports)
        return {
            "problem_id": problem_id,
            "threshold": threshold,
            "compared_count": n,
            "report_count": len(reports),
        }
    async def list_reports(self, problem_id: str) -> dict:
        items = await similarity_repository.list_by_problem(problem_id)
        return {"problem_id": problem_id, "items": items, "total": len(items)}
similarity_service = SimilarityService()
