# CLAUDE.md - VMRS Parts Classification System

**Project:** VMRS Parts Classification and Mapping System
**Version:** 1.0
**Last Updated:** 2025-11-18

---

## Quick Reference

### Project Purpose
Build a modular, multi-agent AI system to classify and map vehicle parts from a company's catalog to a partner's VMRS (Vehicle Maintenance Reporting Standard) codes. The system must handle initial bulk loading and ongoing daily additions while maintaining >90% accuracy.

### Core Challenge
- **Limited part information**: Only part name and code available
- **Mixed catalog**: Heavy-duty and light-duty parts from multiple suppliers
- **Custom codes**: Partner catalog contains ~10% custom VMRS codes
- **Special categories**: Brakes (System 13), Tires (System 17), Filters (System 10) require special handling
- **Previous degradation**: Single-agent approaches degraded over time

### Solution Approach
Five specialized agents working in sequence, each with narrow focus and minimal context to prevent degradation.

---

## System Architecture

### Agent Pipeline

```
INPUT: parts_catalog.csv
   ↓
[Agent 1: System Classifier] → parts_grouped_by_system.json
   ↓
FOR EACH SYSTEM CODE:
   ↓
[Agent 2: Pattern Matcher] → High confidence mappings + Flagged parts
   ↓
   ├─→ High Confidence (≥90%) ──────────────────────┐
   │                                                 ↓
   └─→ Low Confidence or Rules Require Search      [Agent 5: Validator]
          ↓                                          ↓
       [Agent 3: Web Researcher] → Enriched data   OUTPUT FILES
          ↓                                          - master_output.csv
       [Agent 4: VMRS Mapper] → VMRS codes          - flagged_for_review.csv
          ↓
       [Agent 5: Validator] ────────────────────────┘
```

### Agent Specifications Summary

| Agent | Purpose | Input Batch Size | Context | Model Config |
|-------|---------|------------------|---------|--------------|
| **1. Classifier** | Initial classification & catalog matching | ALL parts | System-level catalog | temp=0.0, max_tokens=4000 |
| **2. Pattern Matcher** | Map using rules & validated examples | 5-10 parts (same system) | System-specific rules + validated parts | temp=0.0, max_tokens=3000 |
| **3. Web Researcher** | Research unmapped parts | 1 part | Search template | temp=0.0, max_tokens=2000 |
| **4. VMRS Mapper** | Map researched parts to codes | 1 part | Customer catalog subset | temp=0.0, max_tokens=2000 |
| **5. QA Validator** | Final validation | 5-10 parts (same system) | System rules + catalog | temp=0.0, max_tokens=2000 |

---

## Critical Architectural Principles

### DO NOT
1. **DO NOT** compare against full VMRS standard catalog (too large, causes confusion)
2. **DO NOT** process parts with different system codes in same batch
3. **DO NOT** carry context/memory between parts or batches
4. **DO NOT** invent or hallucinate VMRS codes not in customer catalog
5. **DO NOT** use temperature > 0.0 (all agents must be deterministic)

### DO
1. **DO** compare only against customer's specific VMRS catalog
2. **DO** process parts individually or in small batches (5-10) by system type
3. **DO** store system-specific rules in separate files, load on-demand
4. **DO** execute web search conditionally (only when Agent 2 flags it or rules require it)
5. **DO** maintain stateless agents with minimal context
6. **DO** prefer false negatives over false positives (better unmapped than wrongly mapped)

---

## Project Structure

