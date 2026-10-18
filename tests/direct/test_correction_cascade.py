from conftest import CONTRACT
import json


CORRECTION = "https://origin.example/notices/correction-4"
LABELS = ["Canonical article", "Syndicated copy", "Weekly digest", "Search excerpt"]
URLS = [
    "https://news.example/article",
    "https://syndicate.example/copy",
    "https://digest.example/week-12",
    "https://search.example/result",
]
EDGES = [[0, 1], [0, 2], [1, 3], [2, 3]]


def opened(vm, deploy, owner, max_checks=3):
    vm.strict_mocks = True
    vm.check_pickling = True
    vm.sender = owner
    contract = deploy(CONTRACT)
    contract.open_cascade(
        "corr-4",
        "Incorrect closure date propagation",
        CORRECTION,
        LABELS,
        URLS,
        EDGES,
        max_checks,
    )
    return contract


def sources(vm):
    vm.mock_web(r"origin\.example", {"status": 200, "body": "Correction: the closure date is 18 March, not 8 March."})
    vm.mock_web(r"news\.example", {"status": 200, "body": "Updated: closure date is 18 March."})
    vm.mock_web(r"syndicate\.example", {"status": 200, "body": "Old copy says closure date is 8 March."})
    vm.mock_web(r"digest\.example", {"status": 200, "body": "Correction incorporated: closure date is 18 March."})
    vm.mock_web(r"search\.example", {"status": 200, "body": "Cached excerpt says 8 March."})


def llm(vm, statuses):
    rows = [{"index": index, "status": status} for index, status in enumerate(statuses)]
    vm.mock_llm(r".*CorrectionCascade inspection.*", json.dumps({"rows": rows}))


def test_partial_round_computes_first_stale_frontier(direct_vm, direct_deploy, direct_alice):
    contract = opened(direct_vm, direct_deploy, direct_alice)
    sources(direct_vm)
    llm(direct_vm, ["INCORPORATED", "STALE", "INCORPORATED", "STALE"])
    direct_vm.sender = direct_alice
    contract.check_propagation("corr-4")
    result = contract.get_cascade("corr-4")
    assert result["state"] == "TRACKING"
    assert result["latest_frontier"] == [1]
    assert result["history"][0]["stale"] == [1, 3]
    assert result["history"][0]["result"] == "PARTIAL"
    assert len(result["latest_digests"]) == 5


def test_complete_round_closes_cascade(direct_vm, direct_deploy, direct_alice):
    contract = opened(direct_vm, direct_deploy, direct_alice)
    sources(direct_vm)
    llm(direct_vm, ["INCORPORATED"] * 4)
    contract.check_propagation("corr-4")
    result = contract.get_cascade("corr-4")
    assert result["state"] == "COMPLETE"
    assert result["latest_frontier"] == []
    with direct_vm.expect_revert("active cascade"):
        contract.check_propagation("corr-4")


def test_partial_round_can_progress_to_complete(direct_vm, direct_deploy, direct_alice):
    contract = opened(direct_vm, direct_deploy, direct_alice)
    sources(direct_vm)
    llm(direct_vm, ["INCORPORATED", "STALE", "INCORPORATED", "STALE"])
    contract.check_propagation("corr-4")
    assert contract.get_cascade("corr-4")["state"] == "TRACKING"

    direct_vm._llm_mocks.clear()
    llm(direct_vm, ["INCORPORATED"] * 4)
    contract.check_propagation("corr-4")
    result = contract.get_cascade("corr-4")
    assert result["state"] == "COMPLETE"
    assert result["checks"] == 2
    assert [row["result"] for row in result["history"]] == ["PARTIAL", "COMPLETE"]


def test_check_limit_exhausts_without_false_completion(direct_vm, direct_deploy, direct_alice):
    contract = opened(direct_vm, direct_deploy, direct_alice, max_checks=1)
    sources(direct_vm)
    llm(direct_vm, ["INCORPORATED", "STALE", "STALE", "STALE"])
    contract.check_propagation("corr-4")
    result = contract.get_cascade("corr-4")
    assert result["state"] == "EXHAUSTED"
    assert result["history"][0]["result"] == "PARTIAL"


def test_unreadable_is_inconclusive_not_complete(direct_vm, direct_deploy, direct_alice):
    contract = opened(direct_vm, direct_deploy, direct_alice, max_checks=1)
    sources(direct_vm)
    llm(direct_vm, ["INCORPORATED", "UNREADABLE", "INCORPORATED", "INCORPORATED"])
    contract.check_propagation("corr-4")
    result = contract.get_cascade("corr-4")
    assert result["state"] == "EXHAUSTED"
    assert result["history"][0]["result"] == "INCONCLUSIVE"


def test_validator_rejects_forged_status_and_digest(direct_vm, direct_deploy, direct_alice):
    contract = opened(direct_vm, direct_deploy, direct_alice)
    sources(direct_vm)
    llm(direct_vm, ["INCORPORATED", "STALE", "INCORPORATED", "STALE"])
    result = contract._observe(contract.cascades["CORR-4"])
    assert direct_vm.run_validator(leader_result=result) is True
    forged = {"digests": list(result["digests"]), "rows": json.loads(json.dumps(result["rows"]))}
    forged["rows"][1]["status"] = "INCORPORATED"
    assert direct_vm.run_validator(leader_result=forged) is False
    forged = {"digests": list(result["digests"]), "rows": result["rows"]}
    forged["digests"][0] = "f" * 64
    assert direct_vm.run_validator(leader_result=forged) is False


def test_duplicate_slots_cycle_and_duplicate_id_rejected(direct_vm, direct_deploy, direct_alice):
    contract = opened(direct_vm, direct_deploy, direct_alice)
    with direct_vm.expect_revert("unique cascade id"):
        contract.open_cascade("corr-4", "Duplicate", CORRECTION, LABELS, URLS, EDGES, 2)
    with direct_vm.expect_revert("distinct correction and publication slots"):
        contract.open_cascade("corr-5", "Duplicate URL", CORRECTION, LABELS[:2], [CORRECTION, URLS[1]], [[0, 1]], 2)
    with direct_vm.expect_revert("acyclic dependency graph"):
        contract.open_cascade("corr-6", "Cycle", CORRECTION, LABELS[:2], URLS[:2], [[0, 1], [1, 0]], 2)


def test_cancel_requires_owner_and_zero_checks(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = opened(direct_vm, direct_deploy, direct_alice)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("owner of unchecked cascade"):
        contract.cancel_unchecked("corr-4")
    direct_vm.sender = direct_alice
    contract.cancel_unchecked("corr-4")
    with direct_vm.expect_revert("active cascade"):
        contract.check_propagation("corr-4")
