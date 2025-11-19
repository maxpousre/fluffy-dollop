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
- Model: claude-sonnet-4-20250514
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

        # 1. Build the classification prompt
        prompt = self._build_prompt(parts)
        logger.debug(f"Prompt built with {len(prompt)} characters")

        # 2. Call Claude API
        max_tokens = self.config.get('max_tokens', {}).get('agent_1', 4000)
        temperature = self.config.get('temperature', 0.0)
        max_retries = self.config.get('max_retries', 3)

        try:
            response = self.claude_client.call_claude(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                max_retries=max_retries
            )

            # 3. Parse the JSON response
            content = response['content']
            parsed_response = self.claude_client.validate_json_response(content)

            # 4. Validate the schema
            if not self._validate_output(parsed_response):
                raise ValueError("Response validation failed")

            # 5. Group parts by system code
            classified_parts = parsed_response['classified_parts']
            grouped_parts = {}

            for part in classified_parts:
                system_code = part['vmrs_system_code']

                if system_code not in grouped_parts:
                    grouped_parts[system_code] = {
                        'system_code': system_code,
                        'system_name': part['system_name'],
                        'parts': []
                    }

                grouped_parts[system_code]['parts'].append({
                    'part_code': part['part_code'],
                    'part_name': part['part_name'],
                    'routing': part['routing'],
                    'confidence': part['confidence'],
                    'reasoning': part['reasoning']
                })

            logger.info(f"Successfully classified {len(classified_parts)} parts into "
                       f"{len(grouped_parts)} system codes")

            # Log summary
            for system_code, data in grouped_parts.items():
                logger.info(f"  System {system_code} ({data['system_name']}): "
                           f"{len(data['parts'])} parts")

            return grouped_parts

        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            raise

    def _build_prompt(self, parts: List[Dict]) -> str:
        """
        Build the classification prompt for Claude.

        Args:
            parts: List of parts to classify

        Returns:
            Formatted prompt string
        """
        # Extract system-level information from customer catalog
        systems_info = {}
        for entry in self.customer_catalog:
            code = entry['vmrs_code']
            # Get base system code (before hyphen)
            system_code = code.split('-')[0]
            if system_code not in systems_info:
                systems_info[system_code] = {
                    'system_code': system_code,
                    'system_name': entry['system_name'],
                    'example_codes': []
                }
            # Add up to 3 example codes per system
            if len(systems_info[system_code]['example_codes']) < 3 and '-' in code:
                systems_info[system_code]['example_codes'].append(
                    f"{code}: {entry['description']}"
                )

        # Build systems reference for prompt
        systems_list = []
        for sys_code in sorted(systems_info.keys()):
            sys_info = systems_info[sys_code]
            examples = '\n    '.join(sys_info['example_codes']) if sys_info['example_codes'] else 'N/A'
            systems_list.append(
                f"  - System {sys_code}: {sys_info['system_name']}\n"
                f"    Examples: {examples}"
            )
        systems_reference = '\n'.join(systems_list)

        # Build parts list for prompt
        parts_list = []
        for idx, part in enumerate(parts, 1):
            parts_list.append(f"  {idx}. Part Code: {part['part_code']}, Part Name: {part['part_name']}")
        parts_text = '\n'.join(parts_list)

        # Build the prompt
        prompt = f"""You are a VMRS (Vehicle Maintenance Reporting Standard) parts classification expert.

Your task is to classify vehicle parts into VMRS system codes based on the customer's specific catalog.

CUSTOMER'S VMRS SYSTEMS:
{systems_reference}

CRITICAL INSTRUCTIONS:
1. Classify each part into the most appropriate VMRS system code
2. Only use system codes that exist in the customer's catalog above
3. Determine a routing decision for each part:
   - EXACT_MATCH: Part name matches closely with a specific code in customer catalog
   - PATTERN_MATCH_NEEDED: Part can be classified to system but needs pattern matching
   - WEB_SEARCH_NEEDED: Part is ambiguous and needs web research
4. Be conservative - prefer PATTERN_MATCH_NEEDED or WEB_SEARCH_NEEDED over guessing

PARTS TO CLASSIFY:
{parts_text}

OUTPUT FORMAT:
Return a JSON object with this exact structure:
{{
  "classified_parts": [
    {{
      "part_code": "ABC123",
      "part_name": "Brake Pad Set Front Heavy Duty",
      "vmrs_system_code": "13",
      "system_name": "Brakes",
      "routing": "PATTERN_MATCH_NEEDED",
      "confidence": 95,
      "reasoning": "Clear brake component, belongs to System 13"
    }}
  ]
}}

IMPORTANT:
- confidence: 0-100 integer
- routing: Must be exactly one of: EXACT_MATCH, PATTERN_MATCH_NEEDED, WEB_SEARCH_NEEDED
- vmrs_system_code: Must be a base system code from customer catalog (e.g., "13", not "13-001")
- Classify ALL {len(parts)} parts
- Return ONLY valid JSON, no markdown formatting

Begin classification:"""

        return prompt

    def _validate_output(self, response: Dict) -> bool:
        """
        Validate the classification output against expected schema.

        Args:
            response: Response from Claude API

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check top-level structure
            if 'classified_parts' not in response:
                logger.error("Response missing 'classified_parts' key")
                return False

            classified_parts = response['classified_parts']

            if not isinstance(classified_parts, list):
                logger.error("'classified_parts' must be a list")
                return False

            if len(classified_parts) == 0:
                logger.error("'classified_parts' is empty")
                return False

            # Validate each part
            required_fields = ['part_code', 'part_name', 'vmrs_system_code',
                             'system_name', 'routing', 'confidence', 'reasoning']
            valid_routing_values = ['EXACT_MATCH', 'PATTERN_MATCH_NEEDED', 'WEB_SEARCH_NEEDED']

            for idx, part in enumerate(classified_parts):
                # Check required fields exist
                for field in required_fields:
                    if field not in part:
                        logger.error(f"Part {idx} missing required field: {field}")
                        return False

                # Validate routing value
                if part['routing'] not in valid_routing_values:
                    logger.error(f"Part {idx} has invalid routing value: {part['routing']}")
                    return False

                # Validate confidence is integer 0-100
                confidence = part['confidence']
                if not isinstance(confidence, int) or confidence < 0 or confidence > 100:
                    logger.error(f"Part {idx} has invalid confidence: {confidence}")
                    return False

                # Validate vmrs_system_code is a string
                if not isinstance(part['vmrs_system_code'], str):
                    logger.error(f"Part {idx} has invalid vmrs_system_code type")
                    return False

            logger.info(f"Validation passed for {len(classified_parts)} parts")
            return True

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False

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
