"""Application configuration and stable selectors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WebAppConfig:
    """Configuration for the target web application.

    Parameters
    ----------
    base_url:
        Base URL of the web application.
    login_url:
        Login endpoint URL.
    """

    base_url: str
    login_url: str


WEB_APP_CONFIG = WebAppConfig(
    base_url="https://cap-dev.notmyrealname.fyi",
    login_url="https://cap-dev.notmyrealname.fyi/auth/login",
)


@dataclass(frozen=True)
class WebSelectors:
    """CSS selectors used by automation.

    Notes
    -----
    These selectors match the IDs/classes shown in your developer tools screenshots.
    """

    profile_anchor: str = "a#profile"
    login_username: str = "#login-field-username"
    login_password: str = "#login-field-password"
    login_submit: str = "button[type='submit']"

    modal_body_visible: str = "div.modal.show div.modal-body"
    modal_close_visible: str = "div.modal.show button.btn.btn-secondary:has-text('Close')"

    listplayers_textarea: str = "#listplayerdata"
    listplayers_submit: str = "form#post-form button[type='submit']"


SELECTORS = WebSelectors()


@dataclass(frozen=True)
class GameConfig:
    """Configuration for the in-game console automation."""

    # Virtual-key code for the console key.
    # VK_OEM_3 (0xC0) is the key typically used for ` / ~ on US keyboards.
    console_open_vk: int = 0xC0
    # Scan code for the same physical key (fallback if VK mapping fails).
    console_open_scan_code: int = 0x29
    focus_delay_s: float = 2.0
    click_to_focus: bool = False
    after_escape_delay_s: float = 0.15
    console_open_delay_s: float = 1.0
    after_command_delay_s: float = 0.2
    pre_console_escape: bool = True


GAME_CONFIG = GameConfig()
