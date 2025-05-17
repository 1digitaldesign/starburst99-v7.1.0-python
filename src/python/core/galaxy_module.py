"""Galaxy module for shared data and constants"""

import numpy as np
from typing import Optional, List, Tuple, Union
from dataclasses import dataclass, field
import logging
from pathlib import Path

from .constants import *
# Remove the import - implement functions here


@dataclass
class ModelParameters:
    """Type containing all model configuration parameters"""
    name: str = "default"
    sf_mode: int = 0                    # Star formation mode: >0 continuous, <=0 fixed mass
    total_mass: float = 1.0             # Total stellar mass (10^6 solar masses)
    sf_rate: float = 1.0                # Star formation rate (solar masses per year)
    
    # IMF parameters
    num_intervals: int = 1              # Number of intervals for the IMF
    exponents: List[float] = field(default_factory=lambda: [2.35])
    mass_limits: List[float] = field(default_factory=lambda: [1.0, 100.0])
    sn_cutoff: float = 8.0              # Supernova cut-off mass (solar masses)
    bh_cutoff: float = 120.0            # Black hole cut-off mass (solar masses)
    
    # Model selection parameters
    metallicity_id: int = 0             # Metallicity + tracks identifier
    wind_model: int = 0                 # Wind model (0: evolution, 1: emp., 2: theor., 3: Elson)
    
    # Time step parameters
    initial_time: float = 0.0           # Initial time (years)
    time_scale: int = 0                 # 0=linear, 1=logarithmic
    time_step: float = 1.0              # Time step (years) if time_scale=0
    num_steps: int = 10                 # Number of steps if time_scale=1
    max_time: float = 100.0            # Last grid point (years)
    
    # Atmosphere and library options
    atmosphere_model: int = 0           # Atmosphere model options
    hires_metallicity: int = 0          # Metallicity of high-resolution models
    uv_library: int = 1                 # Library for UV line spectrum (1=solar, 2=LMC/SMC)
    
    # Output control
    outputs: List[bool] = field(default_factory=lambda: [True] * 15)  # Output flags
    
    # RSG parameters
    rsg_vt: int = 0                     # RSG velocity threshold
    rsg_params: int = 0                 # RSG parameters


@dataclass
class TrackData:
    """Type for stellar evolutionary track data"""
    # Basic track information
    num_masses: int = 0                 # Number of initial masses
    num_points: int = 0                 # Number of time points per track
    metallicity: float = 0.0            # Z value for this track set
    source: str = ""                    # Source of track data (Geneva, Padova, etc.)
    
    # Main track arrays
    init_mass: Optional[np.ndarray] = None        # Initial stellar mass (solar masses)
    log_init_mass: Optional[np.ndarray] = None    # Log of initial mass
    
    # Per-track, per-time point data
    age: Optional[np.ndarray] = None              # Stellar age (years)
    log_age: Optional[np.ndarray] = None          # Log of age
    mass: Optional[np.ndarray] = None             # Current mass (solar masses)
    log_mass: Optional[np.ndarray] = None         # Log of current mass
    log_lum: Optional[np.ndarray] = None          # Log luminosity (solar units)
    log_teff: Optional[np.ndarray] = None         # Log effective temperature (K)
    mdot: Optional[np.ndarray] = None             # Mass loss rate (solar masses/yr)
    
    # Surface abundances
    h_frac: Optional[np.ndarray] = None           # Surface hydrogen mass fraction
    he_frac: Optional[np.ndarray] = None          # Surface helium mass fraction
    c_frac: Optional[np.ndarray] = None           # Surface carbon mass fraction
    n_frac: Optional[np.ndarray] = None           # Surface nitrogen mass fraction
    o_frac: Optional[np.ndarray] = None           # Surface oxygen mass fraction
    
    def init(self, num_masses: int, num_points: int):
        """Initialize track data arrays"""
        self.num_masses = num_masses
        self.num_points = num_points
        
        # Initialize 1D arrays
        self.init_mass = np.zeros(num_masses)
        self.log_init_mass = np.zeros(num_masses)
        
        # Initialize 2D arrays (mass index, time index)
        shape = (num_masses, num_points)
        self.age = np.zeros(shape)
        self.log_age = np.zeros(shape)
        self.mass = np.zeros(shape)
        self.log_mass = np.zeros(shape)
        self.log_lum = np.zeros(shape)
        self.log_teff = np.zeros(shape)
        self.mdot = np.zeros(shape)
        
        # Initialize abundance arrays
        self.h_frac = np.zeros(shape)
        self.he_frac = np.zeros(shape)
        self.c_frac = np.zeros(shape)
        self.n_frac = np.zeros(shape)
        self.o_frac = np.zeros(shape)
    
    def cleanup(self):
        """Clean up allocated arrays"""
        # In Python, setting to None allows garbage collection
        self.init_mass = None
        self.log_init_mass = None
        self.age = None
        self.log_age = None
        self.mass = None
        self.log_mass = None
        self.log_lum = None
        self.log_teff = None
        self.mdot = None
        self.h_frac = None
        self.he_frac = None
        self.c_frac = None
        self.n_frac = None
        self.o_frac = None
    
    def get_mass_index(self, mass: float) -> int:
        """Find the index for a given mass"""
        if self.init_mass is None:
            return -1
        
        # Find closest mass index
        idx = np.argmin(np.abs(self.init_mass - mass))
        return idx
    
    def interpolate_in_time(self, mass_idx: int, time: float) -> dict:
        """Interpolate track data at a given time"""
        if self.age is None or mass_idx >= self.num_masses:
            return {}
        
        # Get age array for this mass
        ages = self.age[mass_idx, :]
        
        # Find interpolation indices
        idx = np.searchsorted(ages, time)
        if idx == 0:
            idx = 1
        elif idx >= self.num_points:
            idx = self.num_points - 1
        
        # Linear interpolation factor
        t0, t1 = ages[idx-1], ages[idx]
        if t1 > t0:
            f = (time - t0) / (t1 - t0)
        else:
            f = 0.0
        
        # Interpolate all quantities
        result = {}
        for attr in ['mass', 'log_lum', 'log_teff', 'mdot', 
                    'h_frac', 'he_frac', 'c_frac', 'n_frac', 'o_frac']:
            arr = getattr(self, attr)
            if arr is not None:
                v0, v1 = arr[mass_idx, idx-1], arr[mass_idx, idx]
                result[attr] = v0 + f * (v1 - v0)
        
        return result


