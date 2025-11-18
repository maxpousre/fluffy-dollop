"""
Configuration Settings

All configuration constants for the VMRS Parts Classification System.
"""

import os
from pathlib import Path

# ==========================================
# PROJECT PATHS
# ==========================================

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Data directories
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
VALIDATED_DIR = DATA_DIR / "validated"
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
ENRICHMENT_DIR = DATA_DIR / "enrichment"
OUTPUT_DIR = DATA_DIR / "output"

# Rules directory
RULES_DIR = BASE_DIR / "rules"
SEARCH_TEMPLATES_DIR = RULES_DIR / "search_templates"

# ==========================================
# CLAUDE API CONFIGURATION
# ==========================================

# Default model (Haiku for cost optimization)
# Claude 3.5 Haiku is ~90% cheaper than Sonnet 4 and excellent for structured tasks
DEFAULT_MODEL = "claude-3-5-haiku-20241022"

# Per-agent model configuration (allows flexibility)
# Use Haiku for most agents (cost-efficient), Sonnet only if complex reasoning needed
AGENT_MODELS = {
    "agent_1": "claude-3-5-haiku-20241022",  # System Classifier - structured classification
    "agent_2": "claude-3-5-haiku-20241022",  # Pattern Matcher - rule-based matching
    "agent_3": "claude-3-5-haiku-20241022",  # Web Researcher - can use Haiku for structured extraction
    "agent_4": "claude-3-5-haiku-20241022",  # VMRS Mapper - deterministic mapping
    "agent_5": "claude-3-5-haiku-20241022"   # QA Validator - validation rules
}

# Alternative: Use Sonnet for Agent 3 if you need deeper reasoning for web research
# Uncomment below to use hybrid approach (~70% cost savings instead of ~90%)
# AGENT_MODELS["agent_3"] = "claude-sonnet-4-20250514"

CLAUDE_CONFIG = {
    "model": DEFAULT_MODEL,  # Fallback default
    "agent_models": AGENT_MODELS,  # Per-agent model selection
    "max_tokens": {
        "agent_1": 4000,  # System Classifier
        "agent_2": 3000,  # Pattern Matcher
        "agent_3": 2000,  # Web Researcher
        "agent_4": 2000,  # VMRS Mapper
        "agent_5": 2000   # QA Validator
    },
    "temperature": 0.0,  # Deterministic for all agents
    "timeout": 120,      # seconds
    "max_retries": 3
}

# ==========================================
# BATCH PROCESSING CONFIGURATION
# ==========================================

BATCH_SIZES = {
    "agent_1": None,  # Process all parts at once
    "agent_2": 10,    # 5-10 parts per batch (same system)
    "agent_3": 1,     # 1 part at a time
    "agent_4": 1,     # 1 part at a time
    "agent_5": 10     # 5-10 parts per batch (same system)
}

# ==========================================
# CONFIDENCE THRESHOLDS
# ==========================================

CONFIDENCE_THRESHOLDS = {
    "auto_approve": 90,         # Auto-approve mappings ≥90%
    "medium_confidence": 70,    # Medium confidence range
    "require_web_search": 70,   # Require web search if <70%
    "flag_for_review": 90       # Flag for human review if <90%
}

# ==========================================
# SYSTEM CODES
# ==========================================

# Common VMRS system codes
VMRS_SYSTEMS = {
    "10": "Lubrication",
    "13": "Brakes",
    "14": "Frame and Frame Components",
    "15": "Steering",
    "17": "Tires and Wheels",
    "18": "Suspension"
}

# Systems requiring special handling
SPECIAL_HANDLING_SYSTEMS = ["10", "13", "17"]

# ==========================================
# FILE PATHS
# ==========================================

# Input files
PARTS_CATALOG_FILE = INPUT_DIR / "parts_catalog.csv"
CUSTOMER_VMRS_CATALOG_FILE = INPUT_DIR / "customer_vmrs_catalog.csv"

# Intermediate files
PARTS_GROUPED_FILE = INTERMEDIATE_DIR / "parts_grouped_by_system.json"
ENRICHED_DESCRIPTIONS_FILE = INTERMEDIATE_DIR / "enriched_descriptions.json"
PROCESSING_MANIFEST_FILE = INTERMEDIATE_DIR / "processing_manifest.json"

