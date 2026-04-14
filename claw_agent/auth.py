"""Supabase authentication + user management for Claw Agent.

Handles: signup, login, JWT verification, profile management,
plan enforcement, API key management, usage tracking.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")  # Admin only

# Local credential cache (so CLI doesn't require login every launch)
_CRED_DIR = Path.home() / ".claw-agent" / "auth"
_CRED_FILE = _CRED_DIR / "session.json"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass
class Plan:
    id: str
    name: str
    display_name: str
    description: str = ""
    price_monthly: float = 0.0
    price_yearly: float = 0.0
    max_tokens_per_day: int = 50_000
    max_tokens_per_month: int = 1_000_000
    max_sessions: int = 10
    max_turns_per_session: int = 50
    max_tools: int = 10
    max_models: int = 1
    council_access: bool = False
    cloud_models: bool = False
    ultrathink_mode: bool = False
    mcp_access: bool = False
    priority_support: bool = False
    custom_skills: bool = False
    api_access: bool = False
    allowed_models: list[str] = field(default_factory=lambda: ["deepseek-v3.1:671b-cloud"])
    allowed_tools: list[str] | None = None  # None = all tools

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Plan:
        models = row.get("allowed_models")
        if isinstance(models, str):
            models = json.loads(models)
        tools = row.get("allowed_tools")
        if isinstance(tools, str):
            tools = json.loads(tools)
        return cls(
            id=row["id"],
            name=row["name"],
            display_name=row.get("display_name", row["name"]),
            description=row.get("description", ""),
            price_monthly=float(row.get("price_monthly", 0)),
            price_yearly=float(row.get("price_yearly", 0)),
            max_tokens_per_day=int(row.get("max_tokens_per_day", 50_000)),
            max_tokens_per_month=int(row.get("max_tokens_per_month", 1_000_000)),
            max_sessions=int(row.get("max_sessions", 10)),
            max_turns_per_session=int(row.get("max_turns_per_session", 50)),
            max_tools=int(row.get("max_tools", 10)),
            max_models=int(row.get("max_models", 1)),
            council_access=bool(row.get("council_access")),
            cloud_models=bool(row.get("cloud_models")),
            ultrathink_mode=bool(row.get("ultrathink_mode")),
            mcp_access=bool(row.get("mcp_access")),
            priority_support=bool(row.get("priority_support")),
            custom_skills=bool(row.get("custom_skills")),
            api_access=bool(row.get("api_access")),
            allowed_models=models if isinstance(models, list) else ["deepseek-v3.1:671b-cloud"],
            allowed_tools=tools if isinstance(tools, list) else None,
        )

    def model_allowed(self, model: str) -> bool:
        if "*" in self.allowed_models:
            return True
        return any(pattern in model for pattern in self.allowed_models)

    def tool_allowed(self, tool_name: str) -> bool:
        if self.allowed_tools is None:
            return True
        return tool_name in self.allowed_tools

    def tokens_remaining_today(self, used: int) -> int:
        if self.max_tokens_per_day == -1:
            return 999_999_999
        return max(0, self.max_tokens_per_day - used)

    def tokens_remaining_month(self, used: int) -> int:
        if self.max_tokens_per_month == -1:
            return 999_999_999
        return max(0, self.max_tokens_per_month - used)


@dataclass
class UserProfile:
    id: str
    email: str
    display_name: str = ""
    avatar_url: str = ""
    plan: Plan | None = None
    plan_id: str = ""
    role: str = "user"
    tokens_used_today: int = 0
    tokens_used_month: int = 0
    total_tokens_used: int = 0
    total_sessions: int = 0
    total_turns: int = 0
    is_active: bool = True
    is_banned: bool = False
    ban_reason: str = ""
    preferred_model: str = ""
    auto_approve: bool = False
    theme: str = "light"
    last_active: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row: dict[str, Any], plan: Plan | None = None) -> UserProfile:
        return cls(
            id=row["id"],
            email=row.get("email", ""),
            display_name=row.get("display_name", ""),
            avatar_url=row.get("avatar_url", ""),
            plan=plan,
            plan_id=row.get("plan_id", ""),
            role=row.get("role", "user"),
            tokens_used_today=int(row.get("tokens_used_today", 0)),
            tokens_used_month=int(row.get("tokens_used_month", 0)),
            total_tokens_used=int(row.get("total_tokens_used", 0)),
            total_sessions=int(row.get("total_sessions", 0)),
            total_turns=int(row.get("total_turns", 0)),
            is_active=bool(row.get("is_active", True)),
            is_banned=bool(row.get("is_banned", False)),
            ban_reason=row.get("ban_reason", ""),
            preferred_model=row.get("preferred_model", ""),
            auto_approve=bool(row.get("auto_approve", False)),
            theme=row.get("theme", "light"),
            last_active=str(row.get("last_active", "")),
            created_at=str(row.get("created_at", "")),
        )

    @property
    def is_admin(self) -> bool:
        return self.role in ("admin", "superadmin")

    @property
    def is_superadmin(self) -> bool:
        return self.role == "superadmin"

    def can_use_tokens(self, count: int) -> bool:
        if not self.plan:
            return True
        day_ok = self.plan.max_tokens_per_day == -1 or (self.tokens_used_today + count) <= self.plan.max_tokens_per_day
        month_ok = self.plan.max_tokens_per_month == -1 or (self.tokens_used_month + count) <= self.plan.max_tokens_per_month
        return day_ok and month_ok


# ---------------------------------------------------------------------------
# Auth session (cached locally)
# ---------------------------------------------------------------------------
@dataclass
class AuthSession:
    access_token: str = ""
    refresh_token: str = ""
    user_id: str = ""
    email: str = ""
    expires_at: float = 0.0

    @property
    def is_valid(self) -> bool:
        return bool(self.access_token) and self.expires_at > time.time()

    def save(self) -> None:
        _CRED_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "user_id": self.user_id,
            "email": self.email,
            "expires_at": self.expires_at,
        }
        _CRED_FILE.write_text(json.dumps(data), encoding="utf-8")
        # Restrict file permissions (best effort on Windows)
        try:
            _CRED_FILE.chmod(0o600)
        except OSError:
            pass

    @classmethod
    def load(cls) -> AuthSession:
        if not _CRED_FILE.exists():
            return cls()
        try:
            data = json.loads(_CRED_FILE.read_text(encoding="utf-8"))
            return cls(**data)
        except (json.JSONDecodeError, TypeError, KeyError):
            return cls()

    def clear(self) -> None:
        self.access_token = ""
        self.refresh_token = ""
        self.user_id = ""
        self.email = ""
        self.expires_at = 0.0
        if _CRED_FILE.exists():
            _CRED_FILE.unlink()


# ---------------------------------------------------------------------------
# Supabase HTTP client
# ---------------------------------------------------------------------------
class SupabaseClient:
    """Thin REST client for Supabase Auth + PostgREST."""

    def __init__(self, url: str = "", anon_key: str = "", service_key: str = ""):
        self.url = (url or SUPABASE_URL).rstrip("/")
        self.anon_key = anon_key or SUPABASE_ANON_KEY
        self.service_key = service_key or SUPABASE_SERVICE_KEY
        self._http = httpx.Client(timeout=15)

    def close(self) -> None:
        """Close the HTTP client to release connections."""
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def configured(self) -> bool:
        return bool(self.url and self.anon_key)

    # -- Headers ---------------------------------------------------------------
    def _auth_headers(self, token: str = "") -> dict[str, str]:
        key = token or self.anon_key
        return {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def _admin_headers(self) -> dict[str, str]:
        key = self.service_key or self.anon_key
        return {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    # -- Auth ------------------------------------------------------------------
    def signup(self, email: str, password: str, display_name: str = "") -> dict[str, Any]:
        """Register a new user. Returns Supabase auth response."""
        payload: dict[str, Any] = {"email": email, "password": password}
        if display_name:
            payload["data"] = {"display_name": display_name}
        r = self._http.post(
            f"{self.url}/auth/v1/signup",
            json=payload,
            headers=self._auth_headers(),
        )
        return r.json()

    def login(self, email: str, password: str) -> dict[str, Any]:
        """Email/password login. Returns access_token, refresh_token, user."""
        r = self._http.post(
            f"{self.url}/auth/v1/token?grant_type=password",
            json={"email": email, "password": password},
            headers=self._auth_headers(),
        )
        return r.json()

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        """Refresh an expired access token."""
        r = self._http.post(
            f"{self.url}/auth/v1/token?grant_type=refresh_token",
            json={"refresh_token": refresh_token},
            headers=self._auth_headers(),
        )
        return r.json()

    def logout(self, access_token: str) -> bool:
        """Invalidate the current session."""
        r = self._http.post(
            f"{self.url}/auth/v1/logout",
            headers=self._auth_headers(access_token),
        )
        return r.status_code < 300

    def get_user(self, access_token: str) -> dict[str, Any]:
        """Get current user from JWT."""
        r = self._http.get(
            f"{self.url}/auth/v1/user",
            headers=self._auth_headers(access_token),
        )
        return r.json()

    # -- PostgREST (profiles, plans, usage) ------------------------------------
    def _rest(self, table: str, method: str = "GET", token: str = "",
              params: dict | None = None, data: dict | None = None,
              use_admin: bool = False) -> Any:
        url = f"{self.url}/rest/v1/{table}"
        headers = self._admin_headers() if use_admin else self._auth_headers(token)
        if method == "GET":
            headers["Accept"] = "application/json"
            r = self._http.get(url, headers=headers, params=params or {})
        elif method == "POST":
            headers["Prefer"] = "return=representation"
            r = self._http.post(url, headers=headers, json=data, params=params or {})
        elif method == "PATCH":
            headers["Prefer"] = "return=representation"
            r = self._http.patch(url, headers=headers, json=data, params=params or {})
        elif method == "DELETE":
            r = self._http.delete(url, headers=headers, params=params or {})
        else:
            raise ValueError(f"Unknown method: {method}")
        if r.status_code >= 400:
            return {"error": r.text, "status": r.status_code}
        try:
            return r.json()
        except Exception:
            return {"ok": True}

    # -- Profile ---------------------------------------------------------------
    def get_profile(self, user_id: str, token: str = "") -> dict[str, Any] | None:
        rows = self._rest("profiles", params={"id": f"eq.{user_id}", "select": "*"}, token=token)
        if isinstance(rows, list) and rows:
            return rows[0]
        return None

    def update_profile(self, user_id: str, updates: dict[str, Any], token: str = "") -> dict:
        result = self._rest("profiles", method="PATCH", data=updates,
                            params={"id": f"eq.{user_id}"}, token=token)
        return result if isinstance(result, dict) else {}

    def get_all_profiles(self, token: str = "") -> list[dict]:
        """Admin: get all user profiles."""
        result = self._rest("profiles", params={"select": "*,plans(*)", "order": "created_at.desc"},
                            use_admin=True)
        return result if isinstance(result, list) else []

    # -- Plans -----------------------------------------------------------------
    def get_plans(self, token: str = "") -> list[dict]:
        result = self._rest("plans", params={"select": "*", "order": "sort_order.asc", "is_active": "eq.true"}, token=token)
        return result if isinstance(result, list) else []

    def get_plan(self, plan_id: str, token: str = "") -> dict | None:
        rows = self._rest("plans", params={"id": f"eq.{plan_id}", "select": "*"}, token=token)
        if isinstance(rows, list) and rows:
            return rows[0]
        return None

    def create_plan(self, data: dict[str, Any]) -> dict:
        return self._rest("plans", method="POST", data=data, use_admin=True)

    def update_plan(self, plan_id: str, updates: dict[str, Any]) -> dict:
        return self._rest("plans", method="PATCH", data=updates,
                          params={"id": f"eq.{plan_id}"}, use_admin=True)

    def delete_plan(self, plan_id: str) -> dict:
        return self._rest("plans", method="DELETE",
                          params={"id": f"eq.{plan_id}"}, use_admin=True)

    # -- Usage Logs ------------------------------------------------------------
    def log_usage(self, user_id: str, session_id: str, model: str,
                  prompt_tokens: int, completion_tokens: int, total_tokens: int,
                  tool_calls: int, duration_ms: float, plan_id: str = "",
                  token: str = "") -> dict:
        data = {
            "user_id": user_id,
            "session_id": session_id,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "tool_calls": tool_calls,
            "duration_ms": duration_ms,
        }
        if plan_id:
            data["plan_id"] = plan_id
        return self._rest("usage_logs", method="POST", data=data, token=token)

    def get_usage(self, user_id: str, token: str = "", limit: int = 100) -> list[dict]:
        return self._rest("usage_logs", params={
            "user_id": f"eq.{user_id}", "select": "*",
            "order": "created_at.desc", "limit": str(limit)
        }, token=token) or []

    def get_all_usage(self, limit: int = 500) -> list[dict]:
        """Admin: get all usage logs."""
        result = self._rest("usage_logs", params={
            "select": "*,profiles(email,display_name)",
            "order": "created_at.desc", "limit": str(limit)
        }, use_admin=True)
        return result if isinstance(result, list) else []

    # -- API Keys --------------------------------------------------------------
    def create_api_key(self, user_id: str, name: str = "Default", token: str = "") -> tuple[str, dict]:
        """Generate + store a new API key. Returns (raw_key, row)."""
        raw_key = f"claw_{secrets.token_hex(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12]
        data = {
            "user_id": user_id,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "name": name,
        }
        result = self._rest("api_keys", method="POST", data=data, token=token)
        return raw_key, result

    def verify_api_key(self, raw_key: str) -> dict | None:
        """Verify an API key and return the profile. Uses service key (no user auth)."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        rows = self._rest("api_keys", params={
            "key_hash": f"eq.{key_hash}", "is_active": "eq.true", "select": "*"
        }, use_admin=True)
        if isinstance(rows, list) and rows:
            key_row = rows[0]
            # Check expiry
            if key_row.get("expires_at"):
                from datetime import datetime, timezone
                exp = datetime.fromisoformat(key_row["expires_at"].replace("Z", "+00:00"))
                if exp < datetime.now(timezone.utc):
                    return None
            # Update last_used
            self._rest("api_keys", method="PATCH",
                       data={"last_used": "now()"},
                       params={"id": f"eq.{key_row['id']}"}, use_admin=True)
            return key_row
        return None

    def list_api_keys(self, user_id: str, token: str = "") -> list[dict]:
        result = self._rest("api_keys", params={
            "user_id": f"eq.{user_id}", "select": "id,key_prefix,name,is_active,last_used,created_at",
            "order": "created_at.desc"
        }, token=token)
        return result if isinstance(result, list) else []

    def delete_api_key(self, key_id: str, user_id: str, token: str = "") -> dict:
        return self._rest("api_keys", method="DELETE",
                          params={"id": f"eq.{key_id}", "user_id": f"eq.{user_id}"}, token=token)

    # -- Admin -----------------------------------------------------------------
    def admin_update_user(self, admin_id: str, target_user_id: str,
                          updates: dict[str, Any]) -> dict:
        """Admin: update any user's profile + log the action."""
        result = self._rest("profiles", method="PATCH", data=updates,
                            params={"id": f"eq.{target_user_id}"}, use_admin=True)
        # Audit log
        self._rest("admin_audit_log", method="POST", data={
            "admin_id": admin_id,
            "action": "update_user",
            "target_user_id": target_user_id,
            "details": updates,
        }, use_admin=True)
        return result

    def admin_ban_user(self, admin_id: str, target_user_id: str, reason: str = "") -> dict:
        return self.admin_update_user(admin_id, target_user_id, {
            "is_banned": True, "ban_reason": reason, "is_active": False
        })

    def admin_unban_user(self, admin_id: str, target_user_id: str) -> dict:
        return self.admin_update_user(admin_id, target_user_id, {
            "is_banned": False, "ban_reason": "", "is_active": True
        })

    def admin_change_plan(self, admin_id: str, target_user_id: str, plan_id: str) -> dict:
        result = self._rest("profiles", method="PATCH", data={"plan_id": plan_id},
                            params={"id": f"eq.{target_user_id}"}, use_admin=True)
        self._rest("admin_audit_log", method="POST", data={
            "admin_id": admin_id,
            "action": "change_plan",
            "target_user_id": target_user_id,
            "details": {"plan_id": plan_id},
        }, use_admin=True)
        return result

    def admin_change_role(self, admin_id: str, target_user_id: str, new_role: str) -> dict:
        if new_role not in ("user", "admin", "superadmin"):
            return {"error": f"Invalid role: {new_role}"}
        return self.admin_update_user(admin_id, target_user_id, {"role": new_role})

    def admin_get_audit_log(self, limit: int = 200) -> list[dict]:
        result = self._rest("admin_audit_log", params={
            "select": "*,profiles!admin_audit_log_admin_id_fkey(email,display_name)",
            "order": "created_at.desc", "limit": str(limit)
        }, use_admin=True)
        return result if isinstance(result, list) else []

    def admin_get_stats(self) -> dict[str, Any]:
        """Admin dashboard aggregate stats."""
        profiles = self.get_all_profiles()
        usage = self.get_all_usage(limit=1000)
        plans = self.get_plans()

        total_users = len(profiles)
        active_users = sum(1 for p in profiles if p.get("is_active") and not p.get("is_banned"))
        banned_users = sum(1 for p in profiles if p.get("is_banned"))
        total_tokens = sum(u.get("total_tokens", 0) for u in usage)
        total_tool_calls = sum(u.get("tool_calls", 0) for u in usage)

        # Users per plan
        plan_counts: dict[str, int] = {}
        for p in profiles:
            pid = p.get("plan_id", "none")
            plan_counts[pid] = plan_counts.get(pid, 0) + 1

        return {
            "total_users": total_users,
            "active_users": active_users,
            "banned_users": banned_users,
            "total_tokens": total_tokens,
            "total_tool_calls": total_tool_calls,
            "total_sessions": sum(p.get("total_sessions", 0) for p in profiles),
            "users_per_plan": plan_counts,
            "plan_count": len(plans),
        }

    # -- Announcements ---------------------------------------------------------
    def create_announcement(self, admin_id: str, title: str, content: str,
                            ann_type: str = "info") -> dict:
        return self._rest("announcements", method="POST", data={
            "admin_id": admin_id, "title": title, "content": content, "type": ann_type,
        }, use_admin=True)

    def get_announcements(self, token: str = "") -> list[dict]:
        result = self._rest("announcements", params={
            "is_active": "eq.true", "select": "*",
            "order": "created_at.desc", "limit": "10"
        }, token=token)
        return result if isinstance(result, list) else []


