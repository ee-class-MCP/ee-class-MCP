"""Tests for the pure helpers behind PlaywrightAuthProvider (no browser needed)."""

from eeclass_mcp.client.auth import (
    _describe_payload,
    _is_login_path,
    _pick_confirm_button,
    _rejection_message,
)


def test_is_login_path() -> None:
    assert _is_login_path("https://ncueeclass.ncu.edu.tw/index/login")
    assert _is_login_path("https://ncueeclass.ncu.edu.tw/index/login?next=%2F")
    assert not _is_login_path("https://ncueeclass.ncu.edu.tw/dashboard")


def test_rejection_message() -> None:
    assert _rejection_message({"ret": {"status": "false", "msg": "帳號或密碼錯誤"}}) == (
        "帳號或密碼錯誤"
    )
    assert _rejection_message({"ret": {"status": "false"}})
    assert _rejection_message({"ret": {"status": "true", "action": {}}}) is None
    assert _rejection_message(None) is None


def test_describe_payload_hides_query_strings() -> None:
    summary = _describe_payload(
        {"ret": {"status": "true", "action": {"redir": "/dashboard?ajaxAuth=secret"}}}
    )
    assert "action.redir='/dashboard'" in summary
    assert "secret" not in summary


def _btn(i: int, text: str, **extra: str) -> dict:
    return {"i": i, "text": text, "visible": True, **extra}


def test_multi_login_prefers_keep_login() -> None:
    # Real modal: "此帳號已在其他的位置登入…" with these two links.
    buttons = [_btn(0, "登出所有裝置", tag="a"), _btn(1, "保持登入", tag="a")]
    assert _pick_confirm_button(buttons) == 1


def test_multi_login_never_logs_out_other_devices() -> None:
    assert _pick_confirm_button([_btn(0, "登出所有裝置")]) is None


def test_multi_login_skips_cancel_buttons() -> None:
    buttons = [
        _btn(0, "×", dismiss="modal"),
        _btn(1, "取消", role="form-cancel"),
        _btn(2, "確定", type="button"),
    ]
    assert _pick_confirm_button(buttons) == 2
