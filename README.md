# VMRS Parts Classification System

An agentic approach to AI-powered mapping of vehicle parts catalogs to VMRS (Vehicle Maintenance Reporting Standard) codes using Claude AI.

## Overview

This system uses five specialized AI agents working in sequence to classify and map vehicle parts from a company's catalog to a partner's VMRS codes. The multi-agent architecture prevents degradation over time while maintaining >90% accuracy.

## Key Features

- **Multi-Agent Pipeline**: Five specialized agents with narrow focus and minimal context
- **System-Specific Rules**: Customizable rules for different VMRS systems (Brakes, Tires, Filters, etc.)
- **Conditional Web Research**: Automatic web search only when needed
- **High Accuracy**: >90% correct VMRS code assignment with <5% false positives
- **Scalable**: Handle bulk loads of 10,000+ parts and daily additions of 100-500 parts
- **ERP-Ready Output**: Direct CSV import to ERP systems

## Architecture

The system processes parts through five agents:

1. **Agent 1: System Classifier** - Classifies parts into VMRS system codes
2. **Agent 2: Pattern Matcher** - Maps using rules and validated examples
3. **Agent 3: Web Researcher** - Researches unmapped parts (conditional)
4. **Agent 4: VMRS Mapper** - Maps researched parts to codes (conditional)
5. **Agent 5: QA Validator** - Final validation before output

## Quick Start

### Prerequisites

- Python 3.9+
- Anthropic API key
- pip or conda for package management

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd fluffy-dollop
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

4. Prepare input data:
   - Place your parts catalog in `data/input/parts_catalog.csv`
   - Place customer VMRS catalog in `data/input/customer_vmrs_catalog.csv`

### Usage

Run the main classification pipeline:

```bash
python main.py --input data/input/parts_catalog.csv
```

Options:
- `--input PATH`: Path to input parts catalog (default: data/input/parts_catalog.csv)
- `--vmrs-catalog PATH`: Path to customer VMRS catalog
- `--output PATH`: Path for output file
- `--dry-run`: Run without saving outputs
- `--verbose`: Enable verbose logging

## Project Structure

```
fluffy-dollop/
├── agents/              # Five specialized AI agents
├── rules/               # System-specific rules and search templates
├── data/
│   ├── input/          # Input CSV files
│   ├── validated/      # Previously validated parts
│   ├── intermediate/   # Processing files
│   ├── enrichment/     # Web search cache
│   └── output/         # Final outputs (master_output.csv, flagged_for_review.csv)
├── utils/              # Utilities (API, data loading, validation)
├── config/             # Configuration settings
├── tests/              # Test files
├── main.py             # Main orchestrator
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── CLAUDE.md           # Project reference for Claude AI
└── README.md           # This file
```

## Configuration

### Environment Variables

Create a `.env` file with:

```bash
ANTHROPIC_API_KEY=your_api_key_here
LOG_LEVEL=INFO
```

### System Rules

Customize rules for each VMRS system in the `rules/` directory:
- `rules_system_10_lubrication.txt`
- `rules_system_13_brakes.txt`
- `rules_system_17_tires.txt`

## Output Files

The system generates three main outputs in `data/output/`:

1. **master_output.csv** - ERP-ready file with all validated mappings
2. **flagged_for_review.csv** - Parts requiring human review
3. **processing_report.txt** - Processing statistics and summary

## Development Status

**Current Phase:** Foundation (Phase 1)

- ✅ Project structure implemented
- ✅ Configuration and utilities created
- ✅ Rules files for Systems 10, 13, 17
- ⏳ Agent implementations (in progress)
- ⏳ Integration and testing
- ⏳ Production ready

## Documentation

- **CLAUDE.md** - Comprehensive project reference and development guidelines
- **PRD_VMRS_Parts_Classification_System.md** - Full product requirements document

## Success Criteria

### Quantitative
- ≥95% correct system classification
- ≥90% correct VMRS code assignment
- <5% false positives
- ≥70% parts mapped without web search

### Performance
- Complete 10,000 part bulk load in <8 hours
- Process daily additions (100-500 parts) in <2 hours
- No degradation in accuracy over long runs

## Testing

Run tests with:

```bash
pytest tests/
```

## Contributing

This is a specialized project for VMRS parts classification. For modifications:

1. Review `CLAUDE.md` for architecture guidelines
2. Follow the stateless agent pattern
3. Maintain temperature=0.0 for deterministic results
4. Test with sample data before production use

## License

[Add your license information here]

## Contact

[Add your contact information here] 
