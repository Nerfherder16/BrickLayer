from bl.question_weights import should_flag_human, NEEDS_HUMAN_THRESHOLD


def test_should_flag_human_below_threshold():
    assert should_flag_human(0.3) is True


def test_should_flag_human_at_threshold():
    # Boundary: 0.35 is NOT below threshold
    assert should_flag_human(NEEDS_HUMAN_THRESHOLD) is False


def test_should_flag_human_above_threshold():
    assert should_flag_human(0.9) is False


def test_should_flag_human_zero():
    assert should_flag_human(0.0) is True