```
vmrs-parts-mapper/
├── agents/                          # Agent implementations
│   ├── agent_1_classifier.py       # System classification & catalog matching
│   ├── agent_2_pattern_matcher.py  # Rule-based pattern matching
│   ├── agent_3_web_researcher.py   # Web search & enrichment
│   ├── agent_4_vmrs_mapper.py      # VMRS code assignment
│   └── agent_5_validator.py        # Quality assurance validation
│
├── rules/                           # System-specific rules
│   ├── rules_system_10_lubrication.txt
│   ├── rules_system_13_brakes.txt
│   ├── rules_system_17_tires.txt
│   └── search_templates/
│       ├── search_template_system_10.txt
│       ├── search_template_system_13.txt
│       └── search_template_system_17.txt
│
├── data/
│   ├── input/                       # Source data
│   │   ├── parts_catalog.csv
│   │   └── customer_vmrs_catalog.csv
│   ├── validated/                   # Previously validated mappings
│   │   ├── validated_parts_system_10.csv
│   │   ├── validated_parts_system_13.csv
│   │   └── validated_parts_system_17.csv
│   ├── intermediate/                # Processing files
│   │   ├── parts_grouped_by_system.json
│   │   ├── enriched_descriptions.json
│   │   └── processing_manifest.json
│   ├── enrichment/                  # Search cache
│   │   └── web_search_cache.csv
│   └── output/                      # Final outputs
│       ├── master_output.csv        # ERP-ready import file
│       ├── flagged_for_review.csv   # Human review queue
│       └── processing_report.txt
│
├── utils/                           # Utilities
│   ├── claude_api.py               # Claude API wrapper
│   ├── data_loader.py              # CSV/JSON loading
│   ├── batch_processor.py          # Batch processing logic
│   ├── rules_loader.py             # Rules file parser
│   └── validators.py               # Output validation
│
├── config/
│   └── settings.py                 # Configuration constants
│
├── tests/
│   ├── test_agents.py
│   ├── test_rules.py
│   └── test_integration.py
│
├── main.py                         # Main orchestrator
├── requirements.txt
├── .env.example
├── README.md
├── CLAUDE.md                       # This file
└── PRD_VMRS_Parts_Classification_System.md
```

---

## Key Data Files

### Input Files

**parts_catalog.csv**
```csv
part_code,part_name
ABC123,Brake Pad Set Front Heavy Duty
XYZ789,11R22.5 Drive Tire 14 Ply
```

**customer_vmrs_catalog.csv**
```csv
vmrs_code,system_name,description,is_custom
10,Lubrication,Lubrication System,false
10-040,Lubrication,Engine Oil Filter Spin-On,false
13,Brakes,Brake System,false
13-001,Brakes,Front Brake Pad - Air,false
13-999,Brakes,Custom Brake Component,true
```

### Output Files

**master_output.csv** (ERP-ready)
```csv
part_code,part_name,vmrs_code,confidence,status,match_type,notes,is_custom_code
ABC123,Brake Pad Set Front Heavy Duty,13-001,95,VALIDATED,pattern_match,Front air brake heavy duty,false
```

**flagged_for_review.csv** (Human review queue)
```csv
part_code,part_name,suggested_vmrs_code,confidence,reason_flagged,agent_notes
GHI789,Brake Caliper Rear,13-052,88,CONFIDENCE_BELOW_90,Ambiguous position specification
```

---

## Processing Workflow

### Overall Flow
```
1. INITIALIZATION
   - Load customer VMRS catalog
   - Load system-specific rules
   - Initialize validated parts databases

2. CLASSIFICATION (Agent 1)
   - Process ALL parts in one batch
   - Classify into VMRS system codes (10, 13, 17, etc.)
   - Group by system code
   - Output: parts_grouped_by_system.json

3. SYSTEM-BY-SYSTEM PROCESSING
   For each system_code:

   a. PATTERN MATCHING (Agent 2)
      - Process 5-10 parts at a time (same system)
      - Load system-specific rules
      - Load validated parts for this system only
      - Apply pattern matching
      - Route: High confidence OR Web search needed

   b. WEB RESEARCH (Agent 3) [CONDITIONAL]
      - Process 1 part at a time
      - Execute system-specific web searches
      - Extract system-specific attributes
      - Generate enriched descriptions

   c. CODE MAPPING (Agent 4) [CONDITIONAL]
      - Process 1 enriched part at a time
      - Load customer catalog for this system only
      - Map to VMRS code
      - Assign confidence score

   d. VALIDATION (Agent 5)
      - Process 5-10 parts at a time (same system)
      - Verify codes exist in customer catalog
      - Apply system-specific validation rules
      - Final PASS/REVIEW/FAIL decision

4. AGGREGATION
   - Combine all system outputs
   - Generate master_output.csv
   - Generate flagged_for_review.csv
   - Generate processing_report.txt

5. ERP PREPARATION
   - Format for ERP import
   - Validate data integrity
```

