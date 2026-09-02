import pytest
from itertools import product as iproduct
from collections import defaultdict
from app.api.v1.optimization.simulations import (
    SCENARIO_VARIANTS,
    PERSONA_PROFILE_MAP,
    _build_expanded_variant_pool,
)


# ─────────────────────────────────────────────
# Helpers that mirror the production loop
# ─────────────────────────────────────────────

def _simulate_scenario_generation(profiles, scenario_count):
    """
    Replicate the fixed scenario generation logic from simulations.py.
    Returns a list of (base_profile, budget, requirements_tuple, deadline) tuples.
    """
    pools = {p.upper(): _build_expanded_variant_pool(p) for p in set(profiles)}
    base_labels = {
        p.upper(): [v[0] for v in SCENARIO_VARIANTS.get(p.upper(), SCENARIO_VARIANTS["BALANCED"])]
        for p in set(profiles)
    }
    counters = defaultdict(int)
    scenarios = []
    for index in range(scenario_count):
        base = profiles[index % len(profiles)]
        pool = pools[base.upper()]
        idx = counters[base] % len(pool)
        counters[base] += 1
        budget, reqs, deadline = pool[idx]
        scenarios.append((base, budget, reqs, deadline))
    return scenarios


# ─────────────────────────────────────────────
# _build_expanded_variant_pool unit tests
# ─────────────────────────────────────────────

def test_expanded_pool_starts_with_base_variants():
    """The first 5 entries must match the curated SCENARIO_VARIANTS."""
    for persona_key in SCENARIO_VARIANTS:
        pool = _build_expanded_variant_pool(persona_key)
        base = SCENARIO_VARIANTS[persona_key]
        for i, (label, budget, reqs, deadline) in enumerate(base):
            assert pool[i] == (budget, tuple(reqs), deadline), (
                f"{persona_key}: pool[{i}] mismatch vs base variant '{label}'"
            )


def test_expanded_pool_has_no_duplicates():
    """All entries in the expanded pool must be unique per persona."""
    for persona_key in SCENARIO_VARIANTS:
        pool = _build_expanded_variant_pool(persona_key)
        assert len(pool) == len(set(pool)), (
            f"{persona_key}: expanded pool contains duplicate entries"
        )


def test_expanded_pool_size_sufficient_for_20_scenarios():
    """Each persona's expanded pool must have >= 20 entries so 20 scenarios can be unique."""
    for persona_key in SCENARIO_VARIANTS:
        pool = _build_expanded_variant_pool(persona_key)
        assert len(pool) >= 20, (
            f"{persona_key}: pool has only {len(pool)} entries, need >= 20"
        )


def test_expanded_pool_uses_only_existing_constraint_values():
    """Extended combinations must only use budget/req/deadline values from the base variants."""
    for persona_key in SCENARIO_VARIANTS:
        base = SCENARIO_VARIANTS[persona_key]
        valid_budgets = {v[1] for v in base}
        valid_reqs = {tuple(v[2]) for v in base}
        valid_deadlines = {v[3] for v in base}

        pool = _build_expanded_variant_pool(persona_key)
        for b, r, d in pool:
            assert b in valid_budgets, f"{persona_key}: foreign budget {b} in extended pool"
            assert r in valid_reqs, f"{persona_key}: foreign reqs {r} in extended pool"
            assert d in valid_deadlines, f"{persona_key}: foreign deadline {d} in extended pool"


# ─────────────────────────────────────────────
# Scenario generation tests — coverage matrix
# ─────────────────────────────────────────────

def test_20_scenarios_2_personas_are_all_distinct():
    """
    Regression: with only 2 personas (FEATURE + QUALITY), 20 scenarios must all
    be distinct. Before the expanded pool fix, scenarios 11-20 were copies of 1-10.
    """
    profiles = ["FEATURE", "QUALITY"]
    scenarios = _simulate_scenario_generation(profiles, 20)
    assert len(scenarios) == 20
    assert len(set(scenarios)) == 20, (
        f"Expected 20 unique scenarios with 2 personas, got {len(set(scenarios))} unique.\n"
        + "\n".join(f"  #{i+1}: {s}" for i, s in enumerate(scenarios))
    )


def test_20_scenarios_1_persona_are_all_distinct():
    """With 1 persona selected, 20 scenarios must all be distinct."""
    for persona in ["QUALITY", "FEATURE", "BUDGET", "SPEED", "BALANCED"]:
        profiles = [persona]
        scenarios = _simulate_scenario_generation(profiles, 20)
        assert len(scenarios) == 20
        assert len(set(scenarios)) == 20, (
            f"1-persona [{persona}]: expected 20 unique scenarios, got {len(set(scenarios))} unique."
        )


def test_20_scenarios_all_5_personas_are_all_distinct():
    """With all 5 personas, 20 scenarios must remain distinct."""
    profiles = ["BUDGET", "SPEED", "QUALITY", "FEATURE", "BALANCED"]
    scenarios = _simulate_scenario_generation(profiles, 20)
    assert len(scenarios) == 20
    assert len(set(scenarios)) == 20


