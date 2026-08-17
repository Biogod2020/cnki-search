from __future__ import annotations

import os

import pytest

from cnki_scholar.service import search_cnki

PENG_TITLE = "SCA3发病年龄的临床预测模型构建与罕见变异关联研究"


@pytest.mark.live
def test_live_search_peng_dissertation() -> None:
    if os.environ.get("RUN_LIVE_CNKI") != "1":
        pytest.skip("set RUN_LIVE_CNKI=1 to hit 知网空间")
    response = search_cnki(PENG_TITLE, field="title")
    assert response.status == "ok", response.error
    hit = next((item for item in response.records if PENG_TITLE in item.title), None)
    assert hit is not None
    assert any(
        host in hit.url
        for host in ("cdmd.cnki.com.cn", "search.cnki.com.cn", "www.cnki.com.cn")
    )


@pytest.mark.live
def test_live_keyword_search_returns_sca3_records() -> None:
    if os.environ.get("RUN_LIVE_CNKI") != "1":
        pytest.skip("set RUN_LIVE_CNKI=1 to hit 知网空间")
    response = search_cnki("脊髓小脑性共济失调3型", field="keyword")
    assert response.status == "ok", response.error
    assert response.returned_count >= 1
    blob = " ".join(item.title for item in response.records)
    assert "脊髓小脑" in blob or "SCA3" in blob or "共济失调" in blob
