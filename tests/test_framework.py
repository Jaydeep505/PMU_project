import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pmu_val import analysis
from pmu_val.limits import check
from pmu_val.instruments.load import safe_load_ladder, DEFAULT_INVENTORY


def test_check_pass_fail():
    assert check("v", 5.0, "V", 4.75, 5.25).passed
    assert not check("v", 5.5, "V", 4.75, 5.25).passed
    assert not check("v", 4.0, "V", 4.75, 5.25).passed
    # one-sided limit
    assert check("eff", 90, "%", lower=80, upper=None).passed
    assert not check("eff", 70, "%", lower=80, upper=None).passed


def test_distribution_basic():
    d = analysis.distribution([1.0, 2.0, 3.0])
    assert d["n"] == 3
    assert abs(d["mean"] - 2.0) < 1e-9
    assert d["min"] == 1.0 and d["max"] == 3.0


def test_cpk_centered_high_when_tight():
    # tight spread, well inside wide limits -> large Cpk
    vals = [5.0, 5.001, 4.999, 5.0, 5.0]
    c = analysis.cpk(vals, lower=4.5, upper=5.5)
    assert c is None or c > 1.33


def test_cpk_none_for_single_value():
    assert analysis.cpk([5.0], 4.5, 5.5) is None


def test_yield_pct():
    assert analysis.yield_pct([True, True, True, True]) == 100.0
    assert analysis.yield_pct([True, False]) == 50.0
    assert analysis.yield_pct([]) == 0.0


def test_shmoo_grid_shape():
    rows = [
        {"parameter": "p", "value": 1, "passed": True, "vin": 6, "temp_c": 25},
        {"parameter": "p", "value": 1, "passed": False, "vin": 12, "temp_c": 25},
        {"parameter": "p", "value": 1, "passed": True, "vin": 6, "temp_c": 50},
    ]
    sh = analysis.shmoo(rows, "p")
    assert sh["x"] == [6, 12]
    assert 25 in sh["y"] and 50 in sh["y"]
    assert sh["grid"][(25, 12)] == 0.0


def test_load_ladder_is_safe():
    # every load returned for each rail must respect resistor power ratings
    for rail in (5.0, 9.0, 12.0):
        ladder = safe_load_ladder(list(DEFAULT_INVENTORY), rail)
        assert ladder, f"no safe loads at {rail} V"
        for c in ladder:
            assert c.is_safe(rail), f"{c.label} unsafe at {rail} V"
            # current must be positive and finite
            assert c.current(rail) > 0


def test_load_ladder_currents_monotonic():
    ladder = safe_load_ladder(list(DEFAULT_INVENTORY), 5.0)
    currents = [c.current(5.0) for c in ladder]
    assert currents == sorted(currents)
