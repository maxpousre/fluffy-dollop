#!/usr/bin/env python3
"""
Simple test script for Agent 1: System Classifier

This script tests Agent 1 in isolation by:
1. Loading sample parts from parts_catalog.csv
2. Loading customer VMRS catalog
3. Classifying parts into system codes
4. Saving results to intermediate/parts_grouped_by_system.json
5. Displaying summary statistics
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import project modules
from utils.claude_api import ClaudeClient
from utils.data_loader import DataLoader
from agents.agent_1_classifier import SystemClassifier
from config.settings import (
    CLAUDE_CONFIG,
    PARTS_CATALOG_FILE,
    CUSTOMER_VMRS_CATALOG_FILE,
    PARTS_GROUPED_FILE,
    ensure_directories
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """Main test function."""
    logger.info("=" * 70)
    logger.info("AGENT 1 TEST: System Classifier")
    logger.info("=" * 70)

    # Load environment variables
    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment")
        logger.error("Please create a .env file with your API key")
        return 1

    # Ensure output directories exist
    ensure_directories()

    try:
        # Step 1: Load input data
        logger.info("\n[Step 1] Loading input data...")
        parts = DataLoader.load_parts_catalog(PARTS_CATALOG_FILE)
        logger.info(f"  Loaded {len(parts)} parts from catalog")

        customer_catalog = DataLoader.load_customer_vmrs_catalog(CUSTOMER_VMRS_CATALOG_FILE)
        logger.info(f"  Loaded {len(customer_catalog)} VMRS codes from customer catalog")

        # Get unique systems
        system_codes = DataLoader.get_system_codes(customer_catalog)
        logger.info(f"  Customer catalog contains {len(system_codes)} unique systems")

        # Step 2: Initialize Claude client
        logger.info("\n[Step 2] Initializing Claude API client...")
        claude_client = ClaudeClient(api_key=api_key, config=CLAUDE_CONFIG)
        logger.info("  Claude client initialized successfully")

        # Step 3: Initialize Agent 1
        logger.info("\n[Step 3] Initializing Agent 1: System Classifier...")
        agent_1 = SystemClassifier(
            claude_client=claude_client,
            customer_catalog=customer_catalog,
            config=CLAUDE_CONFIG
        )
        logger.info("  Agent 1 initialized successfully")

        # Step 4: Run classification
        logger.info("\n[Step 4] Classifying parts...")
        logger.info(f"  Processing {len(parts)} parts...")
        grouped_parts = agent_1.classify_parts(parts)

        # Step 5: Save results
        logger.info("\n[Step 5] Saving results...")
        agent_1.save_grouped_parts(grouped_parts, PARTS_GROUPED_FILE)
        logger.info(f"  Results saved to: {PARTS_GROUPED_FILE}")

        # Step 6: Display summary
        logger.info("\n[Step 6] Classification Summary")
        logger.info("=" * 70)
        total_parts = sum(len(data['parts']) for data in grouped_parts.values())
        logger.info(f"Total parts classified: {total_parts}")
        logger.info(f"Number of systems: {len(grouped_parts)}")
        logger.info("")

        # Summary by system
        for system_code in sorted(grouped_parts.keys()):
            data = grouped_parts[system_code]
            logger.info(f"System {system_code}: {data['system_name']}")
            logger.info(f"  Parts: {len(data['parts'])}")

            # Count routing decisions
            routing_counts = {}
            for part in data['parts']:
                routing = part['routing']
                routing_counts[routing] = routing_counts.get(routing, 0) + 1

            for routing, count in sorted(routing_counts.items()):
                logger.info(f"    {routing}: {count}")

            # Show example parts
            logger.info(f"  Example parts:")
            for part in data['parts'][:3]:  # Show first 3
                logger.info(f"    - {part['part_code']}: {part['part_name']}")
                logger.info(f"      Routing: {part['routing']}, Confidence: {part['confidence']}%")
            logger.info("")

        # Overall routing statistics
        logger.info("Overall Routing Statistics:")
        overall_routing = {}
        for system_code, data in grouped_parts.items():
            for part in data['parts']:
                routing = part['routing']
                overall_routing[routing] = overall_routing.get(routing, 0) + 1

        for routing, count in sorted(overall_routing.items()):
            percentage = (count / total_parts) * 100
            logger.info(f"  {routing}: {count} ({percentage:.1f}%)")

        logger.info("\n" + "=" * 70)
        logger.info("TEST COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info(f"\nNext steps:")
        logger.info(f"1. Review the output file: {PARTS_GROUPED_FILE}")
        logger.info(f"2. Verify classifications are accurate")
        logger.info(f"3. Check routing decisions are appropriate")
        logger.info(f"4. Ready to implement Agent 2 (Pattern Matcher)")

        return 0

    except Exception as e:
        logger.error(f"\n{'='*70}")
        logger.error(f"TEST FAILED: {str(e)}")
        logger.error(f"{'='*70}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
