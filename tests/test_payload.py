from cnki_scholar.client import build_listresult_payload


def test_keyword_field_maps_to_keywd() -> None:
    payload = build_listresult_payload("脊髓小脑性共济失调3型", field="keyword")
    assert payload["KeyWd"] == "脊髓小脑性共济失调3型"
    assert "Theme" not in payload
    assert payload["Order"] == 1


def test_title_author_advisor_year_and_journal_type() -> None:
    payload = build_listresult_payload(
        "SCA3发病年龄",
        field="title",
        author="彭林柳",
        advisor="江泓",
        year="2023",
        kind="journal",
        sort="date",
        page=2,
    )
    assert payload["Title"] == "SCA3发病年龄"
    assert payload["Author"] == "彭林柳"
    assert payload["Boss"] == "江泓"
    assert payload["Year"] == "2023"
    assert payload["Type"] == 1
    assert payload["ArticleType"] == 1
    assert payload["Order"] == 2
    assert payload["Page"] == 2


def test_author_only_omits_theme() -> None:
    payload = build_listresult_payload("", author="彭林柳")
    assert "Theme" not in payload
    assert payload["Author"] == "彭林柳"