### Batch Size Summary
- **Agent 1**: ALL parts (need full catalog visibility)
- **Agent 2**: 5-10 parts (same system code)
- **Agent 3**: 1 part (individual research)
- **Agent 4**: 1 part (individual mapping)
- **Agent 5**: 5-10 parts (same system code)

---

## Rules System

### Rules File Structure
Each VMRS system has its own rules file: `rules_system_{code}.txt`

**Required Sections:**
1. System identification
2. Web search requirements
3. Pattern matching rules
4. Code assignment rules
5. Validation rules
6. Common error patterns
7. Confidence scoring guidelines
8. Examples

### Special Handling Categories

**System 13 (Brakes)** - Most complex
- Component type: pad/shoe/rotor/drum/caliper
- Position: front/rear/drive axle/trailer axle
- Brake system type: air/hydraulic
- Duty level: heavy/light

**System 17 (Tires)**
- Size specification (e.g., 11R22.5)
- Ply rating
- Tread pattern: rib/lug
- Position: steer/drive/trailer

**System 10 (Filters)**
- Filter type: oil/fuel/transmission/hydraulic
- Application: engine/transmission
- Style: spin-on/cartridge
- Primary or secondary

---

## Success Criteria

### Quantitative Metrics
- ≥95% correct system classification (Agent 1)
- ≥90% correct VMRS code assignment (overall)
- <5% false positives (incorrect mappings)
- ≥95% error detection rate (Agent 5)
- ≥70% parts mapped without web search
- <10% parts require human review on first pass

### Processing Performance
- Complete 10,000 part bulk load in <8 hours
- Process daily additions (100-500 parts) in <2 hours
- No degradation in accuracy over long runs

### Qualitative Goals
- Consistent results across multiple runs
- No hallucinated VMRS codes
- Clear error messages and logging
- CSV outputs directly importable to ERP

---

## Configuration

### Claude API Settings
```python
# OPTIMIZED FOR COST EFFICIENCY
# Using Claude 3.5 Haiku (~90% cheaper than Sonnet 4)
# Haiku is excellent for deterministic, structured tasks

DEFAULT_MODEL = "claude-3-5-haiku-20241022"

# Per-agent model configuration (allows flexibility)
AGENT_MODELS = {
    "agent_1": "claude-3-5-haiku-20241022",  # System Classifier
    "agent_2": "claude-3-5-haiku-20241022",  # Pattern Matcher
    "agent_3": "claude-3-5-haiku-20241022",  # Web Researcher
    "agent_4": "claude-3-5-haiku-20241022",  # VMRS Mapper
    "agent_5": "claude-3-5-haiku-20241022"   # QA Validator
}

# Optional: Use Sonnet for Agent 3 if complex reasoning needed (~70% savings)
# AGENT_MODELS["agent_3"] = "claude-sonnet-4-20250514"

CLAUDE_CONFIG = {
    "model": DEFAULT_MODEL,
    "agent_models": AGENT_MODELS,
    "max_tokens": {
        "agent_1": 4000,
        "agent_2": 3000,
        "agent_3": 2000,
        "agent_4": 2000,
        "agent_5": 2000
    },
    "temperature": 0.0,  # Deterministic for all agents
    "timeout": 120,
    "max_retries": 3
}

CONFIDENCE_THRESHOLDS = {
    "auto_approve": 90,
    "medium_confidence": 70,
    "require_web_search": 70
}
```

**Why Haiku?**
- **~90% cost reduction** vs Sonnet 4
- **Same accuracy** for deterministic tasks (temp=0.0)
- **Faster response times** = better throughput
- **Ideal for**: Classification, pattern matching, validation
- **Processing 10,000 parts**: ~$X vs ~$Y with Sonnet 4

