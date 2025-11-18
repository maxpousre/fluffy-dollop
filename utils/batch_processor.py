"""
Batch Processing Utilities

Handles batch processing logic including:
- Batch creation and sizing
- Progress tracking
- Error handling for batches
"""

import logging
from typing import List, Dict, Any, Iterator
from tqdm import tqdm

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Utilities for processing data in batches with progress tracking.
    """

    @staticmethod
    def create_batches(
        items: List[Any],
        batch_size: int
    ) -> Iterator[List[Any]]:
        """
        Create batches from a list of items.

        Args:
            items: List of items to batch
            batch_size: Size of each batch

        Yields:
            Batches of items
        """
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]

    @staticmethod
    def process_with_progress(
        items: List[Any],
        process_func: callable,
        description: str = "Processing",
        batch_size: int = 1
    ) -> List[Any]:
        """
        Process items with a progress bar.

        Args:
            items: Items to process
            process_func: Function to apply to each item/batch
            description: Description for progress bar
            batch_size: Batch size (1 for individual processing)

        Returns:
            List of processed results
        """
        results = []

        if batch_size == 1:
            # Process individually
            for item in tqdm(items, desc=description):
                try:
                    result = process_func(item)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing item: {str(e)}")
                    results.append({"error": str(e), "item": item})
        else:
            # Process in batches
            batches = list(BatchProcessor.create_batches(items, batch_size))
            for batch in tqdm(batches, desc=description):
                try:
                    result = process_func(batch)
                    results.extend(result if isinstance(result, list) else [result])
                except Exception as e:
                    logger.error(f"Error processing batch: {str(e)}")
                    results.append({"error": str(e), "batch": batch})

        return results

    @staticmethod
    def group_by_system(parts: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group parts by their system code.

        Args:
            parts: List of parts with 'primary_system' field

        Returns:
            Dictionary with system codes as keys
        """
        grouped = {}

        for part in parts:
            system_code = part.get('primary_system')
            if not system_code:
                logger.warning(f"Part missing system code: {part.get('part_code')}")
                continue

            if system_code not in grouped:
                grouped[system_code] = []

            grouped[system_code].append(part)

        logger.info(f"Grouped parts into {len(grouped)} systems")
        for system_code, system_parts in grouped.items():
            logger.info(f"  System {system_code}: {len(system_parts)} parts")

        return grouped

    @staticmethod
    def track_progress(total_parts: int) -> Dict[str, Any]:
        """
        Initialize progress tracking dictionary.

        Args:
            total_parts: Total number of parts to process

        Returns:
            Progress tracking dictionary
        """
        return {
            "total_parts": total_parts,
            "classified": 0,
            "pattern_matched": 0,
            "web_searched": 0,
            "mapped": 0,
            "validated": 0,
            "failed": 0,
            "by_system": {}
        }

    @staticmethod
    def update_progress(
        progress: Dict[str, Any],
        stage: str,
        count: int,
        system_code: str = None
    ) -> None:
        """
        Update progress tracking.

        Args:
            progress: Progress dictionary
            stage: Stage name (classified, pattern_matched, etc.)
            count: Number to add to counter
            system_code: Optional system code for system-specific tracking
        """
        if stage in progress:
            progress[stage] += count

        if system_code:
            if system_code not in progress["by_system"]:
                progress["by_system"][system_code] = {
                    "total": 0,
                    "completed": 0
                }
            progress["by_system"][system_code]["completed"] += count

        # Calculate percentage
        if progress["total_parts"] > 0:
            percentage = (progress["validated"] / progress["total_parts"]) * 100
            logger.info(f"Progress: {progress['validated']}/{progress['total_parts']} "
                       f"({percentage:.1f}%) validated")
