"""
Data Loading Utilities

Handles loading and parsing of:
- CSV files (parts catalog, VMRS catalog, validated parts)
- JSON files (intermediate processing files)
- Data validation
"""

import csv
import json
import logging
from typing import List, Dict, Any
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Utilities for loading and validating data files.
    """

    @staticmethod
    def load_parts_catalog(file_path: Path) -> List[Dict[str, str]]:
        """
        Load parts catalog from CSV.

        Args:
            file_path: Path to parts_catalog.csv

        Returns:
            List of parts with part_code and part_name

        Expected format:
            part_code,part_name
            ABC123,Brake Pad Set Front Heavy Duty
        """
        logger.info(f"Loading parts catalog from {file_path}")

        parts = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'part_code' not in row or 'part_name' not in row:
                    raise ValueError("Parts catalog must have 'part_code' and 'part_name' columns")
                parts.append({
                    'part_code': row['part_code'].strip(),
                    'part_name': row['part_name'].strip()
                })

        logger.info(f"Loaded {len(parts)} parts from catalog")
        return parts

    @staticmethod
    def load_customer_vmrs_catalog(file_path: Path) -> List[Dict[str, Any]]:
        """
        Load customer's VMRS catalog from CSV.

        Args:
            file_path: Path to customer_vmrs_catalog.csv

        Returns:
            List of VMRS codes with metadata

        Expected format:
            vmrs_code,system_name,description,is_custom
            10,Lubrication,Lubrication System,false
            10-040,Lubrication,Engine Oil Filter Spin-On,false
        """
        logger.info(f"Loading customer VMRS catalog from {file_path}")

        catalog = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                catalog.append({
                    'vmrs_code': row['vmrs_code'].strip(),
                    'system_name': row['system_name'].strip(),
                    'description': row['description'].strip(),
                    'is_custom': row['is_custom'].lower() == 'true'
                })

        logger.info(f"Loaded {len(catalog)} VMRS codes from customer catalog")
        return catalog

    @staticmethod
    def load_validated_parts(file_path: Path, system_code: str) -> List[Dict[str, Any]]:
        """
        Load validated parts for a specific system.

        Args:
            file_path: Path to validated parts CSV
            system_code: VMRS system code

        Returns:
            List of validated parts for this system
        """
        logger.info(f"Loading validated parts for System {system_code} from {file_path}")

        if not file_path.exists():
            logger.warning(f"Validated parts file not found: {file_path}")
            return []

        validated = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                validated.append(row)

        logger.info(f"Loaded {len(validated)} validated parts")
        return validated

    @staticmethod
    def load_json(file_path: Path) -> Dict[str, Any]:
        """
        Load JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data
        """
        logger.info(f"Loading JSON from {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data

    @staticmethod
    def save_json(data: Dict[str, Any], file_path: Path) -> None:
        """
        Save data to JSON file.

        Args:
            data: Data to save
            file_path: Output file path
        """
        logger.info(f"Saving JSON to {file_path}")

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def save_csv(data: List[Dict[str, Any]], file_path: Path) -> None:
        """
        Save data to CSV file.

        Args:
            data: List of dictionaries to save
            file_path: Output file path
        """
        logger.info(f"Saving CSV to {file_path}")

        if not data:
            logger.warning("No data to save")
            return

        file_path.parent.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        logger.info(f"Saved {len(data)} rows to CSV")

    @staticmethod
    def get_system_codes(catalog: List[Dict[str, Any]]) -> List[str]:
        """
        Extract unique system codes from catalog.

        Args:
            catalog: Customer VMRS catalog

        Returns:
            List of unique system codes (e.g., ['10', '13', '17'])
        """
        system_codes = set()
        for entry in catalog:
            code = entry['vmrs_code']
            # Extract base system code (before hyphen)
            system_code = code.split('-')[0]
            system_codes.add(system_code)

        return sorted(list(system_codes))
