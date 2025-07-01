# test_project.py
import pytest
from project import parse_log_file, evaluate_compliance, load_patch_manifest
from datetime import datetime

def test_parse_log_file(tmp_path):
    log_file = tmp_path / "logs.csv"
    log_file.write_text("server,patch,timestamp\nsrv01,patch1,2024-05-01\nsrv02,patch2,2024-05-02\n")
    logs = parse_log_file(str(log_file))
    assert len(logs) == 2
    assert logs[0]["server"] == "srv01"
    assert logs[0]["patch"] == "patch1"
    assert isinstance(logs[0]["timestamp"], datetime)

def test_evaluate_compliance():
    patch_manifest = {
        "srv01": "patch1",
        "srv02": "patch2",
        "srv03": "patch3"
    }
    logs = [
        {"server": "srv01", "patch": "patch1", "timestamp": datetime(2024, 5, 1)},
        {"server": "srv02", "patch": "patch2", "timestamp": datetime(2024, 5, 2)}
    ]
    compliance, _, _ = evaluate_compliance(patch_manifest, logs)
    assert compliance["srv01"] == "Compliant"
    assert compliance["srv02"] == "Compliant"
    assert compliance["srv03"] == "Non-Compliant"

def test_load_patch_manifest(tmp_path):
    yaml_file = tmp_path / "patch.yml"
    yaml_file.write_text("srv01: patch1\nsrv02: patch2")
    manifest = load_patch_manifest(str(yaml_file))
    assert manifest == {"srv01": "patch1", "srv02": "patch2"}
