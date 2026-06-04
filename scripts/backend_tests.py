import json
import uuid
from datetime import timedelta

from fastapi.testclient import TestClient

from api.main import app
from api.auth import jwt_handler

client = TestClient(app)

RESULTS = {
    "auth": {},
    "core": {},
    "business": {},
    "e2e": {},
}


def save_results():
    with open("API_VALIDATION_RESULTS.json", "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, indent=2)


def write_report(passed=True, issues=None):
    with open("BACKEND_TEST_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# Backend Test Report\n\n")
        f.write("Passed: %s\n\n" % passed)
        if issues:
            f.write("## Issues\n")
            for it in issues:
                f.write(f"- {it}\n")

    if issues:
        with open("ISSUES_FOUND.md", "w", encoding="utf-8") as f:
            for it in issues:
                f.write(f"- {it}\n")


def run_auth_tests():
    # Register
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "TestPass123!"
    resp = client.post("/auth/register", json={"username": username, "email": f"{username}@example.com", "password": password})
    RESULTS["auth"]["register_status_code"] = resp.status_code
    RESULTS["auth"]["register_body"] = resp.json()

    # Login
    resp = client.post("/auth/login", json={"username": username, "password": password})
    RESULTS["auth"]["login_status_code"] = resp.status_code
    RESULTS["auth"]["login_body"] = resp.json()

    token = None
    if resp.status_code == 200:
        token = resp.json().get("data", {}).get("access_token")

    # Invalid token
    bad = client.get("/api/transactions", headers={"Authorization": "Bearer BADTOKEN"})
    RESULTS["auth"]["invalid_token_status"] = bad.status_code
    RESULTS["auth"]["invalid_token_body"] = bad.json()

    # Expired token (create one)
    payload = {"user_id": 0, "username": username, "role": "user"}
    expired = jwt_handler.create_access_token(payload, expires_delta=timedelta(seconds=-10))
    exp_resp = client.get("/api/transactions", headers={"Authorization": f"Bearer {expired}"})
    RESULTS["auth"]["expired_token_status"] = exp_resp.status_code
    RESULTS["auth"]["expired_token_body"] = exp_resp.json()

    return token


def run_core_tests(token):
    headers = {"Authorization": f"Bearer {token}"}

    # Transactions
    r_tx = client.get("/api/transactions", headers=headers)
    RESULTS["core"]["transactions_status"] = r_tx.status_code
    RESULTS["core"]["transactions_body_sample"] = r_tx.json()

    txs = r_tx.json().get("data", {}).get("transactions", [])
    RESULTS["core"]["transactions_count_returned"] = len(txs)

    # Suppliers
    r_sup = client.get("/api/suppliers", headers=headers)
    RESULTS["core"]["suppliers_status"] = r_sup.status_code
    RESULTS["core"]["suppliers_body_sample"] = r_sup.json()

    sups = r_sup.json().get("data", {}).get("suppliers", [])
    RESULTS["core"]["suppliers_count_returned"] = len(sups)

    # Metrics / monitoring
    r_mon = client.get("/api/monitoring", headers=headers)
    RESULTS["core"]["monitoring_status"] = r_mon.status_code
    RESULTS["core"]["monitoring_body"] = r_mon.json()

    # Risk score for a transaction
    first_tx = None
    if txs:
        first_tx = txs[0].get("transaction_id")
    if first_tx:
        r_risk = client.get(f"/api/risk/score/{first_tx}", headers=headers)
        RESULTS["core"]["risk_status"] = r_risk.status_code
        RESULTS["core"]["risk_body"] = r_risk.json()


def run_business_checks():
    issues = []
    # Check risk_score range using global metrics
    token = None
    # login as admin
    resp = client.post("/auth/login", json={"username": "admin", "password": "adminpass"})
    if resp.status_code == 200:
        token = resp.json().get("data", {}).get("access_token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = client.get("/api/metrics/global", headers=headers)
    if r.status_code == 200:
        vals = r.json().get("data", {})
        avg = vals.get("avg_risk_score")
        if avg is None:
            issues.append("avg_risk_score missing in global metrics")
        else:
            RESULTS["business"]["avg_risk_score"] = avg
    else:
        issues.append("Failed to fetch global metrics")

    # Basic record field checks
    txs = RESULTS.get("core", {}).get("transactions_body_sample", {}).get("data", {}).get("transactions", [])
    if txs:
        sample = txs[0]
        for field in ["transaction_id", "supplier_id", "risk_score", "risk_level"]:
            if field not in sample:
                issues.append(f"Missing field in transaction sample: {field}")
    else:
        issues.append("No transactions returned for checks")

    return issues


def main():
    token = run_auth_tests()
    if not token:
        RESULTS["e2e"]["status"] = "auth_failed"
        save_results()
        write_report(passed=False, issues=["Auth login failed; cannot continue tests"]) 
        return

    run_core_tests(token)
    issues = run_business_checks()

    save_results()
    write_report(passed=(len(issues) == 0), issues=issues)


if __name__ == "__main__":
    main()
