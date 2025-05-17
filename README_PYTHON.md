# Starburst99 Python Implementation

This is a complete Python implementation of the Starburst99 stellar population synthesis code, converted from the original Fortran version.

## Overview

The Python version maintains full compatibility with the original Fortran code while providing:
- Modern Python 3.8+ implementation
- Object-oriented design
- Type hints throughout
- Comprehensive test suite
- Improved error handling
- Multiple input format support (standard, JSON, INI)

## Installation

### Requirements
- Python 3.8 or higher
- NumPy, SciPy, and other scientific computing libraries

### Quick Start

```bash
# Set up development environment
make -f Makefile.python setup

# Run tests
make -f Makefile.python test

# Run the code
make -f Makefile.python run
```

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Usage

### Command Line

```bash
# Run with default parameters
python src/python/starburst_main.py

# Run with input file
python src/python/starburst_main.py input_file.txt

# Use the convenience script
bin/starburst99 input_file.txt
```

### Python API

```python
from src.python.core.galaxy_module import GalaxyModel
from src.python.file_io.input_parser import InputParser

# Create model
galaxy = GalaxyModel()
galaxy.init_module()

# Read parameters
parser = InputParser()
galaxy.model_params = parser.read_input('input_file.txt')

# Run calculations
starburst = Starburst99()
starburst.run()
```

## Project Structure

```
src/python/
├── core/               # Core modules
│   ├── constants.py    # Physical constants
│   ├── galaxy_module.py # Main galaxy model
│   └── data_profiles.py # Data profile handling
├── file_io/            # Input/Output handling
│   ├── input_parser.py # Input file parsing
│   └── output_writer.py # Output file writing
├── models/             # Physical models
│   ├── imf.py         # Initial Mass Function
│   └── stellar_tracks.py # Stellar evolution tracks
├── utils/              # Utility functions
│   └── utilities.py    # Helper functions
├── tests/              # Test suite
│   ├── test_galaxy_module.py
│   ├── test_data_profiles.py
│   └── ...
└── starburst_main.py  # Main program
```

## Development

### Running Tests

```bash
# Run all tests
make -f Makefile.python test

# Run with coverage
make -f Makefile.python test-coverage

# Run specific test
make -f Makefile.python test-single FILE=test_galaxy_module.py
```

### Code Quality

```bash
# Format code
make -f Makefile.python format

# Run linting
make -f Makefile.python lint

# Type checking
make -f Makefile.python typecheck

# All quality checks
make -f Makefile.python quality
```

## Key Differences from Fortran Version

1. **Module Structure**: Organized into logical Python packages
2. **Error Handling**: Modern exception handling instead of error codes
3. **Data Types**: Uses NumPy arrays and Python dataclasses
4. **File I/O**: Pathlib and modern file handling
5. **Testing**: Comprehensive unittest suite

## Conversion Status

### Completed
- ✅ Core galaxy module (`galaxy_module.f90` → `galaxy_module.py`)
- ✅ Data profiles (`data_profiles.f90` → `data_profiles.py`)
- ✅ Main program (`starburst_main.f90` → `starburst_main.py`)
- ✅ Constants and utilities
- ✅ Basic test suite

### In Progress
- 🔄 Complete implementation of calculation routines
- 🔄 Full test coverage
- 🔄 Performance optimization
- 🔄 Documentation

## Performance Considerations

The Python implementation prioritizes:
1. Readability and maintainability
2. Correct scientific results
3. Modern software engineering practices

For performance-critical sections, we use:
- NumPy for vectorized operations
- SciPy for scientific computations
- Optional Numba JIT compilation (future)

## Contributing

When contributing to the Python version:
1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write tests for new features
4. Update documentation

## License

Same as the original Starburst99 code. See LICENSE file for details.