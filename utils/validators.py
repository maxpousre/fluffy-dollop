"""
Output Validation Utilities

Handles validation of:
- JSON schema compliance
- VMRS code validity
- Confidence score ranges
- Output file formatting
"""

import logging
from typing import Dict, Any, List
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


class OutputValidator:
    """
    Utilities for validating agent outputs and data integrity.
    """

    # JSON Schema for Agent 1 output
    AGENT_1_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "classifications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["part_code", "part_name", "primary_system", "confidence", "routing"],
                    "properties": {
                        "part_code": {"type": "string"},
                        "part_name": {"type": "string"},
                        "primary_system": {"type": "string"},
                        "secondary_system": {"type": ["string", "null"]},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 100},
                        "routing": {"enum": ["EXACT_MATCH", "PATTERN_MATCH_NEEDED", "WEB_SEARCH_NEEDED"]},
                        "notes": {"type": "string"}
                    }
                }
            }
        }
    }

    # JSON Schema for Agent 2 output
    AGENT_2_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "mappings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["part_code", "part_name", "confidence", "match_type", "web_search_needed"],
                    "properties": {
                        "part_code": {"type": "string"},
                        "part_name": {"type": "string"},
                        "vmrs_code": {"type": ["string", "null"]},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 100},
                        "match_type": {"enum": ["exact", "pattern", "none"]},
                        "web_search_needed": {"type": "boolean"},
                        "notes": {"type": "string"}
                    }
                }
            }
        }
    }

    @staticmethod
    def validate_agent_output(output: Dict[str, Any], agent_number: int) -> bool:
        """
        Validate agent output against expected schema.

        Args:
            output: Agent output dictionary
            agent_number: Agent number (1-5)

        Returns:
            True if valid

        Raises:
            ValidationError: If output doesn't match schema
        """
        schemas = {
            1: OutputValidator.AGENT_1_SCHEMA,
            2: OutputValidator.AGENT_2_SCHEMA,
            # Add schemas for agents 3-5 as needed
        }

        schema = schemas.get(agent_number)
        if not schema:
            logger.warning(f"No schema defined for Agent {agent_number}")
            return True

        try:
            validate(instance=output, schema=schema)
            logger.info(f"Agent {agent_number} output validated successfully")
            return True
        except ValidationError as e:
            logger.error(f"Agent {agent_number} output validation failed: {str(e)}")
            raise

    @staticmethod
    def validate_vmrs_code(
        vmrs_code: str,
        customer_catalog: List[Dict[str, Any]]
    ) -> bool:
        """
        Validate that VMRS code exists in customer catalog.

        Args:
            vmrs_code: VMRS code to validate
            customer_catalog: Customer's VMRS catalog

        Returns:
            True if code exists in catalog
        """
        for entry in customer_catalog:
            if entry['vmrs_code'] == vmrs_code:
                return True

        logger.warning(f"VMRS code {vmrs_code} not found in customer catalog")
        return False

    @staticmethod
    def validate_confidence_score(confidence: float) -> bool:
        """
        Validate confidence score is within valid range.

        Args:
            confidence: Confidence score

        Returns:
            True if valid (0-100)
        """
        if not isinstance(confidence, (int, float)):
            logger.error(f"Confidence must be numeric, got {type(confidence)}")
            return False

        if confidence < 0 or confidence > 100:
            logger.error(f"Confidence {confidence} outside valid range (0-100)")
            return False

        return True

    @staticmethod
    def validate_system_code(system_code: str, valid_systems: List[str]) -> bool:
        """
        Validate system code is in list of valid systems.

        Args:
            system_code: System code to validate
            valid_systems: List of valid system codes

        Returns:
            True if valid
        """
        if system_code not in valid_systems:
            logger.warning(f"System code {system_code} not in valid systems: {valid_systems}")
            return False

        return True

    @staticmethod
    def check_required_fields(data: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Check that all required fields are present in data.

        Args:
            data: Data dictionary to check
            required_fields: List of required field names

        Returns:
            True if all fields present

        Raises:
            ValueError: If required fields are missing
        """
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            raise ValueError(f"Missing required fields: {missing_fields}")

        return True

    @staticmethod
    def validate_output_file_format(
        file_path: str,
        expected_columns: List[str]
    ) -> bool:
        """
        Validate that output CSV has expected columns.

        Args:
            file_path: Path to CSV file
            expected_columns: List of expected column names

        Returns:
            True if format is correct
        """
        import csv

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                actual_columns = reader.fieldnames

                missing_columns = [col for col in expected_columns if col not in actual_columns]

                if missing_columns:
                    logger.error(f"Output file missing columns: {missing_columns}")
                    return False

                logger.info(f"Output file format validated: {file_path}")
                return True

        except Exception as e:
            logger.error(f"Error validating output file: {str(e)}")
            return False
