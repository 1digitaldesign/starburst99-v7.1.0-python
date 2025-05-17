# Starburst99 Population Synthesis Code (Python Version)

## Overview

Starburst99 is a stellar population synthesis code for modeling the spectrophotometric and related properties of star-forming galaxies. This code calculates observable parameters of stellar populations including:

- Spectral energy distributions from UV to near-IR
- Stellar wind feedback and supernova rates
- Chemical yields from stellar evolution
- Line spectra at various wavelengths and resolutions
- Photometric properties (colors, magnitudes)
- Ionizing photon production

**This repository contains a complete Python implementation** of Starburst99, fully converted from the original Fortran codebase while maintaining all functionality.

**Citation:** Starburst99 should be cited as Leitherer et al. (1999, ApJS, 123, 3), Vazquez & Leitherer (2005; ApJ, 621, 695), Leitherer et al. (2010; ApJS, 189, 309), and Leitherer et al. (2014, ApJS, 213, 1).

## Version History

- **First version:** August 12, 1998 (Claus Leitherer)
- **Version 4.0:** July 2002 - Added blanketed WR models
- **Version 5.0:** December 2004 - Added Padova tracks and high-resolution optical library
- **Version 6.0:** August 25, 2010 - Added theoretical UV spectra
- **Version 7.0.0:** March 2014 - Added rotating tracks and Wolf-Rayet library
- **Version 7.1.0 (Python):** May 2025 - Complete conversion from Fortran to Python with modern architecture and comprehensive testing

## Directory Structure

The package follows a modern Python project structure:

```
starburst99/
├── src/python/        # Python source code
│   ├── core/          # Core modules
│   │   ├── galaxy_module.py      # Core data structures
│   │   ├── data_profiles.py      # Data profile calculations
│   │   └── constants.py          # Physical constants
│   ├── models/        # Scientific models
│   │   ├── imf.py               # Initial Mass Function
│   │   └── stellar_tracks.py     # Stellar evolution tracks
│   ├── file_io/       # Input/Output modules
│   │   ├── input_parser.py      # Input file parsing
│   │   └── output_writer.py     # Output file writing
│   ├── utils/         # Utility functions
│   ├── tests/         # Test suite (74% coverage)
│   └── starburst_main.py        # Main program
├── data/              # Data files (unchanged from Fortran version)
│   ├── tracks/        # Stellar evolutionary tracks
│   ├── lejeune/       # Model atmospheres
│   └── auxil/         # Auxiliary data files
├── json_data/         # JSON versions of data files
├── tools/             # Utility tools
│   └── converters/    # Data conversion utilities
├── scripts/           # Runtime scripts
├── output/            # Runtime output directory
├── docs/              # Documentation
├── tests/             # Integration test files
├── requirements.txt   # Python dependencies
└── setup.py          # Python package setup
```

## Important Note on Data Files

Some large data files have been excluded from this repository due to GitHub file size limitations:

- Several `allstars*.txt` files in the `data/lejeune/` directory
- Corresponding JSON versions in the `json_data/` directory

See `data/lejeune/README_LARGE_FILES.md` and `json_data/README_LARGE_FILES.md` for details on how to obtain or generate these files.

## Installation

### Prerequisites
- Python 3.8 or higher
- NumPy
- SciPy (optional, for specific calculations)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-repo/starburst99-python.git
cd starburst99-python
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package in development mode:
```bash
pip install -e .
```

## Running the Code

### Command Line Interface

```bash
# Basic usage
python -m starburst99 --help

# Run with default parameters
python -m starburst99

# Run with custom input file
python -m starburst99 --input mymodel.input --output mymodel_output

# Enable debug mode
python -m starburst99 --debug
```

### Python API

```python
from starburst99 import Starburst99

# Create model instance
model = Starburst99(input_file="standard.input1")

# Run the model
model.run()

# Access results
spectrum = model.get_spectrum()
sfr = model.get_star_formation_rate()
```

## Input Parameters

The input file contains all model parameters. Key parameters include:

- **Model Designation**: Identifier for the model
- **Star Formation Mode**: Instantaneous (-1) or continuous (>0)
- **Stellar Mass Parameters**: Total mass or SFR
- **IMF Settings**: Exponents and mass boundaries
- **Metallicity Selection**: Choose from Geneva or Padova tracks at various metallicities
- **Time Range**: Initial time, time step, and maximum age
- **Model Atmosphere**: Choice of atmospheric models
- **Output Selection**: Flags for different output products

## Testing

The Python implementation includes a comprehensive test suite with 74% overall coverage:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=starburst99 --cov-report=html

# Run specific test module
pytest tests/test_galaxy_module.py
```

Key test coverage:
- Core modules: 97-100%
- Main program: 97%
- Scientific models: 80-85%
- I/O modules: 80-97%

## Python Implementation Features

The Python conversion includes:

1. **Modern Architecture**
   - Type hints throughout the codebase
   - Dataclasses for configuration
   - Object-oriented design with clear interfaces
   - Modular structure for maintainability

2. **Enhanced Error Handling**
   - Descriptive error messages
   - Input validation
   - Graceful error recovery

3. **Improved Performance**
   - NumPy for numerical computations
   - Vectorized operations where possible
   - Optional SciPy integrations

4. **Better Logging**
   - Configurable logging levels
   - Progress reporting
   - Debug output options

5. **Extended Testing**
   - Unit tests for all modules
   - Integration tests
   - Edge case coverage
   - Performance benchmarks

## Documentation

Additional documentation:
- `README_PYTHON.md`: Python conversion details
- `CONVERSION_SUMMARY.md`: Summary of conversion process
- `DEVELOPMENT.md`: Development guidelines
- `docs/`: Original documentation
- API documentation (generated with Sphinx)

## Contributing

Contributions are welcome! Please see `DEVELOPMENT.md` for guidelines on:
- Code style
- Testing requirements
- Documentation standards
- Pull request process

## Support

While there is no official help desk, the community may assist with questions and issues through:
- GitHub Issues
- Discussion forums
- Email (time permitting)

The code is distributed freely, and users accept sole responsibility for results produced by the code.

---

*Original Fortran version by: Claus Leitherer, Carmelle Robert, Daniel Schaerer, Jeff Goldader, Rosa Gonzalez-Delgado, & Duilia de Mello*

*Python conversion: 2025*

*Disclaimer: This code is distributed freely to the community. The user accepts sole responsibility for the results produced by the code. Although every effort has been made to identify and eliminate errors, we accept no responsibility for erroneous model predictions.*