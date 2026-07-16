from app.judge.comparator import compare_output, normalize_output

def test_crlf_normalized():
    assert compare_output("3\r\n", "3\n") is True

def test_cr_normalized():
    assert compare_output("3\r", "3\n") is True

def test_lf_unchanged():
    assert normalize_output("3\n") == "3\n"

def test_trailing_spaces_ignored():
    assert compare_output("3   \n", "3\n") is True

def test_trailing_tabs_ignored():
    assert compare_output("3\t\t\n", "3\n") is True

def test_multiline_trailing_whitespace():
    assert compare_output("1   \n2   \n3   \n", "1\n2\n3\n") is True

def test_trailing_extra_newlines_ignored():
    assert compare_output("3\n\n\n", "3\n") is True

def test_no_trailing_newline_still_matches():
    assert compare_output("3", "3\n") is True
    assert compare_output("3\n", "3") is True

def test_middle_blank_lines_preserved():
    assert compare_output("1\n\n3\n", "1\n\n3\n") is True
    assert compare_output("1\n3\n", "1\n\n3\n") is False

def test_leading_spaces_significant():
    assert compare_output(" 3\n", "3\n") is False

def test_internal_spaces_significant():
    assert compare_output("3 4\n", "34\n") is False
    assert compare_output("3  4\n", "3 4\n") is False

def test_extra_prompt_rejected():
    assert compare_output("Answer: 3\n", "3\n") is False
    assert compare_output("结果是 3\n", "3\n") is False

def test_doc_example_ac():
    assert compare_output("3\n", "3\n") is True

def test_doc_example_wa():
    assert compare_output("答案是 3\n", "3\n") is False

def test_empty_outputs_match():
    assert compare_output("", "") is True
    assert compare_output("\n", "") is True
    assert compare_output("", "\n") is True

def test_empty_vs_nonempty_differ():
    assert compare_output("", "3\n") is False
    assert compare_output("3\n", "") is False

def test_multiline_match():
    actual = "1\n2\n3\n"
    expected = "1\n2\n3\n"
    assert compare_output(actual, expected) is True

def test_multiline_partial_mismatch():
    actual = "1\n2\n4\n"
    expected = "1\n2\n3\n"
    assert compare_output(actual, expected) is False