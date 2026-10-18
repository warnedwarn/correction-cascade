import json
import re
import time
from pathlib import Path

from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from genlayer_py.contracts import actions as contract_actions


def calldata_compat(method=None, args=None, kwargs=None):
    result = {}
    if method is not None:
        result["method"] = method
    if args:
        result["args"] = args
    if kwargs:
        result["kwargs"] = kwargs
    return result


contract_actions.make_calldata_object = calldata_compat
ROOT = Path(__file__).parents[1]
ENV = (ROOT.parents[3] / "accounts.env").read_text()
DEPLOYMENT = json.loads((ROOT / "deployment.json").read_text())
ADDRESS = DEPLOYMENT["contractAddress"]
COMMIT = DEPLOYMENT["sourceCommit"]
KEY = re.search(r'^ACCOUNT_2_GENLAYER_PRIVATE_KEY\s*=\s*"?([^"\r\n]+)', ENV, re.M).group(1).strip()
ACCOUNT = create_account(account_private_key=KEY)
CLIENT = create_client(chain=studionet, account=ACCOUNT)


def write(name, args):
    tx = CLIENT.write_contract(address=ADDRESS, function_name=name, args=args)
    print(name + "_tx=" + str(tx), flush=True)
    receipt = CLIENT.wait_for_transaction_receipt(
        transaction_hash=tx,
        wait_until="finalized",
        retries=180,
        interval=5000,
        full_transaction=True,
    )
    leaders = receipt.get("consensus_data", {}).get("leader_receipt") or []
    leaders = [leaders] if isinstance(leaders, dict) else leaders
    assert receipt.get("result_name") == "MAJORITY_AGREE"
    assert any(item.get("execution_result") == "SUCCESS" for item in leaders)
    return str(tx)


base = f"https://raw.githubusercontent.com/warnedwarn/correction-cascade/{COMMIT}/evidence"
cascade_id = "CASCADE-" + str(int(time.time()))
labels = ["Canonical article", "Syndicated copy", "Weekly digest", "Search excerpt"]
urls = [
    base + "/publication-origin.md",
    base + "/publication-syndicated.md",
    base + "/publication-digest.md",
    base + "/publication-search.md",
]
transactions = {
    "open": write(
        "open_cascade",
        [
            cascade_id,
            "North Archive closure-date correction",
            base + "/correction-notice.md",
            labels,
            urls,
            [[0, 1], [0, 2], [1, 3], [2, 3]],
            3,
        ],
    )
}
transactions["check"] = write("check_propagation", [cascade_id])
state = CLIENT.read_contract(address=ADDRESS, function_name="get_cascade", args=[cascade_id])
assert state["state"] == "COMPLETE"
assert state["latest_statuses"] == ["INCORPORATED"] * 4
assert state["latest_frontier"] == []
assert len(state["latest_digests"]) == 5
proof = {
    "cascadeId": cascade_id,
    "transactions": transactions,
    "state": state,
    "fixtureDisclosure": "The correction and publication pages are operator-authored technical fixtures used to demonstrate digest binding, semantic incorporation checks, and deterministic graph handling.",
}
(ROOT / "evidence" / "live-proof.json").write_text(json.dumps(proof, indent=2) + "\n")
print(json.dumps(proof, indent=2), flush=True)