class GalaxyModel:
    """Main galaxy model class containing all model data and parameters"""
    
    def __init__(self):
        """Initialize the galaxy model with default parameters"""
        # Initialize model parameters
        self.model_params = ModelParameters()
        
        # Legacy compatibility - individual variables
        self.model_name = "default"
        self.isf = 0                           # Star formation mode
        self.toma = 1.0                        # Total stellar mass (10^6 solar masses)
        self.sfr = 1.0                         # Star formation rate (solar masses per year)
        
        # IMF parameters
        self.ninterv = 1                       # Number of intervals for the IMF
        self.xponent = np.array([2.35] * NMAXINT)  # IMF exponents
        self.xmaslim = np.array([1.0, 100.0] + [0.0] * (NMAXINT1-2))  # Mass boundaries
        self.sncut = 8.0                       # Supernova cut-off mass
        self.bhcut = 120.0                     # Black hole cut-off mass
        
        # Metallicity and model selection
        self.iz = 0                            # Metallicity + tracks identifier
        self.iwind = 0                         # Wind model
        
        # Time parameters
        self.time1 = 0.0                       # Initial time (10^6 years)
        self.jtime = 0                         # Time scale: 0=linear, 1=logarithmic
        self.tbiv = 1.0                        # Time step (10^6 years) if jtime=0
        self.itbiv = 10                        # Number of steps if jtime=1
        self.tmax = 100.0                      # Last grid point (10^6 years)
        
        # Grid parameters
        self.jmg = 0                           # Synthesis method selection
        self.lmin = 0                          # Min index of evolutionary tracks
        self.lmax = 0                          # Max index of evolutionary tracks
        self.tdel = 1.0                        # Time step for printing spectra
        
        # Atmosphere and library options
        self.iatmos = 0                        # Atmosphere model options
        self.ilib = 0                          # Metallicity of high-resolution models
        self.iline = 1                         # Library for UV line spectrum
        self.ivt = 0                           # RSG velocity threshold
        self.irsg = 0                          # RSG parameters
        
        # Output options (15 flags)
        self.io1 = 1
        self.io2 = 1  
        self.io3 = 1
        self.io4 = 1
        self.io5 = 1
        self.io6 = 1
        self.io7 = 1
        self.io8 = 1
        self.io9 = 1
        self.io10 = 1
        self.io11 = 1
        self.io12 = 1
        self.io13 = 1
        self.io14 = 1
        self.io15 = 1
        
        # Derived time variables
        self.tvar = 0.0                        # Current time step size
        self.tinter = 0.0                      # Number of time steps
        self.tiempo1 = 0.0                     # Current time (log scale)
        self.tstep = 0.0                       # Current time step adjusted
        self.upma = 0.0                        # Upper mass limit
        self.doma = 0.0                        # Lower mass limit
        
        # WR related parameters
        self.iwrt = 0                          # WR temperature adjustment method
        self.iwrscale = 0                      # WR scaling parameter
        self.xmwr = 20.0                       # Minimum mass for WR stars
        
        # SN/nucleosynthesis mass limits
        self.critma = 8.0                      # Critical mass for supernovae
        self.critma_new = 8.0                  # Updated critical mass
        self.critup = 120.0                    # Upper critical mass
        self.critup_new = 120.0                # Updated upper critical mass
        self.critma1 = 8.0                     # Secondary critical mass
        self.critma_new1 = 8.0                 # Updated secondary critical mass
        self.critup1 = 120.0                   # Secondary upper critical mass
        self.critup_new1 = 120.0               # Updated secondary upper critical mass
        
        # Initialize main data arrays
        self.cmass = None                      # Grid of stellar masses
        self.dens = None                       # Number density of stars per mass bin
        self.wavel = None                      # Wavelength grid
        self.spectra = None                    # Spectral data arrays
        
        # Physical output arrays
        self.wind_power = None                 # Wind power per mass bin
        self.sn_rates = None                   # Supernova rates per mass bin
        self.sp_type_counts = None             # Counts of different spectral types
        self.element_yields = None             # Chemical yields for different elements
        self.uv_lines = None                   # UV line strengths
        self.fuv_lines = None                  # FUV line strengths
        self.hires_lines = None                # High-resolution optical line strengths
        
        # Track data for multiple metallicities
        self.tracks = []
        
        # Error message
        self.error_message = ""
        
        # Initialize logging
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging for the galaxy model"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('starburst99.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('GalaxyModel')
    
    def init_module(self):
        """Initialize the module - allocate arrays and set defaults"""
        self.logger.info("Initializing GalaxyModel module")
        
        # Initialize mass grid
        self.cmass = np.zeros(NPGRID)
        self.dens = np.zeros(NPGRID)
        
        # Initialize wavelength grid
        self.wavel = np.zeros(max(NP, NP1))
        
        # Initialize spectral arrays
        self.spectra = np.zeros((100, max(NP, NP1)))  # Adjust dimensions as needed
        
        # Initialize output arrays
        self.wind_power = np.zeros(100)
        self.sn_rates = np.zeros(100)
        self.sp_type_counts = np.zeros(20)  # Assuming ~20 spectral types
        self.element_yields = np.zeros(30)  # Assuming ~30 elements
        self.uv_lines = np.zeros(100)
        self.fuv_lines = np.zeros(50)
        self.hires_lines = np.zeros(200)
    
    def cleanup_module(self):
        """Clean up module resources"""
        self.logger.info("Cleaning up GalaxyModel module")
        
        # Clean up arrays
        self.cmass = None
        self.dens = None
        self.wavel = None
        self.spectra = None
        self.wind_power = None
        self.sn_rates = None
        self.sp_type_counts = None
        self.element_yields = None
        self.uv_lines = None
        self.fuv_lines = None
        self.hires_lines = None
        
        # Clean up tracks
        for track in self.tracks:
            if hasattr(track, 'cleanup'):
                track.cleanup()
        self.tracks = []
    
    def open_file(self, unit: int, filename: Union[str, Path], status: str = 'old',
                  action: str = 'read') -> bool:
        """
        Open a file with error handling
        
        Args:
            unit: File unit number (for compatibility)
            filename: Path to file
            status: File status ('old', 'new', 'replace')
            action: File action ('read', 'write', 'readwrite')
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if isinstance(filename, str):
                filename = Path(filename)
            
            if status == 'old' and not filename.exists():
                self.error_handler(f"File not found: {filename}",
                                 routine='open_file', fatal=False)
                return False
            
            # Store file reference for later use
            # In a real implementation, you'd manage file handles
            return True
            
        except Exception as e:
            self.error_handler(str(e), routine='open_file', fatal=False)
            return False
    
    def error_handler(self, message: str, routine: str = '', fatal: bool = False):
        """
        Handle errors with consistent formatting
        
        Args:
            message: Error message
            routine: Name of routine where error occurred
            fatal: If True, raise exception
        """
        prefix = "FATAL ERROR" if fatal else "WARNING"
        full_message = f"{prefix} in {routine}: {message}"
        
        self.error_message = full_message
        
        if fatal:
            self.logger.error(full_message)
            raise RuntimeError(full_message)
        else:
            self.logger.warning(full_message)


# Utility functions that were in the Fortran module
def flin(x: float, x1: float, x2: float, y1: float, y2: float) -> float:
    """
    Linear interpolation function
    
    Args:
        x: Point to interpolate at
        x1, x2: Known x values
        y1, y2: Known y values
        
    Returns:
        float: Interpolated y value
    """
    if abs(x2 - x1) < np.finfo(float).eps:
        return y1  # Avoid division by zero
    else:
        return y1 + (y2 - y1) * (x - x1) / (x2 - x1)


def integer_to_string(n: int) -> str:
    """Convert integer to string with proper formatting"""
    return str(n)


def exp10(x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Compute 10^x.
    
    Args:
        x: Exponent value(s)
        
    Returns:
        10 raised to the power of x
    """
    return np.power(10.0, x)


def linear_interp(x: float, x_arr: np.ndarray, y_arr: np.ndarray) -> float:
    """
    Perform linear interpolation.
    
    Args:
        x: Value at which to interpolate
        x_arr: Array of x values (must be sorted)
        y_arr: Array of y values
        
    Returns:
        Interpolated y value at x
    """
    # Convert to numpy arrays if needed
    x_arr = np.asarray(x_arr)
    y_arr = np.asarray(y_arr)
    
    if x <= x_arr[0]:
        return y_arr[0]
    elif x >= x_arr[-1]:
        return y_arr[-1]
    
    # Find bracketing indices
    idx = np.searchsorted(x_arr, x) - 1
    
    # Linear interpolation
    x1, x2 = x_arr[idx], x_arr[idx + 1]
    y1, y2 = y_arr[idx], y_arr[idx + 1]
    
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)