"""
Content policy validator.

Validates that content complies with content policies (simulated).
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from fakeai.validation.base import ValidationResult


class ContentPolicyValidator:
    """
    Validator that checks content against content policies.

    This is a simulated content policy validator that checks for obvious
    policy violations. In a real system, this would integrate with a
    content moderation service.
    """

    # Keywords that might indicate policy violations (simplified)
    FLAGGED_KEYWORDS = {
        "illegal",
        "hack",
        "exploit",
        "malware",
        "virus",
        "crack",
        "pirate",
        "stolen",
        "counterfeit",
    }

    def __init__(
        self,
        strict_mode: bool = False,
        name: str = "ContentPolicyValidator",
    ):
        """
        Initialize the content policy validator.

        Args:
            strict_mode: If True, apply stricter checks
            name: Name for this validator
        """
        self._strict_mode = strict_mode
        self._name = name

    @property
    def name(self) -> str:
        """Get the name of this validator."""
        return self._name

    def validate(
        self, request: Any, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Validate content policy compliance.

        Expected context keys:
            - content: Text content to check (optional)
            - messages: List of messages to check (optional)

        Args:
            request: The request object
            context: Context containing content to check

        Returns:
            ValidationResult indicating success or failure
        """
        result = ValidationResult.success()
        context = context or {}

        # Collect all content to check
        content_to_check = []

        # Check single content field
        if "content" in context and context["content"]:
            content_to_check.append(context["content"])

        # Check messages
        if "messages" in context and context["messages"]:
            messages = context["messages"]
            for msg in messages:
                if isinstance(msg, dict) and "content" in msg:
                    content = msg["content"]
                    if isinstance(content, str):
                        content_to_check.append(content)
                elif hasattr(msg, "content") and msg.content:
                    content = msg.content
                    if isinstance(content, str):
                        content_to_check.append(content)

        # Extract content from request if available
        if hasattr(request, "messages"):
            for msg in request.messages:
                if hasattr(msg, "content") and msg.content:
                    if isinstance(msg.content, str):
                        content_to_check.append(msg.content)

        # Check for policy violations
        violations_found = []
        for content in content_to_check:
            if not isinstance(content, str):
                continue

            content_lower = content.lower()

            # Check for flagged keywords
            found_keywords = [
                keyword
                for keyword in self.FLAGGED_KEYWORDS
                if keyword in content_lower
            ]

            if found_keywords:
                violations_found.extend(found_keywords)

        # Report violations
        if violations_found:
            unique_violations = list(set(violations_found))

            if self._strict_mode:
                result.add_error(
                    message=f"Content may violate usage policies. Flagged terms: {', '.join(unique_violations)}",
                    code="content_policy_violation",
                    param="content",
                )
            else:
                result.add_warning(
                    message=f"Content may violate usage policies. Flagged terms: {', '.join(unique_violations)}",
                    code="content_policy_warning",
                    param="content",
                )

            result.metadata["flagged_terms"] = unique_violations

        # Additional checks for very long content (possible abuse)
        total_length = sum(len(c) for c in content_to_check)
        if total_length > 1_000_000:  # 1M characters
            result.add_warning(
                message=f"Content is very large ({total_length} characters). This may indicate abuse.",
                code="large_content_warning",
                param="content",
            )

        return result
