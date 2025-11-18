"""
Rules File Loading and Parsing

Handles loading and parsing of system-specific rules files including:
- Pattern matching rules
- Validation rules
- Search templates
- Code assignment rules
"""

import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class RulesLoader:
    """
    Utilities for loading and parsing rules files.
    """

    def __init__(self, rules_dir: Path):
        """
        Initialize rules loader.

        Args:
            rules_dir: Directory containing rules files
        """
        self.rules_dir = Path(rules_dir)
        logger.info(f"Rules loader initialized with directory: {rules_dir}")

    def load_system_rules(self, system_code: str) -> str:
        """
        Load rules file for a specific system.

        Args:
            system_code: VMRS system code (e.g., "10", "13", "17")

        Returns:
            Rules file content as string

        Raises:
            FileNotFoundError: If rules file doesn't exist
        """
        # Map common system codes to their rule files
        system_names = {
            "10": "lubrication",
            "13": "brakes",
            "17": "tires"
        }

        system_name = system_names.get(system_code, f"system_{system_code}")
        rules_file = self.rules_dir / f"rules_system_{system_code}_{system_name}.txt"

        # Fall back to generic system file if specific one doesn't exist
        if not rules_file.exists():
            rules_file = self.rules_dir / f"rules_system_{system_code}.txt"

        if not rules_file.exists():
            logger.warning(f"No rules file found for System {system_code}")
            return ""

        logger.info(f"Loading rules from {rules_file}")

        with open(rules_file, 'r', encoding='utf-8') as f:
            rules_content = f.read()

        return rules_content

    def load_search_template(self, system_code: str) -> str:
        """
        Load search template for a specific system.

        Args:
            system_code: VMRS system code

        Returns:
            Search template content as string
        """
        template_file = self.rules_dir / "search_templates" / f"search_template_system_{system_code}.txt"

        if not template_file.exists():
            logger.warning(f"No search template found for System {system_code}")
            return "{Part Name} {Part Code} specifications"  # Default template

        logger.info(f"Loading search template from {template_file}")

        with open(template_file, 'r', encoding='utf-8') as f:
            template = f.read()

        return template

    def parse_rules_sections(self, rules_content: str) -> Dict[str, str]:
        """
        Parse rules file into sections.

        Args:
            rules_content: Full rules file content

        Returns:
            Dictionary with section names as keys and content as values
        """
        sections = {}
        current_section = None
        current_content = []

        for line in rules_content.split('\n'):
            # Check for section headers (lines with = signs)
            if '=' * 10 in line:
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_content = []
                continue

            # Check for section titles (all caps lines)
            if line.strip() and line.strip().replace(' ', '').replace('_', '').isupper():
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        logger.info(f"Parsed {len(sections)} sections from rules")
        return sections

    def get_web_search_requirement(self, rules_content: str) -> bool:
        """
        Check if web search is required for this system.

        Args:
            rules_content: Rules file content

        Returns:
            True if web search is required
        """
        # Look for WEB_SEARCH_REQUIRED configuration
        for line in rules_content.split('\n'):
            if 'WEB_SEARCH_REQUIRED' in line and ':' in line:
                value = line.split(':')[1].strip().lower()
                return value == 'true'

        return False

    @staticmethod
    def create_default_rules_file(system_code: str, system_name: str, output_path: Path) -> None:
        """
        Create a default rules file template.

        Args:
            system_code: VMRS system code
            system_name: System name
            output_path: Path to save the rules file
        """
        template = f"""SYSTEM: {system_code} - {system_name}
DESCRIPTION: {system_name} System Components

==========================================
WEB SEARCH CONFIGURATION
==========================================
WEB_SEARCH_REQUIRED: False
WEB_SEARCH_CATEGORIES:
  - [Define categories that require web search]

WEB_SEARCH_QUERY_TEMPLATE: "{{Part Name}} {{Part Code}} specifications"

==========================================
PATTERN MATCHING RULES
==========================================

1. COMPONENT DETECTION:
   Keywords: [Define keywords for this system]

   Logic:
   - [Define pattern matching logic]

==========================================
CODE ASSIGNMENT RULES
==========================================

[Define how to assign VMRS codes based on part attributes]

==========================================
VALIDATION RULES
==========================================

CRITICAL CHECKS:
1. [Define validation checks]

CONSISTENCY CHECKS:
- [Define consistency requirements]

COMMON ERROR PATTERNS:
- [Define common errors to avoid]

==========================================
CONFIDENCE SCORING GUIDELINES
==========================================

HIGH CONFIDENCE (90-100%):
- [Define criteria for high confidence]

MEDIUM CONFIDENCE (70-89%):
- [Define criteria for medium confidence]

LOW CONFIDENCE (<70%):
- [Define criteria for low confidence]

==========================================
EXAMPLES
==========================================

GOOD MAPPINGS:
✓ [Example 1]
  Reason: [Explanation]

PROBLEMATIC CASES:
✗ [Example 1]
  Reason: [Explanation]

==========================================
END OF RULES FILE
==========================================
"""

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template)

        logger.info(f"Created default rules file at {output_path}")
