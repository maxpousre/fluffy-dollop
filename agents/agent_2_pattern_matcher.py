"""
Agent 2: System-Specific Pattern Matcher

Purpose: Map parts using validated examples and system-specific rules.

Key Responsibilities:
- Apply pattern matching rules from system-specific rules files
- Check against validated parts database for this system
- Determine if web search is needed
- Assign confidence scores

Processing:
- Batch Size: 5-10 parts (all same system code)
- Context: System-specific rules + validated parts for this system only
- Output: High-confidence mappings + parts flagged for web search

Configuration:
- Model: claude-3-5-haiku-20241022 (cost-optimized)
- Temperature: 0.0 (deterministic)
- Max Tokens: 3000
"""

import logging
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class PatternMatcher:
    """
    Agent 2: Maps parts using pattern matching and validated examples.
    """

    def __init__(self, claude_client, config: Dict):
        """
        Initialize the Pattern Matcher agent.

        Args:
            claude_client: Instance of Claude API client
            config: Configuration dictionary with model parameters
        """
        self.claude_client = claude_client
        self.config = config
        logger.info("Agent 2: Pattern Matcher initialized")

    def match_parts(
        self,
        parts_batch: List[Dict],
        system_code: str,
        rules: str,
        validated_parts: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Match parts using pattern matching.

        Args:
            parts_batch: Batch of 5-10 parts (all same system)
            system_code: VMRS system code (e.g., "13")
            rules: System-specific rules content
            validated_parts: Previously validated parts for this system

        Returns:
            Dictionary with 'high_confidence' and 'needs_web_search' lists
        """
        logger.info(f"Pattern matching {len(parts_batch)} parts for System {system_code}")

        # TODO: Implement pattern matching logic
        # 1. Build prompt with rules and validated parts
        # 2. Call Claude API with parts batch
        # 3. Parse response
        # 4. Categorize by confidence and web search needs
        # 5. Return categorized parts

        raise NotImplementedError("Pattern matching logic to be implemented")

    def _build_prompt(
        self,
        parts_batch: List[Dict],
        system_code: str,
        rules: str,
        validated_parts: List[Dict]
    ) -> str:
        """
        Build the pattern matching prompt for Claude.

        Args:
            parts_batch: Parts to match
            system_code: VMRS system code
            rules: System-specific rules
            validated_parts: Validated parts database

        Returns:
            Formatted prompt string
        """
        # TODO: Implement prompt building
        raise NotImplementedError("Prompt building to be implemented")

    def _validate_output(self, response: Dict) -> bool:
        """
        Validate the pattern matching output.

        Args:
            response: Response from Claude API

        Returns:
            True if valid, False otherwise
        """
        # TODO: Implement validation
        raise NotImplementedError("Output validation to be implemented")