### Environment Variables
```bash
ANTHROPIC_API_KEY=your_api_key_here
LOG_LEVEL=INFO
OUTPUT_DIR=data/output
MAX_WORKERS=4  # For parallel processing
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- Project structure and utilities
- Claude API integration
- Data loading and validation
- **Agent 1 implementation**
- Basic rules files for System 13 (Brakes)

### Phase 2: Core Agents (Week 2)
- **Agent 2 implementation** (Pattern Matcher)
- **Agent 5 implementation** (Validator)
- Rules files for Systems 10, 17
- Validated parts database structure

### Phase 3: Web Research (Week 3)
- **Agent 3 implementation** (Web Researcher)
- **Agent 4 implementation** (VMRS Mapper)
- Search templates for all systems
- Web search caching

### Phase 4: Integration & Testing (Week 4)
- Main orchestrator
- Complete workflow integration
- Error handling and retry logic
- Progress tracking and reporting

### Phase 5: Production Ready (Week 5)
- Documentation
- ERP export formatting
- Daily operations workflow
- User acceptance testing

---

## Development Guidelines

### When Implementing Agents

1. **Keep context minimal**
   - Load only what the agent needs
   - Don't pass full datasets
   - Clear context between batches

2. **Make agents stateless**
   - No memory between parts
   - No global state
   - Fresh start for each batch

3. **Use deterministic behavior**
   - Temperature = 0.0 for all agents
   - Consistent prompt formatting
   - Validate output schemas

4. **Handle errors gracefully**
   - Retry with exponential backoff
   - Log all failures
   - Flag for human review when uncertain

5. **Validate outputs rigorously**
   - Check JSON schema compliance
   - Verify VMRS codes exist in customer catalog
   - Ensure confidence scores are within bounds

### When Writing Rules Files

1. **Be explicit and specific**
   - Define exact keywords for pattern matching
   - Specify when web search is required
   - List common error patterns

2. **Keep rules system-specific**
   - One rules file per system code
   - Don't mix logic across systems
   - Load rules on-demand only

3. **Include validation criteria**
   - Define what makes a valid mapping
   - Specify confidence thresholds
   - List edge cases and special handling

4. **Provide examples**
   - Good mappings with reasoning
   - Problematic cases to avoid
   - Edge cases and how to handle them

---

## Common VMRS Systems Reference

```
System 10: Lubrication
  - Oil filters, transmission filters, hydraulic filters

System 13: Brakes
  - Brake pads, shoes, rotors, drums, calipers
  - Air and hydraulic brake components

System 14: Frame and Frame Components
  - Frame members, cross members

System 15: Steering
  - Steering components, power steering

System 17: Tires and Wheels
  - Tires (steer, drive, trailer)
  - Wheels and rims

System 18: Suspension
  - Springs, shock absorbers
```

---

## Testing Strategy

### Test Sets Required

1. **Known Validated Parts** (100 parts)
   - Requirement: 100% accuracy
   - Purpose: Verify pattern matching works

2. **Difficult Categories** (50 parts each)
   - Brakes: Complex position/type combinations
   - Tires: Various sizes and applications
   - Filters: Different filter types
   - Requirement: ≥90% correct mapping

3. **Ambiguous Parts** (30 parts)
   - Missing information
   - Generic part names
   - Requirement: Properly flag for review

4. **Custom Codes** (20 parts)
   - Parts mapping to custom VMRS codes
   - Requirement: Correctly identify as custom

---

## Key Reminders for Claude

When working on this project:

1. **Always check customer catalog** - Never invent VMRS codes
2. **Keep batches small** - 5-10 parts max for Agents 2 & 5, 1 for Agents 3 & 4
3. **Load only what's needed** - Don't load full VMRS standard or all rules at once
4. **Group by system** - Never mix different system codes in same batch
5. **Be conservative** - Better to flag for review than to make incorrect mapping
6. **Validate everything** - Check outputs against schemas, verify codes exist
7. **Log thoroughly** - All decisions, errors, and edge cases
8. **Test incrementally** - Don't build all agents at once, test each independently

---

## Current Project Status

**Status:** Ready for Implementation
**Next Step:** Phase 1 - Foundation

**Immediate Tasks:**
1. Set up project structure
2. Install dependencies (see requirements.txt)
3. Configure environment variables
4. Create sample data files for testing
5. Implement Agent 1 (Classifier)

---

**END OF CLAUDE.md**
