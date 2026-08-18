from models.schemas import EligibilityStatus, UserProfile


def test_merge_fills_missing_fields_only():
    base = UserProfile(age=22, gender="female")
    update = UserProfile(state="Himachal Pradesh")

    merged = base.merge(update)

    assert merged.age == 22
    assert merged.gender == "female"
    assert merged.state == "Himachal Pradesh"


def test_merge_overrides_with_new_non_null_values():
    base = UserProfile(age=22)
    update = UserProfile(age=23)

    merged = base.merge(update)

    assert merged.age == 23


def test_merge_does_not_mutate_originals():
    base = UserProfile(age=22)
    update = UserProfile(state="Delhi")

    base.merge(update)

    assert base.state is None
    assert update.age is None


def test_eligibility_status_values_are_stable():
    # These string values are relied on by the LLM JSON schema contract.
    assert EligibilityStatus.ELIGIBLE.value == "eligible"
    assert EligibilityStatus.LIKELY_ELIGIBLE.value == "likely_eligible"
    assert EligibilityStatus.NOT_ELIGIBLE.value == "not_eligible"
    assert EligibilityStatus.INSUFFICIENT_INFO.value == "insufficient_info"
