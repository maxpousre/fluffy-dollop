# Agent 1 Testing Guide

This guide walks you through testing the newly implemented Agent 1: System Classifier.

## What Was Implemented

Agent 1 now has complete functionality for:
- **System Classification**: Classifies parts into VMRS system codes (10, 13, 17, etc.)
- **Routing Decisions**: Determines next processing stage for each part
  - `EXACT_MATCH`: Direct match found in customer catalog
  - `PATTERN_MATCH_NEEDED`: Needs Agent 2 (pattern matching)
  - `WEB_SEARCH_NEEDED`: Needs Agent 3 (web research)
- **Output Grouping**: Groups classified parts by system code
- **Validation**: Ensures all outputs conform to expected schema

## Setup Instructions

### 1. Create Environment File

Copy the example environment file and add your Anthropic API key:

```bash
cp .env.example .env
```

Then edit `.env` and add your actual API key:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

Get your API key from: https://console.anthropic.com/

### 2. Create Output Directories

```bash
mkdir -p data/intermediate data/output data/enrichment
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `anthropic` - Claude API client
- `pandas` - Data manipulation
- `python-dotenv` - Environment variables
- `jsonschema` - JSON validation
- And other dependencies

### 4. Verify Input Data Exists

Check that you have the required input files:
- `data/input/parts_catalog.csv` - Your parts to classify
- `data/input/customer_vmrs_catalog.csv` - Customer's VMRS codes

Both files should already exist in your project.

## Running the Test

### Quick Test (Recommended)

Run the provided test script:

```bash
python test_agent_1_manual.py
```

This will:
1. Load your parts catalog (15 sample parts)
2. Load customer VMRS catalog
3. Classify all parts using Agent 1
4. Save results to `data/intermediate/parts_grouped_by_system.json`
5. Display comprehensive summary statistics

### Expected Output

You should see output like:

```
======================================================================
AGENT 1 TEST: System Classifier
======================================================================

[Step 1] Loading input data...
  Loaded 15 parts from catalog
  Loaded 7653 VMRS codes from customer catalog
  Customer catalog contains 154 unique systems

[Step 2] Initializing Claude API client...
  Claude client initialized successfully

[Step 3] Initializing Agent 1: System Classifier...
  Agent 1 initialized successfully

[Step 4] Classifying parts...
  Processing 15 parts...
  Successfully classified 15 parts into 3 system codes
  System 10 (Lubrication): 4 parts
  System 13 (Brakes): 6 parts
  System 17 (Tires and Wheels): 5 parts

[Step 5] Saving results...
  Results saved to: data/intermediate/parts_grouped_by_system.json

[Step 6] Classification Summary
======================================================================
Total parts classified: 15
Number of systems: 3

System 10: Lubrication
  Parts: 4
    PATTERN_MATCH_NEEDED: 4
  Example parts:
    - DEF456: Engine Oil Filter Spin-On
      Routing: PATTERN_MATCH_NEEDED, Confidence: 92%
    ...

System 13: Brakes
  Parts: 6
    PATTERN_MATCH_NEEDED: 6
  Example parts:
    - ABC123: Brake Pad Set Front Heavy Duty
      Routing: PATTERN_MATCH_NEEDED, Confidence: 95%
    ...

System 17: Tires and Wheels
  Parts: 5
    PATTERN_MATCH_NEEDED: 5
  Example parts:
    - XYZ789: 11R22.5 Drive Tire 14 Ply
      Routing: PATTERN_MATCH_NEEDED, Confidence: 98%
    ...

Overall Routing Statistics:
  PATTERN_MATCH_NEEDED: 15 (100.0%)

======================================================================
TEST COMPLETED SUCCESSFULLY!
======================================================================
```

## What to Check

### 1. Verify Output File

Check the generated file: `data/intermediate/parts_grouped_by_system.json`

It should have this structure:

```json
{
  "13": {
    "system_code": "13",
    "system_name": "Brakes",
    "parts": [
      {
        "part_code": "ABC123",
        "part_name": "Brake Pad Set Front Heavy Duty",
        "routing": "PATTERN_MATCH_NEEDED",
        "confidence": 95,
        "reasoning": "Clear brake component, belongs to System 13"
      }
    ]
  },
  "10": { ... },
  "17": { ... }
}
```

### 2. Validate Classifications

Check that:
- All parts were classified (count matches input)
- System codes are correct for each part type:
  - Brake parts → System 13
  - Tire parts → System 17
  - Filter parts → System 10
- Confidence scores are reasonable (typically 80-100)
- Routing decisions make sense

### 3. Check Logs

Review the console output for:
- No error messages
- All parts successfully processed
- Reasonable distribution across systems

## Troubleshooting

### Error: "ANTHROPIC_API_KEY not found"

**Solution**: Make sure you created the `.env` file and added your API key.

```bash
# Check if .env exists
ls -la .env

# If not, copy from example
cp .env.example .env

# Edit and add your key
nano .env  # or use your preferred editor
```

### Error: "No such file or directory"

**Solution**: Create the output directories:

```bash
mkdir -p data/intermediate data/output data/enrichment
```

### Error: "ModuleNotFoundError"

**Solution**: Install dependencies:

```bash
pip install -r requirements.txt
```

### API Rate Limiting or Errors

**Solution**: The script has built-in retry logic with exponential backoff. If you see rate limiting, it will automatically retry up to 3 times.

### Unexpected Classifications

**What to check**:
1. Review the `reasoning` field in the output for each part
2. Check if the customer catalog contains relevant system codes
3. Verify input part names are descriptive enough

## Next Steps After Successful Test

Once Agent 1 is working correctly:

1. ✅ **Review Output**: Manually verify a few classifications
2. ✅ **Check Routing**: Ensure routing decisions are appropriate
3. ✅ **Validate Confidence**: Check if confidence scores are reasonable
4. 🔄 **Expand Test Data**: Add more parts to `parts_catalog.csv` if desired
5. 🔄 **Implement Agent 2**: Start building the Pattern Matcher agent
6. 🔄 **Integration Testing**: Test the full pipeline once all agents are built

## File Locations

- **Test Script**: `test_agent_1_manual.py`
- **Agent Implementation**: `agents/agent_1_classifier.py`
- **Input Data**: `data/input/parts_catalog.csv`
- **Customer Catalog**: `data/input/customer_vmrs_catalog.csv`
- **Output File**: `data/intermediate/parts_grouped_by_system.json`
- **Configuration**: `config/settings.py`

## Performance Expectations

- **Processing Time**: ~10-30 seconds for 15 parts
- **API Tokens**: ~5,000-10,000 tokens per run (input + output)
- **Accuracy Target**: ≥95% correct system classification

## Testing with More Parts

To test with additional parts, edit `data/input/parts_catalog.csv`:

```csv
part_code,part_name
ABC123,Brake Pad Set Front Heavy Duty
XYZ789,11R22.5 Drive Tire 14 Ply
NEW001,Air Filter Heavy Duty
NEW002,Front Shock Absorber
```

Then re-run the test script.

## Questions or Issues?

If you encounter any problems:
1. Check this troubleshooting section
2. Review the logs for specific error messages
3. Verify all setup steps were completed
4. Check that your API key is valid and has credits

---

**Ready to test?** Run: `python test_agent_1_manual.py`
