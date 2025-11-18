# Project Requirements Document
# VMRS Parts Classification and Mapping System

**Version:** 1.0  
**Date:** November 18, 2025  
**Document Type:** Technical Specification & Requirements

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Overview](#project-overview)
3. [System Architecture](#system-architecture)
4. [Detailed Agent Specifications](#detailed-agent-specifications)
5. [Data Structures & File Formats](#data-structures--file-formats)
6. [Rules & Configuration System](#rules--configuration-system)
7. [Processing Workflow](#processing-workflow)
8. [Technical Specifications](#technical-specifications)
9. [Success Criteria](#success-criteria)
10. [Implementation Phases](#implementation-phases)

---

## Executive Summary

### Purpose
Build a modular, multi-agent AI system to classify and map vehicle parts from a company's catalog to a partner's VMRS (Vehicle Maintenance Reporting Standard) codes. The system must handle initial bulk loading and ongoing daily additions while maintaining >90% accuracy.

### Core Challenge
- Limited part information (only name and code)
- Mix of heavy-duty and light-duty parts from multiple suppliers
- Partner catalog contains ~10% custom VMRS codes
- Specific categories (brakes, tires, filters) require special handling
- Previous single-agent attempts degraded over time

### Solution Approach
Five specialized agents working in sequence, each with narrow focus and minimal context to prevent degradation:
1. System classification
2. Pattern matching with rules
3. Web research (conditional)
4. VMRS code mapping
5. Quality validation

---

## Project Overview

### Business Context
- **Initial Load:** Bulk classification of existing parts catalog
- **Ongoing Operations:** Daily additions of new parts requiring mapping
- **Integration Point:** Output must load into ERP system
- **Quality Standard:** Better to leave unmapped than incorrectly map (false negatives > false positives)
- **Human Review:** All mappings validated by humans on first run; 90%+ confidence threshold for auto-mapping in future

### Key Constraints
1. **DO NOT** compare against full VMRS standard catalog (too large, causes confusion)
2. **DO** compare only against customer's specific VMRS catalog
3. **Context Management:** Process parts individually or in small batches (5-10) by system type
4. **Rules Separation:** System-specific rules stored in separate files, loaded on-demand
5. **Conditional Execution:** Web search only when needed (Agent 2 flags it or rules require it)

### Difficult Categories Requiring Special Handling
- **Brake System Components** (VMRS System 13)
- **Tires** (VMRS System 17)  
- **Oil Filters** (VMRS System 10)

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     INPUT: parts_catalog.csv                     │
│              (Part Code, Part Name from all suppliers)           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 1: System Classifier & Customer Catalog Matcher          │
│  Input: All parts + customer VMRS catalog (system-level only)   │
│  Output: parts_grouped_by_system.json                           │
│  Processing: Single batch, all parts at once                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
         ┌────────────┴────────────┐
         │  Parts Grouped by       │
         │  System Code            │
         │  (10, 13, 17, etc.)     │
         └────────────┬────────────┘
                      │
        ┌─────────────┴─────────────┐
        │  FOR EACH SYSTEM CODE:    │
        └─────────────┬─────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 2: System-Specific Pattern Matcher                       │
│  Input: 5-10 parts (same system) + rules + validated parts DB   │
│  Output: High-confidence mappings + flagged parts                │
│  Processing: Small batches (5-10 parts, same system)            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
         ▼                         ▼
   High Confidence          Low Confidence or
   (≥90%)                   Rules Require Search
         │                         │
         │                         ▼
         │    ┌─────────────────────────────────────────────────┐
         │    │  AGENT 3: System-Specific Web Researcher        │
         │    │  Input: 1 part + search template                │
         │    │  Output: Enriched description                   │
         │    │  Processing: Individual (1 part at a time)      │
         │    └─────────────────────┬───────────────────────────┘
         │                          │
         │                          ▼
         │    ┌─────────────────────────────────────────────────┐
         │    │  AGENT 4: System-Specific VMRS Mapper           │
         │    │  Input: Description + customer catalog subset   │
         │    │  Output: VMRS code + confidence                 │
         │    │  Processing: Individual (1 part at a time)      │
         │    └─────────────────────┬───────────────────────────┘
         │                          │
         └──────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 5: Quality Assurance Validator                           │
│  Input: 5-10 mapped parts (same system) + rules                 │
│  Output: Validated mappings + flagged items                     │
│  Processing: Small batches (5-10 parts, same system)            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  OUTPUT: master_output.csv (ERP-ready format)                   │
│          flagged_for_review.csv (human review queue)            │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Stateless Agents:** No memory between parts/batches
2. **Minimal Context:** Each agent loads only what it needs
3. **System Grouping:** Parts processed in batches by system code
4. **Conditional Execution:** Agents 3 & 4 only run when needed
5. **Rules Externalization:** System-specific logic in separate files
6. **Customer Catalog Focus:** Never load full VMRS standard

---

## Detailed Agent Specifications

### Agent 1: System Classifier & Customer Catalog Matcher

**Purpose:** Initial classification and direct matching against customer's catalog

**Inputs:**
- `parts_catalog.csv` - All parts to classify
- `customer_vmrs_catalog.csv` - Customer's VMRS codes (system-level structure only, not full detail)

**Outputs:**
- `parts_grouped_by_system.json` - Parts organized by VMRS system code

**Processing Logic:**

```python
for each part in parts_catalog:
    1. Load customer VMRS catalog (system-level: codes like 10, 13, 17)
    2. Analyze part name and code
    3. Classify into 1-2 possible system codes
    4. Attempt direct/fuzzy match in customer catalog
    5. Assign confidence score (0-100)
    6. Determine routing:
       - EXACT_MATCH: Found in customer catalog
       - PATTERN_MATCH_NEEDED: System identified, need rules
       - WEB_SEARCH_NEEDED: Ambiguous or insufficient info
    7. Output:
       {
         "part_code": "ABC123",
         "part_name": "Brake Pad Set Front",
         "primary_system": "13",
         "secondary_system": null,
         "confidence": 95,
         "routing": "PATTERN_MATCH_NEEDED"
       }
```

**Context Management:**
- Process all parts in one execution
- Load only system-level catalog structure (not detailed codes)
- Output grouped by system code for next stage

**Success Criteria:**
- 95%+ parts assigned to correct system
- Clear routing decision for each part
- No parts lost in classification

**Claude API Configuration:**
```python
model = "claude-sonnet-4-20250514"
max_tokens = 4000
temperature = 0.0  # Deterministic classification
```

**Prompt Template:**
```
You are a VMRS parts classification specialist. Your task is to classify vehicle parts into VMRS system codes using ONLY the customer's specific catalog.

Customer VMRS Systems Available:
{customer_catalog_systems}

Parts to Classify:
{parts_batch}

For each part:
1. Analyze the part name and code
2. Identify the most likely VMRS system code(s)
3. Check if the part exists in customer's catalog (direct or fuzzy match)
4. Assign confidence score (0-100)
5. Determine routing: EXACT_MATCH, PATTERN_MATCH_NEEDED, or WEB_SEARCH_NEEDED

Output JSON format:
{
  "classifications": [
    {
      "part_code": "...",
      "part_name": "...",
      "primary_system": "...",
      "secondary_system": "..." or null,
      "confidence": 0-100,
      "routing": "EXACT_MATCH|PATTERN_MATCH_NEEDED|WEB_SEARCH_NEEDED",
      "notes": "brief reasoning"
    }
  ]
}

Guidelines:
- DO NOT invent or reference VMRS codes not in customer's catalog
- If uncertain between 2 systems, list both and flag for review
- Common systems: 10=Lubrication, 13=Brakes, 17=Tires
- Be conservative: if confidence <90%, flag for next stage
```

---

### Agent 2: System-Specific Pattern Matcher

**Purpose:** Map parts using validated examples and system-specific rules

**Inputs:**
- Parts batch (5-10 parts, all same system code)
- `rules_system_{code}.txt` - System-specific matching rules
- `validated_parts_system_{code}.csv` - Previously validated mappings for this system

**Outputs:**
- Mapped parts with confidence scores
- Parts flagged for web search

**Processing Logic:**

```python
for batch in parts_grouped_by_system[system_code]:
    1. Load system-specific rules file
    2. Load validated parts for this system ONLY
    3. For each part in batch:
       a. Check for exact match in validated parts
       b. Apply pattern matching rules from rules file
       c. Check if category requires web search (per rules)
       d. Calculate confidence score
    4. Output decisions:
       - Confidence ≥90%: Return VMRS code
       - Confidence 70-89%: Flag as MEDIUM_CONFIDENCE
       - Confidence <70%: Flag as WEB_SEARCH_NEEDED
       - Rules specify "always search": Flag regardless of confidence
```

**Context Management:**
- Process 5-10 parts at a time
- All parts in batch must be same system code
- Load ONLY rules and validated parts for this system
- Fresh context for each batch

**Success Criteria:**
- 70%+ parts mapped without web search
- No false positives (incorrect mappings)
- Proper flagging of parts needing research

**Rules File Integration:**
```python
# Load rules for this system
rules_path = f"rules/rules_system_{system_code}.txt"
rules = load_rules_file(rules_path)

# Check if web search required
if rules['WEB_SEARCH_REQUIRED'] and matches_category(part, rules['CATEGORIES']):
    flag_for_web_search(part)
```

**Claude API Configuration:**
```python
model = "claude-sonnet-4-20250514"
max_tokens = 3000
temperature = 0.0
```

**Prompt Template:**
```
You are a VMRS parts mapping specialist for System {system_code}.

System-Specific Rules:
{rules_content}

Validated Parts Database (this system only):
{validated_parts_sample}  # Max 100 examples

Parts to Map:
{parts_batch}  # 5-10 parts

For each part:
1. Check validated parts database for exact or similar matches
2. Apply pattern matching rules from system-specific rules
3. Determine if web search is required (per rules)
4. If mapping: assign confidence score (0-100)

Output JSON format:
{
  "mappings": [
    {
      "part_code": "...",
      "part_name": "...",
      "vmrs_code": "..." or null,
      "confidence": 0-100,
      "match_type": "exact|pattern|none",
      "web_search_needed": true/false,
      "notes": "reasoning"
    }
  ]
}

Critical Rules:
- Only suggest codes that exist in customer's catalog
- Follow system-specific rules exactly
- If rules say "always web search" for category, flag it
- Confidence ≥90% required for auto-mapping
```

---

### Agent 3: System-Specific Web Researcher

**Purpose:** Research unmapped parts using system-specific search strategies

**Inputs:**
- Single part (part_code, part_name, system_code)
- `search_template_system_{code}.txt` - System-specific search query template

**Outputs:**
- Enriched part description with system-specific attributes

**Processing Logic:**

```python
for each part flagged for web search:
    1. Load search template for this system
    2. Construct dynamic query based on system type
    3. Execute web search
    4. Extract system-specific attributes:
       - Brakes: position, type, duty level
       - Tires: size, ply, pattern, position
       - Filters: application, type, style
    5. Synthesize structured description (200-300 words max)
    6. Store in enrichment database for future use
    7. Output enriched description
```

**Search Query Templates by System:**

**System 13 (Brakes):**
```
"{Part Name} {Part Code} specifications for front or rear component"
```

**System 17 (Tires):**
```
"{Part Name} {Part Code} - Rib or Lug Pattern for rib vs. number of plys"
```

**System 10 (Oil Filters):**
```
"Is {Part Name} {Part Code} used for engine or transmission"
```

**Context Management:**
- Process 1 part at a time
- No memory between parts
- Each search is independent

**Success Criteria:**
- Extract relevant technical specifications
- Identify system-specific attributes
- Build reusable knowledge base

**Claude API Configuration:**
```python
model = "claude-sonnet-4-20250514"
max_tokens = 2000
temperature = 0.0
```

**Prompt Template:**
```
You are a vehicle parts research specialist for VMRS System {system_code}.

Part to Research:
- Code: {part_code}
- Name: {part_name}
- System: {system_code}

Search Query Template:
{search_template}

Web Search Results:
{search_results}

Extract the following system-specific information:

For Brakes (System 13):
- Component type (pad/shoe/rotor/drum/caliper)
- Position (front/rear/drive axle/trailer axle)
- Brake system type (air/hydraulic)
- Duty level (heavy/light)

For Tires (System 17):
- Size specification (e.g., 11R22.5)
- Ply rating
- Tread pattern (rib/lug)
- Position (steer/drive/trailer)

For Filters (System 10):
- Filter type (oil/fuel/transmission/hydraulic)
- Application (engine/transmission)
- Style (spin-on/cartridge)
- Primary or secondary filter

Output JSON format:
{
  "part_code": "...",
  "enriched_description": "...",  # 200-300 words
  "system_attributes": {
    // system-specific attributes extracted above
  },
  "confidence_in_research": 0-100,
  "sources": ["url1", "url2"]
}

Guidelines:
- Be factual and specific
- Include manufacturer details if available
- Note any ambiguities or uncertainties
- Focus on attributes needed for VMRS mapping
```

---

### Agent 4: System-Specific VMRS Mapper

**Purpose:** Map web-researched parts to customer's VMRS codes

**Inputs:**
- Enriched description from Agent 3
- Customer VMRS catalog (filtered to relevant system only)
- `rules_system_{code}.txt` - System-specific mapping rules

**Outputs:**
- VMRS code assignment
- Confidence score
- Mapping reasoning

**Processing Logic:**

```python
for each enriched part:
    1. Load customer's catalog for this system ONLY
    2. Load system-specific mapping rules
    3. Analyze enriched description against VMRS definitions
    4. Apply strict matching criteria from rules
    5. Handle custom codes (note if code is non-standard)
    6. Calculate confidence:
       - 95-100%: Direct functional match + clear application
       - 85-94%: Functional match but ambiguous application
       - <85%: Flag for Agent 5 or human review
    7. Output VMRS code with reasoning
```

**Context Management:**
- Process 1 part at a time
- Load ONLY customer's codes for this system
- Fresh context per part

**Success Criteria:**
- Accurate mapping to customer's specific codes
- Confidence ≥90% for auto-approval
- Proper handling of custom (non-standard) codes

**Claude API Configuration:**
```python
model = "claude-sonnet-4-20250514"
max_tokens = 2000
temperature = 0.0
```

**Prompt Template:**
```
You are a VMRS code mapping specialist for System {system_code}.

Customer's VMRS Codes (System {system_code} only):
{customer_catalog_filtered}

System-Specific Mapping Rules:
{rules_content}

Part to Map:
{enriched_description}

System Attributes Extracted:
{system_attributes}

Task:
1. Match the part to the most appropriate VMRS code from customer's catalog
2. Apply system-specific mapping rules
3. If code appears to be custom (non-standard), flag it
4. Assign confidence score (0-100)

Output JSON format:
{
  "part_code": "...",
  "vmrs_code": "...",
  "confidence": 0-100,
  "is_custom_code": true/false,
  "reasoning": "detailed explanation of why this code was chosen",
  "alternative_codes": ["...", "..."],  # if any close alternatives
  "notes": "any concerns or ambiguities"
}

Critical Rules:
- ONLY use codes from customer's catalog provided above
- Apply system-specific validation rules strictly
- Confidence ≥90% required for auto-approval
- If multiple codes possible, choose most specific
- Flag custom codes explicitly
```

---

### Agent 5: Quality Assurance Validator

**Purpose:** Final validation before human review

**Inputs:**
- Batch of mapped parts (5-10, same system)
- System-specific rules
- Customer VMRS catalog (for verification)

**Outputs:**
- PASS/FAIL status for each mapping
- Validation notes
- Final confidence adjustment

**Processing Logic:**

```python
for batch in mapped_parts_by_system:
    1. Load system-specific validation rules
    2. For each mapped part:
       a. Verify VMRS code exists in customer catalog
       b. Check against system-specific validation rules
       c. Look for common errors (per rules)
       d. Cross-check consistency within batch
    3. Output:
       - PASS: Ready for ERP import
       - REVIEW: Requires human validation
       - FAIL: Mapping error detected
```

**Validation Checks:**

**Cross-System Validation:**
- Brake parts not mapped to suspension codes
- Tire codes match size/position specifications
- Filter types match application codes

**Code Existence:**
- Verify code exists in customer's catalog
- Flag custom codes for review

**Logic Validation:**
- Position indicators match code ranges
- Duty level appropriate for code
- No conflicting attributes

**Context Management:**
- Process 5-10 parts at a time (same system)
- Load rules for this system only
- Fresh context per batch

**Success Criteria:**
- Catch 95%+ of mapping errors
- No false negatives (rejecting correct mappings)
- Clear validation notes for human review

**Claude API Configuration:**
```python
model = "claude-sonnet-4-20250514"
max_tokens = 2000
temperature = 0.0
```

**Prompt Template:**
```
You are a quality assurance specialist validating VMRS part mappings for System {system_code}.

Customer VMRS Catalog:
{customer_catalog}

System Validation Rules:
{validation_rules}

Mapped Parts to Validate:
{mapped_parts_batch}

For each mapping, check:
1. VMRS code exists in customer's catalog
2. System-specific validation rules are satisfied
3. Common errors (defined in rules) are not present
4. Attributes are consistent with code assignment

Output JSON format:
{
  "validations": [
    {
      "part_code": "...",
      "vmrs_code": "...",
      "status": "PASS|REVIEW|FAIL",
      "issues_found": ["..."],  # empty if PASS
      "confidence_adjustment": 0,  # +/- adjustment to confidence
      "final_confidence": 0-100,
      "notes": "validation reasoning"
    }
  ]
}

Validation Rules:
- PASS: Code exists, rules satisfied, no issues
- REVIEW: Code exists but low confidence or edge case
- FAIL: Code invalid or major rule violation
- Be strict: better to flag for review than approve incorrectly
```

---

## Data Structures & File Formats

### Input Files

#### `parts_catalog.csv`
```csv
part_code,part_name
ABC123,Brake Pad Set Front Heavy Duty
XYZ789,11R22.5 Drive Tire 14 Ply
DEF456,Engine Oil Filter Spin-On
```

#### `customer_vmrs_catalog.csv`
```csv
vmrs_code,system_name,description,is_custom
10,Lubrication,Lubrication System,false
10-040,Lubrication,Engine Oil Filter Spin-On,false
10-041,Lubrication,Engine Oil Filter Cartridge,false
13,Brakes,Brake System,false
13-001,Brakes,Front Brake Pad - Air,false
13-999,Brakes,Custom Brake Component,true
17,Tires,Tires and Wheels,false
17-051,Tires,Drive Tire 11R22.5,false
```

### Intermediate Files

#### `parts_grouped_by_system.json`
```json
{
  "10": [
    {
      "part_code": "DEF456",
      "part_name": "Engine Oil Filter Spin-On",
      "primary_system": "10",
      "secondary_system": null,
      "confidence": 95,
      "routing": "PATTERN_MATCH_NEEDED"
    }
  ],
  "13": [
    {
      "part_code": "ABC123",
      "part_name": "Brake Pad Set Front Heavy Duty",
      "primary_system": "13",
      "secondary_system": null,
      "confidence": 90,
      "routing": "PATTERN_MATCH_NEEDED"
    }
  ]
}
```

#### `enriched_descriptions.json`
```json
{
  "part_code": "ABC123",
  "enriched_description": "Heavy-duty air brake pad set designed for front axle applications...",
  "system_attributes": {
    "component_type": "brake_pad",
    "position": "front",
    "brake_type": "air",
    "duty_level": "heavy"
  },
  "confidence_in_research": 92,
  "sources": ["https://example.com/spec1", "https://example.com/spec2"]
}
```

### Output Files

#### `master_output.csv` (ERP Import Format)
```csv
part_code,part_name,vmrs_code,confidence,status,match_type,notes,is_custom_code
ABC123,Brake Pad Set Front Heavy Duty,13-001,95,VALIDATED,pattern_match,Front air brake heavy duty,false
DEF456,Engine Oil Filter Spin-On,10-040,92,PENDING_REVIEW,web_search,Verified engine application,false
XYZ789,Custom Bracket Assembly,88-999,78,NEEDS_REVIEW,web_search,Custom code candidate,true
```

#### `flagged_for_review.csv` (Human Review Queue)
```csv
part_code,part_name,suggested_vmrs_code,confidence,reason_flagged,agent_notes
GHI789,Brake Caliper Rear,13-052,88,CONFIDENCE_BELOW_90,Ambiguous position specification
JKL012,Unknown Filter,10-060,75,CATEGORY_UNCERTAIN,Could be fuel or hydraulic filter
```

### Database Files

#### `validated_parts_system_{code}.csv`
```csv
part_code,part_name,vmrs_code,confidence,match_type,date_validated
ABC123,Brake Pad Set Front,13-001,100,human_validated,2025-01-15
ABC124,Brake Pad Set Rear,13-002,100,human_validated,2025-01-15
```

#### `web_search_cache.csv`
```csv
part_code,part_name,search_query,enriched_description,search_date,sources
XYZ789,HD Air Filter,"HD Air Filter specifications",Heavy-duty air filter for...,2025-01-15,"url1|url2"
```

---

## Rules & Configuration System

### Rules File Structure

Each VMRS system code has its own rules file: `rules_system_{code}.txt`

**Required Sections:**
1. System identification
2. Web search requirements
3. Pattern matching rules
4. Validation rules
5. Common errors to avoid

### Example: `rules_system_13_brakes.txt`

```
SYSTEM: 13 - Brakes
DESCRIPTION: Brake System Components

==========================================
WEB SEARCH CONFIGURATION
==========================================
WEB_SEARCH_REQUIRED: True
WEB_SEARCH_CATEGORIES:
  - Calipers (always require specifications)
  - Rotors with diameter specifications
  - Custom or modified brake components

WEB_SEARCH_OPTIONAL: False
WEB_SEARCH_QUERY_TEMPLATE: "{Part Name} {Part Code} specifications for front or rear component"

==========================================
PATTERN MATCHING RULES
==========================================

1. BRAKE PAD/SHOE DETECTION:
   Keywords: "pad", "shoe", "lining", "friction material"
   Position Required: "front", "rear", "drive axle", "trailer axle", "steer"
   
   Logic:
   - If position keywords found → Extract position
   - If position missing → FLAG: WEB_SEARCH_NEEDED
   - Heavy duty keywords: "HD", "heavy duty", "severe service"
   - Light duty keywords: "LD", "light duty", "standard"

2. ROTOR/DRUM DETECTION:
   Keywords: "rotor", "drum", "disc"
   
   Critical Attributes:
   - Diameter specification (e.g., "15 inch", "381mm")
   - If diameter not in part name → FLAG: WEB_SEARCH_NEEDED
   
   Code Assignment:
   - Rotors (disc): 13-010 to 13-019
   - Drums: 13-020 to 13-029

3. CALIPER DETECTION:
   Keywords: "caliper", "wheel cylinder", "brake cylinder"
   
   Requirements:
   - ALWAYS require web search for specifications
   - Must verify position (front/rear)
   - Must verify axle configuration
   
   Code Range: 13-030 to 13-049

4. AIR VS HYDRAULIC BRAKE SYSTEM:
   Air Brake Indicators: "air brake", "pneumatic", "Bendix", "Haldex"
   Hydraulic Indicators: "hydraulic", "DOT 3", "DOT 4", "brake fluid"
   
   Code Ranges:
   - Air brake components: 13-100 to 13-299
   - Hydraulic components: 13-300 to 13-499

==========================================
CODE ASSIGNMENT RULES
==========================================

FRONT BRAKE COMPONENTS:
- Pads/Shoes: 13-001 to 13-010
- Rotors/Drums: 13-011 to 13-020
- Calipers: 13-031 to 13-040

REAR BRAKE COMPONENTS:
- Pads/Shoes: 13-051 to 13-060
- Rotors/Drums: 13-061 to 13-070
- Calipers: 13-081 to 13-090

HEAVY DUTY DESIGNATION:
- Add suffix "-HD" for heavy-duty components
- Heavy duty indicators: 10+ ply, severe service, class 8 truck

==========================================
VALIDATION RULES
==========================================

CRITICAL CHECKS:
1. NEVER map brake components to suspension codes (14-xxx)
2. NEVER map brake components to steering codes (15-xxx)
3. Position must be explicitly stated or researched
4. Air and hydraulic components must not be confused

CONSISTENCY CHECKS:
- Front brake parts must have "front" or "steer" in notes
- Rear brake parts must have "rear" or "drive/trailer" in notes
- Heavy duty parts should have HD designation
- Part code ranges must align with position

COMMON ERROR PATTERNS:
- Brake pad mapped to rotor code → FAIL
- Air brake component mapped to hydraulic code → FAIL
- Missing position specification → FLAG FOR REVIEW
- Duty level mismatch → FLAG FOR REVIEW

==========================================
CONFIDENCE SCORING GUIDELINES
==========================================

HIGH CONFIDENCE (90-100%):
- Exact match in validated parts database
- Clear position indicators + duty level + brake type
- All required attributes present

MEDIUM CONFIDENCE (70-89%):
- Position identified but duty level unclear
- Brake type assumed but not explicit
- Similar pattern in validated database

LOW CONFIDENCE (<70%):
- Position ambiguous or missing
- Brake type uncertain
- No similar examples in database
→ Require web search

==========================================
EXAMPLES
==========================================

GOOD MAPPINGS:
✓ "Front Brake Pad Heavy Duty Air" → 13-001-HD
  Reason: Position (front) + duty (heavy) + type (air) all clear

✓ "Rear Brake Rotor 15 inch" → 13-061
  Reason: Position (rear) + component (rotor) + size specified

✓ "Steer Axle Brake Caliper" → 13-031
  Reason: Position (steer/front) + component (caliper)

PROBLEMATIC CASES:
✗ "Brake Pad" → INSUFFICIENT INFO
  Reason: Missing position (front/rear?)

✗ "Heavy Duty Brake Component" → REQUIRES WEB SEARCH
  Reason: Component type unclear, position missing

✗ "Universal Brake Pad" → FLAG FOR REVIEW
  Reason: "Universal" suggests multiple applications

==========================================
EDGE CASES & SPECIAL HANDLING
==========================================

1. COMBINATION KITS:
   Example: "Front and Rear Brake Pad Kit"
   → Should be split into two separate mappings
   → Or map to kit code if customer has kit codes

2. AFTERMARKET VS OEM:
   - Both map to same VMRS codes
   - Note manufacturer in description field
   - No separate codes for aftermarket

3. REMANUFACTURED PARTS:
   - Map to same codes as new parts
   - Add "REMAN" to notes field
   - Quality level not reflected in VMRS code

4. CROSS-REFERENCE PARTS:
   Example: "Replaces ABC-123, fits XYZ-456"
   → Ignore cross-reference info for VMRS mapping
   → Map based on actual part function only

==========================================
END OF RULES FILE
==========================================
```

### Example: `search_template_system_13.txt`

```
SYSTEM 13: Brake Components Search Template

Base Query Format:
"{Part Name} {Part Code} specifications"

Additional Search Terms by Category:

BRAKE PADS/SHOES:
- Add: "for front or rear component"
- Add: "heavy duty or light duty"
- Example: "Brake Pad Set ABC123 specifications for front or rear component"

ROTORS/DRUMS:
- Add: "diameter specifications"
- Add: "vehicle application"
- Example: "Brake Rotor XYZ789 diameter specifications vehicle application"

CALIPERS:
- Add: "axle position"
- Add: "piston configuration"
- Example: "Brake Caliper DEF456 axle position piston configuration"

Search Priority:
1. Manufacturer's official product pages
2. Cross-reference catalogs (e.g., AutoZone, NAPA)
3. Technical specification sheets
4. OEM parts databases

Information to Extract:
- Component position (front/rear/drive/trailer)
- Brake system type (air/hydraulic)
- Duty level (heavy/light/standard)
- Dimensions (diameter, width, thickness)
- Application (vehicle types, makes, models)
- Manufacturer details

Minimum Required Info for Mapping:
- Component type (pad/rotor/caliper/drum)
- Position (front/rear)
- Brake type (air/hydraulic) if not obvious

Flag for Human Review if:
- Conflicting information across sources
- Position unclear after research
- Custom or modified component
```

---

## Processing Workflow

### Overall Process Flow

```
PHASE 1: INITIALIZATION
├─ Load customer VMRS catalog
├─ Load system-specific rules
├─ Initialize validated parts databases
└─ Prepare output directories

PHASE 2: CLASSIFICATION (Agent 1)
├─ Load all parts from catalog
├─ Classify and group by system code
├─ Output: parts_grouped_by_system.json
└─ Generate processing manifest

PHASE 3: SYSTEM-BY-SYSTEM PROCESSING
For each system_code in grouped_parts:
  │
  ├─ STAGE 1: Pattern Matching (Agent 2)
  │   ├─ Load system rules
  │   ├─ Load validated parts for this system
  │   ├─ Process in batches of 5-10
  │   ├─ Output: high_confidence_mappings.csv
  │   └─ Output: parts_for_web_search.csv
  │
  ├─ STAGE 2: Web Research (Agent 3) [CONDITIONAL]
  │   ├─ For each part in parts_for_web_search:
  │   │   ├─ Load search template
  │   │   ├─ Execute web search
  │   │   ├─ Extract system-specific attributes
  │   │   └─ Store enriched description
  │   └─ Output: enriched_descriptions.json
  │
  ├─ STAGE 3: Code Mapping (Agent 4) [CONDITIONAL]
  │   ├─ For each enriched part:
  │   │   ├─ Load customer catalog subset
  │   │   ├─ Load system rules
  │   │   ├─ Map to VMRS code
  │   │   └─ Assign confidence
  │   └─ Output: web_mapped_parts.csv
  │
  └─ STAGE 4: Validation (Agent 5)
      ├─ Combine all mappings for this system
      ├─ Validate in batches of 5-10
      ├─ Check against rules and catalog
      ├─ Output: validated_mappings_system_{code}.csv
      └─ Output: flagged_items_system_{code}.csv

PHASE 4: AGGREGATION
├─ Combine all system outputs
├─ Generate master_output.csv
├─ Generate flagged_for_review.csv
└─ Generate processing_report.txt

PHASE 5: ERP PREPARATION
├─ Format master_output.csv for ERP import
├─ Validate data integrity
└─ Generate import manifest
```

### Batch Processing Strategy

**Agent 1 (Classifier):**
- Process: ALL parts in one execution
- Reason: Need to see full catalog for system assignment
- Output: Grouped by system code

**Agent 2 (Pattern Matcher):**
- Process: 5-10 parts per batch
- Constraint: All parts in batch must have same system code
- Reason: Load only relevant rules and validated data

**Agent 3 (Web Researcher):**
- Process: 1 part at a time
- Reason: Individual web searches, no context contamination
- Rate limiting: Consider API rate limits

**Agent 4 (VMRS Mapper):**
- Process: 1 part at a time
- Reason: Each mapping requires fresh context with description
- Input: One enriched description at a time

**Agent 5 (Validator):**
- Process: 5-10 parts per batch
- Constraint: All parts in batch must have same system code
- Reason: Can cross-validate within system efficiently

### Error Handling & Retry Logic

```python
# Pseudo-code for error handling

def process_with_retry(agent_function, part, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = agent_function(part)
            if validate_result(result):
                return result
            else:
                log_invalid_result(part, result, attempt)
        except APIError as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 5  # Exponential backoff
                time.sleep(wait_time)
            else:
                log_failure(part, e)
                flag_for_manual_review(part, reason="API_ERROR")
        except Exception as e:
            log_failure(part, e)
            flag_for_manual_review(part, reason="PROCESSING_ERROR")
            break
    
    return None  # Failed after all retries
```

### Progress Tracking

```python
# Progress tracking structure
progress = {
    "total_parts": 0,
    "classified": 0,
    "pattern_matched": 0,
    "web_searched": 0,
    "mapped": 0,
    "validated": 0,
    "failed": 0,
    "by_system": {
        "10": {"total": 0, "completed": 0},
        "13": {"total": 0, "completed": 0},
        # ...
    },
    "start_time": "2025-01-15T10:00:00Z",
    "estimated_completion": "2025-01-15T14:30:00Z"
}
```

---

## Technical Specifications

### Technology Stack

**Language:** Python 3.9+

**Required Libraries:**
```python
anthropic>=0.30.0      # Claude API client
pandas>=2.0.0          # Data manipulation
requests>=2.31.0       # HTTP requests (if needed)
python-dotenv>=1.0.0   # Environment configuration
tqdm>=4.66.0           # Progress bars
jsonschema>=4.19.0     # JSON validation
```

**Project Structure:**
```
vmrs-parts-mapper/
├── agents/
│   ├── __init__.py
│   ├── agent_1_classifier.py
│   ├── agent_2_pattern_matcher.py
│   ├── agent_3_web_researcher.py
│   ├── agent_4_vmrs_mapper.py
│   └── agent_5_validator.py
│
├── rules/
│   ├── rules_system_10_lubrication.txt
│   ├── rules_system_13_brakes.txt
│   ├── rules_system_17_tires.txt
│   └── search_templates/
│       ├── search_template_system_10.txt
│       ├── search_template_system_13.txt
│       └── search_template_system_17.txt
│
├── data/
│   ├── input/
│   │   ├── parts_catalog.csv
│   │   └── customer_vmrs_catalog.csv
│   ├── validated/
│   │   ├── validated_parts_system_10.csv
│   │   ├── validated_parts_system_13.csv
│   │   └── validated_parts_system_17.csv
│   ├── intermediate/
│   │   ├── parts_grouped_by_system.json
│   │   ├── enriched_descriptions.json
│   │   └── processing_manifest.json
│   ├── enrichment/
│   │   └── web_search_cache.csv
│   └── output/
│       ├── master_output.csv
│       ├── flagged_for_review.csv
│       └── processing_report.txt
│
├── utils/
│   ├── __init__.py
│   ├── claude_api.py          # Claude API wrapper
│   ├── data_loader.py         # CSV/JSON loading utilities
│   ├── batch_processor.py     # Batch processing logic
│   ├── rules_loader.py        # Rules file parser
│   └── validators.py          # Output validation
│
├── config/
│   ├── __init__.py
│   └── settings.py            # Configuration constants
│
├── tests/
│   ├── test_agents.py
│   ├── test_rules.py
│   └── test_integration.py
│
├── main.py                    # Main orchestrator
├── requirements.txt
├── .env.example
└── README.md
```

### API Configuration

**Claude API Settings:**
```python
# config/settings.py

CLAUDE_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": {
        "agent_1": 4000,
        "agent_2": 3000,
        "agent_3": 2000,
        "agent_4": 2000,
        "agent_5": 2000
    },
    "temperature": 0.0,  # Deterministic for all agents
    "timeout": 120,  # seconds
    "max_retries": 3
}

BATCH_SIZES = {
    "agent_1": None,  # Process all at once
    "agent_2": 10,
    "agent_3": 1,
    "agent_4": 1,
    "agent_5": 10
}

CONFIDENCE_THRESHOLDS = {
    "auto_approve": 90,
    "medium_confidence": 70,
    "require_web_search": 70
}
```

**Environment Variables:**
```bash
# .env
ANTHROPIC_API_KEY=your_api_key_here
LOG_LEVEL=INFO
OUTPUT_DIR=data/output
MAX_WORKERS=4  # For parallel processing if implemented
```

### Data Validation Schemas

**JSON Schema for Agent 1 Output:**
```json
{
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
```

### Performance Requirements

**Processing Speed:**
- Agent 1: 100 parts/minute
- Agent 2: 50 parts/minute (pattern matching)
- Agent 3: 20 parts/minute (web search bottleneck)
- Agent 4: 30 parts/minute
- Agent 5: 50 parts/minute

**Scalability:**
- Handle up to 50,000 parts in initial bulk load
- Process 100-500 daily additions efficiently
- Parallel processing for independent batches (future enhancement)

**Resource Usage:**
- Memory: <2GB RAM for typical batch sizes
- API Calls: Estimate 1-5 calls per part depending on routing
- Storage: Minimal (CSV/JSON files)

---

## Success Criteria

### Quantitative Metrics

**Accuracy:**
- ≥95% correct system classification (Agent 1)
- ≥90% correct VMRS code assignment (overall)
- <5% false positives (incorrect mappings)
- Agent 5 catches ≥95% of mapping errors

**Efficiency:**
- ≥70% parts mapped without web search (Agent 2)
- ≥90% web-searched parts successfully mapped (Agent 4)
- <10% parts require human review on first pass

**Processing:**
- Complete 10,000 part bulk load in <8 hours
- Process daily additions (100-500 parts) in <2 hours
- No degradation in accuracy over long runs

### Qualitative Metrics

**Reliability:**
- Consistent results across multiple runs
- Proper handling of edge cases
- No hallucinated VMRS codes

**Maintainability:**
- Rules files easily updateable by non-programmers
- Clear error messages and logging
- Audit trail available if needed

**Usability:**
- CSV outputs directly importable to ERP
- Human review queue well-organized
- Processing reports clear and actionable

### Test Cases

**Test Set 1: Known Validated Parts (100 parts)**
- Requirement: 100% accuracy on previously validated parts
- Purpose: Ensure pattern matching works correctly

**Test Set 2: Difficult Categories (50 parts each)**
- Brakes: Complex position/type combinations
- Tires: Various sizes and applications
- Filters: Different filter types and applications
- Requirement: ≥90% correct mapping

**Test Set 3: Ambiguous Parts (30 parts)**
- Parts with missing information
- Generic part names
- Requirement: Properly flag for human review

**Test Set 4: Custom Codes (20 parts)**
- Parts that map to customer's custom VMRS codes
- Requirement: Correctly identify as custom codes

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Deliverables:**
- Project structure and utilities
- Claude API integration
- Data loading and validation
- Agent 1 (Classifier) implementation
- Basic rules files for System 13 (Brakes)

**Testing:**
- Classify 1000-part sample
- Verify grouping by system code
- Validate JSON output structure

### Phase 2: Core Agents (Week 2)
**Deliverables:**
- Agent 2 (Pattern Matcher) implementation
- Agent 5 (Validator) implementation
- Rules files for Systems 10, 17
- Validated parts database structure

**Testing:**
- Pattern match 500 parts for System 13
- Validate outputs
- Test batch processing

### Phase 3: Web Research (Week 3)
**Deliverables:**
- Agent 3 (Web Researcher) implementation
- Agent 4 (VMRS Mapper) implementation
- Search templates for all systems
- Web search caching

**Testing:**
- Research and map 100 difficult parts
- Validate enrichment quality
- Test end-to-end flow for one system

### Phase 4: Integration & Testing (Week 4)
**Deliverables:**
- Main orchestrator
- Complete workflow integration
- Error handling and retry logic
- Progress tracking and reporting

**Testing:**
- Full 10,000-part bulk load test
- All systems processing
- Performance benchmarking
- Error recovery testing

### Phase 5: Production Ready (Week 5)
**Deliverables:**
- Documentation
- ERP export formatting
- Daily operations workflow
- Training materials

**Testing:**
- User acceptance testing
- Production data validation
- Human review interface verification

---

## Appendix

### A. Common VMRS Systems Reference

```
System 10: Lubrication
  - Oil filters, transmission filters, hydraulic filters
  - Lubricants and fluids

System 13: Brakes
  - Brake pads, shoes, rotors, drums, calipers
  - Air brake components
  - Hydraulic brake components

System 14: Frame and Frame Components
  - Frame members
  - Cross members
  - Frame modifications

System 15: Steering
  - Steering components
  - Power steering pumps

System 17: Tires and Wheels
  - Tires (steer, drive, trailer)
  - Wheels and rims
  - Tire accessories

System 18: Suspension
  - Springs
  - Shock absorbers
  - Suspension components
```

### B. Glossary

**VMRS:** Vehicle Maintenance Reporting Standard - standardized coding system for vehicle components and repairs

**System Code:** Top-level VMRS category (e.g., 13 for Brakes)

**Detail Code:** Specific component code within a system (e.g., 13-001 for Front Brake Pad)

**Custom Code:** Non-standard VMRS code specific to customer's system (~10% of codes)

**Confidence Score:** 0-100 value indicating certainty of mapping

**Pattern Matching:** Mapping based on similarity to validated parts

**Enrichment:** Adding detailed information through web research

**Heavy Duty:** Commercial/industrial grade components (class 7-8 trucks)

**Light Duty:** Consumer/light commercial grade (class 1-6 vehicles)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-18 | System Design Team | Initial PRD based on requirements gathering |

---

## Approval

This document requires approval from:
- [ ] Project Stakeholder
- [ ] Technical Lead
- [ ] Development Team

**Document Status:** READY FOR IMPLEMENTATION

---

**END OF DOCUMENT**
