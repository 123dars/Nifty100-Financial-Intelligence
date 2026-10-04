"""Async email service using aiosmtplib + Jinja2 templates."""

from __future__ import annotations

import logging
from email.message import EmailMessage
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader

from app.config import settings

logger = logging.getLogger("app.services.email")

_template_dir = Path(__file__).resolve().parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_template_dir)), autoescape=True)

# Placeholder SMTP credentials are treated as "not configured" so the service
# skips sending (avoids slow connection attempts against real providers).
_SMTP_PLACEHOLDERS = {"you@gmail.com", "your-app-password", "your-email@example.com"}


def _smtp_configured() -> bool:
    if not settings.SMTP_HOST:
        return False
    if settings.SMTP_USER in _SMTP_PLACEHOLDERS:
        return False
    return settings.SMTP_PASS not in _SMTP_PLACEHOLDERS


async def _send(to: str, subject: str, html_body: str) -> None:
    """Low-level send via SMTP."""
    if not _smtp_configured():
        logger.warning("SMTP not configured – skipping email to %s", to)
        return

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(html_body, subtype="html")

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            use_tls=False,
            start_tls=True,
        )
        logger.info("Email sent to %s – %s", to, subject)
    except Exception:
        logger.exception("Failed to send email to %s", to)


def _render(template_name: str, **kwargs: str | int | float) -> str:
    tmpl = _env.get_template(template_name)
    return tmpl.render(**kwargs)


# ── Public helpers ──────────────────────────────────────────────


async def send_welcome_email(to: str, name: str) -> None:
    html = _render("welcome.html", name=name, frontend_url=settings.FRONTEND_URL)
    await _send(to, "Welcome to Village API", html)


async def send_approval_email(to: str, name: str) -> None:
    html = _render("approved.html", name=name, frontend_url=settings.FRONTEND_URL)
    await _send(to, "Your Village API Account Has Been Approved", html)


async def send_rejection_email(to: str, name: str, reason: str) -> None:
    html = _render("rejected.html", name=name, reason=reason)
    await _send(to, "Village API – Account Registration Update", html)


async def send_usage_alert(
    to: str, name: str, pct: int, daily_limit: int
) -> None:
    html = _render(
        "usage_alert.html",
        name=name,
        pct=pct,
        daily_limit=daily_limit,
        frontend_url=settings.FRONTEND_URL,
    )
    await _send(to, f"Village API – {pct}% of Daily Limit Reached", html)