# Enrichment cache
WEB_SEARCH_CACHE_FILE = ENRICHMENT_DIR / "web_search_cache.csv"

# Output files
MASTER_OUTPUT_FILE = OUTPUT_DIR / "master_output.csv"
FLAGGED_FOR_REVIEW_FILE = OUTPUT_DIR / "flagged_for_review.csv"
PROCESSING_REPORT_FILE = OUTPUT_DIR / "processing_report.txt"

# ==========================================
# OUTPUT FILE SCHEMAS
# ==========================================

# Master output CSV columns
MASTER_OUTPUT_COLUMNS = [
    "part_code",
    "part_name",
    "vmrs_code",
    "confidence",
    "status",
    "match_type",
    "notes",
    "is_custom_code"
]

# Flagged for review CSV columns
FLAGGED_REVIEW_COLUMNS = [
    "part_code",
    "part_name",
    "suggested_vmrs_code",
    "confidence",
    "reason_flagged",
    "agent_notes"
]

# Validated parts CSV columns
VALIDATED_PARTS_COLUMNS = [
    "part_code",
    "part_name",
    "vmrs_code",
    "confidence",
    "match_type",
    "date_validated"
]

# ==========================================
# STATUS VALUES
# ==========================================

STATUS_VALUES = {
    "VALIDATED": "Passed all validation checks",
    "PENDING_REVIEW": "Awaiting human review",
    "NEEDS_REVIEW": "Requires human review",
    "FAILED": "Failed validation"
}

MATCH_TYPES = {
    "exact_match": "Direct match in customer catalog",
    "pattern_match": "Matched using pattern rules",
    "web_search": "Mapped after web research",
    "human_validated": "Validated by human reviewer"
}

# ==========================================
# ROUTING VALUES
# ==========================================

ROUTING_VALUES = [
    "EXACT_MATCH",
    "PATTERN_MATCH_NEEDED",
    "WEB_SEARCH_NEEDED"
]

# ==========================================
# LOGGING CONFIGURATION
# ==========================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ==========================================
# PERFORMANCE SETTINGS
# ==========================================

# Maximum workers for parallel processing (future enhancement)
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

# Performance targets (for monitoring)
PERFORMANCE_TARGETS = {
    "agent_1_parts_per_minute": 100,
    "agent_2_parts_per_minute": 50,
    "agent_3_parts_per_minute": 20,
    "agent_4_parts_per_minute": 30,
    "agent_5_parts_per_minute": 50,
    "bulk_load_max_hours": 8,      # 10,000 parts
    "daily_load_max_hours": 2      # 100-500 parts
}

# ==========================================
# VALIDATION SETTINGS
# ==========================================

# Minimum required fields for input data
REQUIRED_PART_FIELDS = ["part_code", "part_name"]
REQUIRED_VMRS_FIELDS = ["vmrs_code", "system_name", "description", "is_custom"]

# ==========================================
# ERROR HANDLING
# ==========================================

# Retry settings
RETRY_SETTINGS = {
    "max_retries": 3,
    "initial_wait": 5,      # seconds
    "backoff_multiplier": 2  # exponential backoff
}

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_validated_parts_file(system_code: str) -> Path:
    """Get path to validated parts file for a system."""
    system_name = VMRS_SYSTEMS.get(system_code, f"system_{system_code}")
    return VALIDATED_DIR / f"validated_parts_system_{system_code}.csv"


def get_rules_file(system_code: str) -> Path:
    """Get path to rules file for a system."""
    system_name = VMRS_SYSTEMS.get(system_code, "").lower().replace(" ", "_")
    if system_name:
        return RULES_DIR / f"rules_system_{system_code}_{system_name}.txt"
    return RULES_DIR / f"rules_system_{system_code}.txt"


def get_search_template_file(system_code: str) -> Path:
    """Get path to search template file for a system."""
    return SEARCH_TEMPLATES_DIR / f"search_template_system_{system_code}.txt"


def ensure_directories():
    """Create all necessary directories if they don't exist."""
    directories = [
        INPUT_DIR,
        VALIDATED_DIR,
        INTERMEDIATE_DIR,
        ENRICHMENT_DIR,
        OUTPUT_DIR,
        RULES_DIR,
        SEARCH_TEMPLATES_DIR
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
