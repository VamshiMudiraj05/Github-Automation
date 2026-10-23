"""Pre-commit secret scanner preventing credentials, private keys, and tokens from being committed."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


@dataclass
class SecretViolation:
    rule_name: str
    matched_snippet: str
    file_path: str
    line_number: int


class SecretScanner:
    """Detects leaked API keys, tokens, private keys, and sensitive environment configs."""

    # Regex patterns for common secret signatures
    PATTERNS: List[Tuple[str, re.Pattern]] = [
        ("Private Key Block", re.compile(r"-----BEGIN (RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
        ("GitHub Personal Access Token", re.compile(r"(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})")),
        ("Google API Key / AI Studio", re.compile(r"AIza[0-9A-Za-z-_]{35}")),
        ("OpenAI Secret Key", re.compile(r"sk-[a-zA-Z0-9-_]{40,}")),
        ("Anthropic API Key", re.compile(r"sk-ant-[a-zA-Z0-9-_]{40,}")),
        ("AWS Access Key ID", re.compile(r"\b(AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b")),
        ("Slack Webhook / Bot Token", re.compile(r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,}")),
        ("Generic Password Assignment", re.compile(r"""(?i)(?:password|secret|passwd|token)\s*[:=]\s*["']([^"'\s]{8,})["']""")),
    ]

    # Prohibited files that should never be staged or committed
    PROHIBITED_FILE_NAMES = {
        ".env",
        ".env.local",
        ".env.production",
        "id_rsa",
        "id_ed25519",
        "credentials.json",
        "service-account.json",
    }

    def scan_file_path(self, path: Path) -> List[SecretViolation]:
        """Check if filename itself is prohibited."""
        violations = []
        name = path.name.lower()
        if name in self.PROHIBITED_FILE_NAMES or name.endswith(".key") or name.endswith(".pem"):
            violations.append(
                SecretViolation(
                    rule_name="Prohibited Sensitive File",
                    matched_snippet=str(path),
                    file_path=str(path),
                    line_number=0,
                )
            )
        return violations

    def scan_content(self, content: str, file_path: str = "<memory>") -> List[SecretViolation]:
        """Scan string content (diff or file body) for secret patterns."""
        violations: List[SecretViolation] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            # Skip comments that might explain patterns in documentation or tests
            if "SecretScanner" in line or "re.compile" in line:
                continue

            for rule_name, pattern in self.PATTERNS:
                match = pattern.search(line)
                if match:
                    # Redact middle characters for safe logging
                    raw = match.group(0)
                    if len(raw) > 8:
                        redacted = f"{raw[:3]}...{raw[-3:]}"
                    else:
                        redacted = "***"

                    violations.append(
                        SecretViolation(
                            rule_name=rule_name,
                            matched_snippet=redacted,
                            file_path=file_path,
                            line_number=idx,
                        )
                    )

        return violations

    def scan_git_diff(self, diff_text: str) -> List[SecretViolation]:
        """Scan added lines in a git diff (+ lines)."""
        violations: List[SecretViolation] = []
        current_file = "<diff>"
        lines = diff_text.splitlines()

        for idx, line in enumerate(lines, start=1):
            if line.startswith("+++ b/"):
                current_file = line[6:].strip()
                # Check filename
                violations.extend(self.scan_file_path(Path(current_file)))
                continue

            # Only scan added lines
            if line.startswith("+") and not line.startswith("+++"):
                content_to_check = line[1:]
                file_violations = self.scan_content(content_to_check, file_path=current_file)
                for v in file_violations:
                    v.line_number = idx
                violations.extend(file_violations)

        return violations