def test_5_scenario_mode():
    """5 scenarios with any number of personas must produce 5 unique scenarios."""
    for profiles in [["QUALITY"], ["FEATURE", "QUALITY"], ["BUDGET", "SPEED", "QUALITY", "FEATURE", "BALANCED"]]:
        scenarios = _simulate_scenario_generation(profiles, 5)
        assert len(scenarios) == 5
        assert len(set(scenarios)) == 5, f"profiles={profiles}: expected 5 unique, got {len(set(scenarios))}"


def test_10_scenario_mode():
    """10 scenarios with any number of personas must produce 10 unique scenarios."""
    for profiles in [["QUALITY"], ["FEATURE", "QUALITY"], ["BUDGET", "SPEED", "QUALITY", "FEATURE", "BALANCED"]]:
        scenarios = _simulate_scenario_generation(profiles, 10)
        assert len(scenarios) == 10
        assert len(set(scenarios)) == 10, f"profiles={profiles}: expected 10 unique, got {len(set(scenarios))}"


def test_deterministic_reproducibility():
    """Identical inputs must produce identical scenario sequences on repeated calls."""
    for profiles in [["QUALITY"], ["FEATURE", "QUALITY"], ["BUDGET", "SPEED", "QUALITY", "FEATURE", "BALANCED"]]:
        run_a = _simulate_scenario_generation(profiles, 20)
        run_b = _simulate_scenario_generation(profiles, 20)
        assert run_a == run_b, f"profiles={profiles}: scenario generation is not deterministic!"


def test_first_10_and_second_10_differ_with_2_personas():
    """Regression: with 2 personas, second batch of 10 scenarios ≠ first batch."""
    profiles = ["FEATURE", "QUALITY"]
    scenarios = _simulate_scenario_generation(profiles, 20)
    assert scenarios[:10] != scenarios[10:], (
        "Scenarios 11-20 are identical to 1-10 with 2 personas selected."
    )


def test_first_10_and_second_10_differ_with_1_persona():
    """Regression: with 1 persona, second batch of 10 scenarios ≠ first batch."""
    for persona in ["QUALITY", "BUDGET"]:
        scenarios = _simulate_scenario_generation([persona], 20)
        assert scenarios[:10] != scenarios[10:], (
            f"1-persona [{persona}]: scenarios 11-20 are identical to 1-10."
        )


def test_intent_combinations_are_meaningfully_different():
    """
    Extended scenarios must differ in at least one constraint dimension
    (budget, requirements, or deadline) from every base scenario for the same persona.
    """
    for persona_key in SCENARIO_VARIANTS:
        pool = _build_expanded_variant_pool(persona_key)
        n_base = len(SCENARIO_VARIANTS[persona_key])
        base_set = set(pool[:n_base])
        for entry in pool[n_base:]:
            assert entry not in base_set, (
                f"{persona_key}: extended entry {entry} duplicates a base variant."
            )


# ─────────────────────────────────────────────
# Pre-existing structural tests (unchanged)
# ─────────────────────────────────────────────

def test_scenario_variants_are_distinct():
    """Verify the first 5 variants for a persona do not all have identical intent configurations."""
    feature_variants = SCENARIO_VARIANTS.get("FEATURE")
    assert feature_variants is not None
    assert len(feature_variants) == 5
    intent_specs = set()
    for variant in feature_variants:
        label, max_budget, requirements, deadline = variant
        intent_specs.add((max_budget, tuple(requirements), deadline))
    assert len(intent_specs) > 1


def test_scenario_cycle_wraps_deterministically():
    budget_variants = SCENARIO_VARIANTS.get("BUDGET")
    n = len(budget_variants)
    for i in range(n * 3):
        expected = budget_variants[i % n]
        actual = budget_variants[i % len(budget_variants)]
        assert expected == actual


def test_budget_ordering_semantics():
    """Verify that 'low', 'mid', 'high' budget variants represent logically increasing limits."""
    for persona, variants in SCENARIO_VARIANTS.items():
        low_budget = next((v[1] for v in variants if 'low' in v[0] or 'tight' in v[0] or 'essentials' in v[0]), None)
        high_budget = next((v[1] for v in variants if 'high' in v[0] or 'premium' in v[0] or 'complete' in v[0]), None)
        if low_budget and high_budget:
            assert low_budget < high_budget, f"{persona} budget ordering failed"


def test_variant_requirements_validity():
    for persona, variants in SCENARIO_VARIANTS.items():
        for variant in variants:
            label, max_budget, requirements, deadline = variant
            for req in requirements:
                assert req in ["warranty", "fast_delivery", "return_policy"]


def test_all_personas_have_five_variants():
    for persona, variants in SCENARIO_VARIANTS.items():
        assert len(variants) == 5, f"{persona} has {len(variants)} variants, expected 5"


def test_speed_variants_all_have_deadlines():
    for variant in SCENARIO_VARIANTS["SPEED"]:
        label, budget, requirements, deadline = variant
        assert deadline is not None, f"SPEED variant '{label}' has no deadline"
        assert deadline >= 1


def test_no_duplicate_variants_within_persona():
    for persona, variants in SCENARIO_VARIANTS.items():
        labels = [v[0] for v in variants]
        assert len(labels) == len(set(labels)), f"{persona} has duplicate variant labels"
