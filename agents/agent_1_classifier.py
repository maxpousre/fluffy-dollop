"""
Agent 1: System Classifier & Customer Catalog Matcher

Purpose: Initial classification of parts into VMRS system codes and direct matching
         against customer's specific catalog.

Key Responsibilities:
- Classify all parts into VMRS system codes (10, 13, 17, etc.)
- Attempt direct/fuzzy matching in customer catalog
- Route parts to appropriate next stage
- Group output by system code

Processing:
- Batch Size: ALL parts in one execution
- Context: System-level catalog only (not detailed codes)
- Output: parts_grouped_by_system.json

Configuration:
- Model: claude-3-5-haiku-20241022 (cost-optimized)
- Temperature: 0.0 (deterministic)
- Max Tokens: 4000
"""

import json
import logging
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SystemClassifier:
    """
    Agent 1: Classifies parts into VMRS system codes and matches against customer catalog.
    """

    def __init__(self, claude_client, customer_catalog: List[Dict], config: Dict):
        """
        Initialize the System Classifier agent.

        Args:
            claude_client: Instance of Claude API client
            customer_catalog: Customer's VMRS catalog (system-level)
            config: Configuration dictionary with model parameters
        """
        self.claude_client = claude_client
        self.customer_catalog = customer_catalog
        self.config = config
        logger.info("Agent 1: System Classifier initialized")

    def classify_parts(self, parts: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Classify all parts into VMRS system codes.

        Args:
            parts: List of parts with part_code and part_name

        Returns:
            Dictionary with system codes as keys and lists of classified parts
        """
        logger.info(f"Classifying {len(parts)} parts")

        # TODO: Implement classification logic using Claude API
        # 1. Prepare prompt with customer catalog systems
        # 2. Call Claude API with all parts
        # 3. Parse response and validate JSON schema
        # 4. Group by system code
        # 5. Return grouped parts

        raise NotImplementedError("Classification logic to be implemented")

    def _build_prompt(self, parts: List[Dict]) -> str:
        """
        Build the classification prompt for Claude.

        Args:
            parts: List of parts to classify

        Returns:
            Formatted prompt string
        """
        # TODO: Implement prompt building
        raise NotImplementedError("Prompt building to be implemented")

    def _validate_output(self, response: Dict) -> bool:
        """
        Validate the classification output against expected schema.

        Args:
            response: Response from Claude API

        Returns:
            True if valid, False otherwise
        """
        # TODO: Implement schema validation
        raise NotImplementedError("Output validation to be implemented")

    def save_grouped_parts(self, grouped_parts: Dict, output_path: Path) -> None:
        """
        Save grouped parts to JSON file.

        Args:
            grouped_parts: Parts grouped by system code
            output_path: Path to save the JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(grouped_parts, f, indent=2)
        logger.info(f"Saved grouped parts to {output_path}")