# ---------------------------------------------------------------------------
# High-level auth manager (used by CLI + API)
# ---------------------------------------------------------------------------
class AuthManager:
    """Manages authentication state for the Claw Agent CLI."""

    def __init__(self):
        self.client = SupabaseClient()
        self.session = AuthSession.load()
        self._profile: UserProfile | None = None
        self._plan: Plan | None = None

    @property
    def configured(self) -> bool:
        return self.client.configured

    @property
    def logged_in(self) -> bool:
        if self.session.is_valid:
            return True
        # Try refresh
        if self.session.refresh_token:
            return self._try_refresh()
        return False

    @property
    def user_id(self) -> str:
        return self.session.user_id

    @property
    def email(self) -> str:
        return self.session.email

    @property
    def profile(self) -> UserProfile | None:
        if self._profile is None and self.logged_in:
            self._load_profile()
        return self._profile

    @property
    def plan(self) -> Plan | None:
        if self._plan is None and self.profile and self.profile.plan_id:
            plan_row = self.client.get_plan(self.profile.plan_id, self.session.access_token)
            if plan_row and "error" not in plan_row:
                self._plan = Plan.from_row(plan_row)
                if self._profile is not None:
                    self._profile.plan = self._plan
        return self._plan

    def signup(self, email: str, password: str, display_name: str = "") -> tuple[bool, str]:
        if not self.configured:
            return False, "Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY."
        result = self.client.signup(email, password, display_name)
        if "error" in result:
            err = result.get("error_description") or result.get("msg") or str(result["error"])
            return False, f"Signup failed: {err}"
        if result.get("access_token"):
            self._save_session(result)
            return True, f"Account created! Welcome, {display_name or email}."
        return True, "Check your email to confirm your account."

    def login(self, email: str, password: str) -> tuple[bool, str]:
        if not self.configured:
            return False, "Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY."
        result = self.client.login(email, password)
        if "error" in result:
            err = result.get("error_description") or result.get("msg") or str(result["error"])
            return False, f"Login failed: {err}"
        if not result.get("access_token"):
            return False, "Login failed: no access token returned."
        self._save_session(result)
        self._load_profile()

        # Check if banned
        if self._profile and self._profile.is_banned:
            reason = self._profile.ban_reason or "No reason given"
            self.logout()
            return False, f"Account banned: {reason}"

        plan_name = self._plan.display_name if self._plan else "Free"
        return True, f"Welcome back, {self._profile.display_name if self._profile else email}! Plan: {plan_name}"

    def logout(self) -> tuple[bool, str]:
        if self.session.access_token:
            self.client.logout(self.session.access_token)
        self.session.clear()
        self._profile = None
        self._plan = None
        return True, "Logged out."

    def check_token_budget(self, tokens: int) -> tuple[bool, str]:
        """Check if user can consume `tokens` more tokens."""
        if not self.logged_in or not self.profile:
            return True, ""  # No auth = no limits (local mode)
        if not self.plan:
            return True, ""
        if not self.profile.can_use_tokens(tokens):
            day_left = self.plan.tokens_remaining_today(self.profile.tokens_used_today)
            month_left = self.plan.tokens_remaining_month(self.profile.tokens_used_month)
            return False, (
                f"Token limit reached ({self.plan.display_name} plan). "
                f"Day: {day_left:,} left, Month: {month_left:,} left. "
                f"Upgrade your plan for more."
            )
        return True, ""

    def record_usage(self, session_id: str, model: str, prompt_tokens: int,
                     completion_tokens: int, total_tokens: int,
                     tool_calls: int, duration_ms: float) -> None:
        """Record token usage to Supabase and update profile counters."""
        if not self.logged_in:
            return
        # Log to usage_logs table
        self.client.log_usage(
            user_id=self.user_id,
            session_id=session_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            tool_calls=tool_calls,
            duration_ms=duration_ms,
            plan_id=self.profile.plan_id if self.profile else "",
            token=self.session.access_token,
        )
        # Update profile counters
        if self.profile:
            self.client.update_profile(self.user_id, {
                "tokens_used_today": self.profile.tokens_used_today + total_tokens,
                "tokens_used_month": self.profile.tokens_used_month + total_tokens,
                "total_tokens_used": self.profile.total_tokens_used + total_tokens,
                "total_turns": self.profile.total_turns + 1,
                "last_active": "now()",
            }, self.session.access_token)
            # Update local cache
            self.profile.tokens_used_today += total_tokens
            self.profile.tokens_used_month += total_tokens
            self.profile.total_tokens_used += total_tokens
            self.profile.total_turns += 1

    def check_model_access(self, model: str) -> tuple[bool, str]:
        """Check if user's plan allows this model."""
        if not self.logged_in or not self.plan:
            return True, ""
        if not self.plan.model_allowed(model):
            return False, f"Model '{model}' not available on {self.plan.display_name} plan. Upgrade for access."
        return True, ""

    def check_tool_access(self, tool_name: str) -> tuple[bool, str]:
        """Check if user's plan allows this tool."""
        if not self.logged_in or not self.plan:
            return True, ""
        if not self.plan.tool_allowed(tool_name):
            return False, f"Tool '{tool_name}' not available on {self.plan.display_name} plan."
        return True, ""

    def check_council_access(self) -> tuple[bool, str]:
        if not self.logged_in or not self.plan:
            return True, ""
        if not self.plan.council_access:
            return False, f"Council mode requires UltraThink plan or higher. Current: {self.plan.display_name}"
        return True, ""

    def check_ultrathink_access(self) -> tuple[bool, str]:
        if not self.logged_in or not self.plan:
            return True, ""
        if not self.plan.ultrathink_mode:
            return False, f"UltraThink mode requires UltraThink plan or higher. Current: {self.plan.display_name}"
        return True, ""

    # -- Private ---------------------------------------------------------------
    def _save_session(self, auth_result: dict) -> None:
        self.session = AuthSession(
            access_token=auth_result["access_token"],
            refresh_token=auth_result.get("refresh_token", ""),
            user_id=auth_result.get("user", {}).get("id", ""),
            email=auth_result.get("user", {}).get("email", ""),
            expires_at=time.time() + auth_result.get("expires_in", 3600),
        )
        self.session.save()

    def _try_refresh(self) -> bool:
        result = self.client.refresh(self.session.refresh_token)
        if "error" in result or not result.get("access_token"):
            self.session.clear()
            return False
        self._save_session(result)
        return True

    def _load_profile(self) -> None:
        if not self.session.user_id:
            return
        row = self.client.get_profile(self.session.user_id, self.session.access_token)
        if not row:
            return
        # Load plan
        plan_id = row.get("plan_id")
        if plan_id:
            plan_row = self.client.get_plan(plan_id, self.session.access_token)
            if plan_row and "error" not in plan_row:
                self._plan = Plan.from_row(plan_row)
        self._profile = UserProfile.from_row(row, self._plan)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_auth_manager: AuthManager | None = None


def get_auth_manager() -> AuthManager:
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
