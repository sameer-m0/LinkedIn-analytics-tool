from app.insights import text_utils as T


def test_nfkc_normalizes_styled_unicode():
    # Fullwidth letters (NFKC-equivalent to ASCII) collapse to plain ASCII.
    assert T.normalize("Ｎｏｗ") == "Now"  # Ｎｏｗ


def test_extract_hashtags_dedup_lowercase():
    tags = T.extract_hashtags("Great launch! #Gaming #gaming #IndiaGaming")
    assert tags == ["gaming", "indiagaming"]


def test_extract_hashtags_from_styled_text():
    # Hashtag written in fullwidth unicode still extracted after NFKC.
    assert "gaming" in T.extract_hashtags("partners #Ｇａｍｉｎｇ")  # fullwidth


def test_extract_mentions():
    assert T.extract_mentions("thanks @PlaySuper and @forbes") == ["PlaySuper", "forbes"]


def test_extract_keywords_skips_stopwords():
    kws = T.extract_keywords("We are building the future of gaming in India. Gaming is huge.")
    assert "gaming" in kws and "india" in kws
    assert "the" not in kws and "are" not in kws


def test_has_link_and_question():
    assert T.has_link("read more https://lnkd.in/abc") is True
    assert T.has_link("no link here") is False
    assert T.has_question("What do you think?") is True


def test_hook_first_line_truncated():
    text = "First line hook here\nsecond line"
    assert T.hook(text) == "First line hook here"
    long = "x" * 200
    assert T.hook(long).endswith("…")


def test_extract_tagged_people_pipe_separated():
    text = "Great work team.\n\nMohit Mohan | Disha Sharma | Sharad Yadav\n\n#vc #gaming"
    assert T.extract_tagged_people(text) == ["Mohit Mohan", "Disha Sharma", "Sharad Yadav"]


def test_extract_tagged_people_space_separated_pairs():
    text = "Thanks all.\n\nKrish Anurag Yashmit Kedia Mohit Mohan\n#startups"
    assert T.extract_tagged_people(text) == ["Krish Anurag", "Yashmit Kedia", "Mohit Mohan"]


def test_extract_tagged_people_none_when_only_prose():
    text = "We are excited to announce our new fund. Read more below. #vc"
    assert T.extract_tagged_people(text) == []
