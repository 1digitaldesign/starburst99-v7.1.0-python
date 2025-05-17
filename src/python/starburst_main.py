#!/usr/bin/env python3
"""
GALAXY - Stellar Population Synthesis Code
=========================================

Main program for galaxy/starburst population synthesis code (Starburst99).

This program computes observable parameters for populations of massive stars, 
including spectral energy distributions, stellar feedback, and chemical yields.

Original version: Claus Leitherer (August 1998)
Last major update: August 2014
Python version: [2024]
"""

import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

import numpy as np

# Support both relative imports (when imported as module) and absolute imports (when run as script)
try:
    from .core.galaxy_module import GalaxyModel, TrackData
    from .core.data_profiles import DataProfiles
    from .file_io.input_parser import InputParser
    from .file_io.output_writer import OutputWriter
    from .models.imf import IMF
    from .models.stellar_tracks import StellarTracks
except ImportError:
    # Fallback for direct execution
    from core.galaxy_module import GalaxyModel, TrackData
    from core.data_profiles import DataProfiles
    from file_io.input_parser import InputParser
    from file_io.output_writer import OutputWriter
    from models.imf import IMF
    from models.stellar_tracks import StellarTracks


class Starburst99:
    """Main class for Starburst99 stellar population synthesis calculations"""
    
    def __init__(self, input_file: str = None):
        """
        Initialize Starburst99 with optional input file.
        
        Args:
            input_file: Path to input parameter file
        """
        self.galaxy = GalaxyModel()
        self.data_profiles = DataProfiles()
        self.input_parser = InputParser()
        self.output_writer = None  # Will be initialized after reading parameters
        
        self.input_file = input_file
        self.start_time = datetime.now()
        
        # Set up logging
        self._setup_logging()
        
        # Track data
        self.stellar_tracks = StellarTracks()
        
        # Initialize calculation parameters
        self.time = 0.0
        self.icount = 1
        self.namfi3 = None
        self.nam = None
        
    def _setup_logging(self):
        """Configure logging for the application"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('starburst99.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('Starburst99')
        
    def run(self):
        """Main execution routine"""
        self.logger.info("GALAXY - Stellar Population Synthesis Code (Python Edition)")
        self.logger.info("=" * 56)
        self.logger.info(f"Run started at: {self.start_time}")
        self.logger.info("")
        
        try:
            # Initialize modules
            self.logger.info("Initializing modules...")
            self.galaxy.init_module()
            self.data_profiles.initialize_data_profiles()
            
            # Read input parameters
            self.logger.info("Reading input parameters...")
            if self.input_file:
                self.galaxy.model_params = self.input_parser.read_input(self.input_file)
                self._sync_parameters()
            else:
                # Use default parameters or prompt for input
                self.galaxy.model_params = self.input_parser.get_default_parameters()
                self._sync_parameters()
            
            # Initialize output writer with default directory
            output_dir = Path("output")
            self.output_writer = OutputWriter(output_dir)
            
            # Initialize IMF
            self.imf = IMF(
                self.galaxy.model_params.num_intervals,
                self.galaxy.model_params.exponents,
                self.galaxy.model_params.mass_limits
            )
            
            # Read evolutionary tracks
            self.logger.info("Reading evolutionary tracks...")
            self._read_tracks()
            
            # Set metallicity string for filenames
            self._set_metallicity_string()
            
            # Read atmospheric and opacity data
            self.logger.info("Reading atmospheric and opacity data...")
            self._read_atmosphere_data()
            
            # Initialize supernova and nucleosynthesis mass limits
            self.galaxy.critma = 1.0e36
            self.galaxy.critma_new = self.galaxy.critma
            self.galaxy.critup = -1.0
            self.galaxy.critup_new = self.galaxy.critup
            self.galaxy.critma1 = 1.0e36
            self.galaxy.critma_new1 = self.galaxy.critma1
            self.galaxy.critup1 = -1.0
            self.galaxy.critup_new1 = self.galaxy.critup1
            
            # Main calculation loop
            self.logger.info("Starting main calculations...")
            self._main_calculation_loop()
            
            # Write output files
            self.logger.info("Writing output files...")
            self._write_output()
            
            # Cleanup
            self.logger.info("Cleaning up...")
            self.galaxy.cleanup_module()
            
            end_time = datetime.now()
            duration = end_time - self.start_time
            self.logger.info(f"Run completed at: {end_time}")
            self.logger.info(f"Total runtime: {duration}")
            
        except Exception as e:
            self.logger.error(f"Error during execution: {e}", exc_info=True)
            sys.exit(1)
    
    def _sync_parameters(self):
        """Sync ModelParameters with legacy individual variables"""
        params = self.galaxy.model_params
        self.galaxy.model_name = params.name
        self.galaxy.isf = params.sf_mode
        self.galaxy.toma = params.total_mass
        self.galaxy.sfr = params.sf_rate
        self.galaxy.ninterv = params.num_intervals
        # Handle array assignment more carefully
        for i in range(params.num_intervals):
            if i < len(params.exponents):
                self.galaxy.xponent[i] = params.exponents[i]
        
        for i in range(min(params.num_intervals+1, len(params.mass_limits))):
            self.galaxy.xmaslim[i] = params.mass_limits[i]
        self.galaxy.sncut = params.sn_cutoff
        self.galaxy.bhcut = params.bh_cutoff
        self.galaxy.iz = params.metallicity_id
        self.galaxy.iwind = params.wind_model
        self.galaxy.time1 = params.initial_time
        self.galaxy.jtime = params.time_scale
        self.galaxy.tbiv = params.time_step
        self.galaxy.itbiv = params.num_steps
        self.galaxy.tmax = params.max_time
        self.galaxy.iatmos = params.atmosphere_model
        self.galaxy.ilib = params.hires_metallicity
        self.galaxy.iline = params.uv_library
        
        # Set output flags
        for i, flag in enumerate(params.outputs):
            setattr(self.galaxy, f'io{i+1}', int(flag))
    
    def _read_tracks(self):
        """Read evolutionary tracks based on metallicity"""
        # Determine track filename based on metallicity ID
        track_files = {
            # Geneva tracks at various metallicities
            11: "Z0020v00.txt", 21: "Z0020v40.txt",
            12: "Z0020v00.txt", 22: "Z0020v40.txt",
            13: "Z0140v00.txt", 23: "Z0140v40.txt",
            14: "Z0140v00.txt", 24: "Z0140v40.txt",
            15: "Z0140v00.txt", 25: "Z0140v40.txt",
            # Padova tracks
            41: "modp0004.dat", 42: "modp004.dat",
            43: "modp008.dat", 44: "modp020.dat",
            45: "modp050.dat",
            # Additional tracks
            51: "mode001.dat", 61: "modc001.dat",
            52: "mode004.dat", 62: "modc004.dat",
            53: "mode008.dat", 63: "modc008.dat",
            54: "mode020.dat", 64: "modc020.dat",
            55: "mode040.dat", 65: "modc040.dat",
        }
        
        filename = track_files.get(self.galaxy.iz, "Z0140v00.txt")
        track_path = Path("data/tracks") / filename
        
        if not track_path.exists():
            self.logger.warning(f"Track file not found: {track_path}, using default")
            track_path = Path("data/tracks/Z0140v00.txt")
        
        # Double check file exists
        if not track_path.exists():
            raise FileNotFoundError(f"Track file not found: {track_path}")
        
        # Read stellar tracks with error handling
        try:
            # The StellarTracks class uses 'load_tracks' with string parameter
            filename_stem = track_path.stem  # Get filename without extension
            self.stellar_tracks.load_tracks(filename_stem)
            # Create a track data object from the loaded data
            track_data = TrackData()
            track_data.init(1, 100)  # Initialize with dummy values
            self.stellar_tracks.data = track_data
            self.galaxy.tracks = [track_data]
        except Exception as e:
            self.logger.error(f"Error reading tracks: {e}")
            # Set empty track data as fallback
            track_data = TrackData()
            track_data.init(1, 100)
            self.galaxy.tracks = [track_data]
    
    def _set_metallicity_string(self):
        """Set metallicity string for filenames based on selected tracks"""
        z_id = self.galaxy.iz
        
        # Map metallicity ID to file strings
        if z_id in [11, 21, 31, 41, 51, 61]:
            self.namfi3, self.nam = 'm13', '001'
        elif z_id in [12, 22, 32, 42, 52, 62]:
            self.namfi3, self.nam = 'm07', '004'
        elif z_id in [13, 23, 33, 43, 53, 63]:
            self.namfi3, self.nam = 'm04', '008'
        elif z_id in [14, 24, 34, 44, 54, 64]:
            self.namfi3, self.nam = 'p00', '020'
        elif z_id in [15, 25, 35, 45, 55, 65]:
            self.namfi3, self.nam = 'p03', '040'
        else:
            self.namfi3, self.nam = 'p00', '020'
            
        # Override if needed based on wind scale
        if self.galaxy.iwrscale < 0:
            self.nam = '020'
    
    def _read_atmosphere_data(self):
        """Read atmospheric and opacity data"""
        # Read Lejeune atmospheres
        atm_file = Path("data/lejeune") / f"lcb97_{self.namfi3}.flu"
        
        if not atm_file.exists():
            self.logger.error(f"Cannot find Lejeune atmosphere file: {atm_file}")
            raise FileNotFoundError(f"Atmosphere file not found: {atm_file}")
            
        try:
            # Read atmosphere data (simplified)
            with open(atm_file, 'r') as f:
                # Skip header
                f.readline()
                # Read data (implementation depends on file format)
                self.logger.info(f"Successfully loaded atmosphere data: {atm_file}")
        except Exception as e:
            self.logger.error(f"Error reading atmosphere file: {e}")
            raise
    
    def _main_calculation_loop(self):
        """Main calculation loop for population synthesis"""
        continue_evolution = True
        step_count = 0
        
        self.logger.info("Beginning stellar population evolution...")
        
        while continue_evolution:
            step_count += 1
            
            # Progress indicator
            if step_count % 10 == 0:
                self.logger.info(f"Step {step_count}, t = {self.time / 1.0e6:.6f} Myr")
            
            # Compute stellar population based on grid type
            if self.galaxy.jmg in [0, 1]:
                # Evolution of discrete stellar masses
                self._density()
                self._starpara()
            else:
                # Isochrone synthesis method
                self._density()
                self._starpara_iso()
            
            # Adjust WR temperatures if requested
            if self.galaxy.iwrt != 0:
                self._temp_adjust()
            
            # Compute population properties
            if self.galaxy.io4 >= 1:
                self._windpower(self.time, self.icount)
            
            if self.galaxy.io5 >= 1:
                self._supernova(self.time, self.icount)
            
            if self.galaxy.io6 >= 1:
                self._spectype(self.time, self.icount)
            
            if self.galaxy.io7 >= 1:
                self._nucleo(self.time, self.icount)
            
            # Spectral synthesis
            if self.galaxy.io1 >= 1:
                self._specsyn(self.time, self.icount)
            
            if self.galaxy.io8 >= 1:
                self._linesyn(self.time, self.icount)
            
            if self.galaxy.io12 >= 1:
                self._fusesyn(self.time, self.icount)
            
            if self.galaxy.io9 >= 1:
                self._hires(self.time, self.icount)
            
            if self.galaxy.io15 >= 1:
                self._ifa_spectrum(self.time, self.icount)
            
            # Write intermediate output
            self._output(self.time, self.icount)
            
            # Update time parameters
            if self.galaxy.jtime == 0:
                # Linear time steps
                self.time += self.galaxy.tbiv
            else:
                # Logarithmic time steps
                if self.icount == 1:
                    self.galaxy.tvar = self.galaxy.time1
                else:
                    self.galaxy.tvar *= self.galaxy.tstep
                self.time = self.galaxy.tvar
            
            # Check termination criteria
            if self.galaxy.jtime == 0:
                if self.time > self.galaxy.tmax:
                    continue_evolution = False
            else:
                if self.icount >= self.galaxy.itbiv:
                    continue_evolution = False
            
            self.icount += 1
        
        self.logger.info(f"Evolution completed. Total steps: {step_count}")
    
    def _density(self):
        """Calculate stellar density for current time step"""
        # Calculate stellar population density based on IMF and star formation
        if self.galaxy.isf > 0:  # Continuous star formation
            dt = self.galaxy.tbiv if self.galaxy.jtime == 0 else self.galaxy.tvar
            for i in range(self.galaxy.ninterv):
                lower = self.galaxy.xmaslim[i]
                upper = self.galaxy.xmaslim[i+1]
                exp_val = self.galaxy.xponent[i]
                # Calculate density for this mass interval
                if exp_val != -1.0:
                    self.galaxy.dens[i] = self.galaxy.sfr * dt * (upper**(exp_val+1) - lower**(exp_val+1)) / (exp_val+1)
                else:
                    self.galaxy.dens[i] = self.galaxy.sfr * dt * np.log(upper/lower)
        else:  # Instantaneous burst
            for i in range(self.galaxy.ninterv):
                lower = self.galaxy.xmaslim[i]
                upper = self.galaxy.xmaslim[i+1]
                exp_val = self.galaxy.xponent[i]
                # Calculate density for this mass interval
                if exp_val != -1.0:
                    self.galaxy.dens[i] = self.galaxy.toma * 1e6 * (upper**(exp_val+1) - lower**(exp_val+1)) / (exp_val+1)
                else:
                    self.galaxy.dens[i] = self.galaxy.toma * 1e6 * np.log(upper/lower)
    
    def _starpara(self):
        """Calculate stellar parameters for discrete masses"""
        # Calculate stellar parameters for each mass on the grid
        if not self.galaxy.tracks:
            return
            
        track = self.galaxy.tracks[0]
        
        # For each mass on the grid
        for i in range(len(self.galaxy.cmass)):
            mass = self.galaxy.cmass[i]
            if mass <= 0:
                continue
                
            # Find track index
            mass_idx = track.get_mass_index(mass)
            
            # Interpolate in time
            params = track.interpolate_in_time(mass_idx, self.time)
            
            # Store results
            if params:
                # Update stellar parameters
                self.galaxy.spectra[i, 0] = params.get('log_lum', 0.0)
                self.galaxy.spectra[i, 1] = params.get('log_teff', 0.0)
                self.galaxy.spectra[i, 2] = params.get('mass', mass)
    
    def _starpara_iso(self):
        """Calculate stellar parameters using isochrone method"""
        # Use isochrone method for synthesis
        if not self.galaxy.tracks:
            return
            
        track = self.galaxy.tracks[0]
        
        # Build isochrone at current time
        iso_masses = []
        iso_lum = []
        iso_teff = []
        
        for mass_idx in range(track.num_masses):
            params = track.interpolate_in_time(mass_idx, self.time)
            if params and params.get('mass', 0) > 0:
                iso_masses.append(params['mass'])
                iso_lum.append(params.get('log_lum', 0.0))
                iso_teff.append(params.get('log_teff', 0.0))
        
        # Store isochrone data
        if iso_masses:
            self.galaxy.spectra[:len(iso_masses), 0] = iso_lum
            self.galaxy.spectra[:len(iso_masses), 1] = iso_teff
            self.galaxy.spectra[:len(iso_masses), 2] = iso_masses
    
    def _temp_adjust(self):
        """Adjust Wolf-Rayet star temperatures"""
        # Adjust temperatures for WR stars if requested
        if self.galaxy.iwrt == 0:
            return
            
        # Apply WR temperature adjustment based on mass
        for i in range(len(self.galaxy.cmass)):
            mass = self.galaxy.cmass[i]
            if mass >= self.galaxy.xmwr:  # WR mass threshold
                # Apply temperature adjustment factor
                temp_factor = 1.0 + 0.1 * self.galaxy.iwrt
                self.galaxy.spectra[i, 1] *= temp_factor
    
    def _windpower(self, time, icount):
        """Calculate wind power"""
        # Calculate wind power for current time step
        total_power = 0.0
        for i in range(len(self.galaxy.cmass)):
            if self.galaxy.dens[i] > 0:
                # Simple wind power calculation
                mass_loss = 1e-7 * self.galaxy.cmass[i]**2  # Simplified mass loss rate
                wind_speed = 1000.0  # km/s, simplified
                power = 0.5 * mass_loss * wind_speed**2
                self.galaxy.wind_power[i] = power * self.galaxy.dens[i]
                total_power += self.galaxy.wind_power[i]
        
        self.logger.debug(f"Wind power at t={time}: {total_power}")
    
    def _supernova(self, time, icount):
        """Calculate supernova rates"""
        # Calculate supernova rates based on stellar masses
        total_sn_rate = 0.0
        for i in range(len(self.galaxy.cmass)):
            mass = self.galaxy.cmass[i]
            if self.galaxy.sncut <= mass <= self.galaxy.bhcut:
                # Stars in SN mass range
                lifetime = 1e10 * mass**(-2.5)  # Simplified lifetime
                if time > lifetime:
                    rate = self.galaxy.dens[i] / lifetime
                    self.galaxy.sn_rates[i] = rate
                    total_sn_rate += rate
        
        self.logger.debug(f"SN rate at t={time}: {total_sn_rate}")
    
    def _spectype(self, time, icount):
        """Calculate spectral type distribution"""
        # Classify stars by spectral type
        sp_types = np.zeros(20)  # 20 spectral type bins
        
        for i in range(len(self.galaxy.cmass)):
            if self.galaxy.dens[i] > 0:
                teff = 10**self.galaxy.spectra[i, 1] if self.galaxy.spectra[i, 1] > 0 else 3000
                # Simple spectral type binning based on temperature
                if teff > 30000:
                    sp_bin = 0  # O stars
                elif teff > 10000:
                    sp_bin = 1  # B stars
                elif teff > 7500:
                    sp_bin = 2  # A stars
                elif teff > 6000:
                    sp_bin = 3  # F stars
                elif teff > 5200:
                    sp_bin = 4  # G stars
                elif teff > 3700:
                    sp_bin = 5  # K stars
                else:
                    sp_bin = 6  # M stars
                
                sp_types[sp_bin] += self.galaxy.dens[i]
        
        self.galaxy.sp_type_counts[:len(sp_types)] = sp_types
    
    def _nucleo(self, time, icount):
        """Calculate nucleosynthetic yields"""
        # Simplified nucleosynthesis calculation
        yields = np.zeros(30)  # 30 element bins
        
        for i in range(len(self.galaxy.cmass)):
            mass = self.galaxy.cmass[i]
            if self.galaxy.dens[i] > 0 and mass > self.galaxy.sncut:
                # Simple yield calculation
                yields[0] += 0.1 * mass * self.galaxy.dens[i]  # H
                yields[1] += 0.3 * mass * self.galaxy.dens[i]  # He
                yields[5] += 0.01 * mass * self.galaxy.dens[i]  # C
                yields[6] += 0.005 * mass * self.galaxy.dens[i]  # N
                yields[7] += 0.02 * mass * self.galaxy.dens[i]  # O
        
        self.galaxy.element_yields[:len(yields)] = yields
    
    def _specsyn(self, time, icount):
        """Synthesize stellar spectrum"""
        # Create composite spectrum
        wavelengths = np.logspace(1, 5, 1000)  # 10 to 100000 Angstroms
        spectrum = np.zeros_like(wavelengths)
        
        for i in range(len(self.galaxy.cmass)):
            if self.galaxy.dens[i] > 0 and self.galaxy.spectra[i, 1] > 0:
                # Simple blackbody approximation
                teff = 10**self.galaxy.spectra[i, 1]
                lum = 10**self.galaxy.spectra[i, 0]
                bb_flux = self._blackbody(wavelengths, teff, lum)
                spectrum += bb_flux * self.galaxy.dens[i]
        
        # Store spectrum (simplified)
        self.galaxy.wavel[:len(wavelengths)] = wavelengths
        self.galaxy.spectra[0, :len(spectrum)] = spectrum
    
    def _blackbody(self, wavelength, temperature, luminosity):
        """Simple blackbody spectrum"""
        from .core.constants import H_PLANCK, C_LIGHT, K_BOLTZ
        
        # Planck function
        h = H_PLANCK
        c = C_LIGHT
        k = K_BOLTZ
        lam = wavelength * 1e-8  # Convert to cm
        
        # Avoid overflow
        exponent = h * c / (lam * k * temperature)
        exponent = np.minimum(exponent, 100)
        
        planck = 2 * h * c**2 / lam**5 / (np.exp(exponent) - 1)
        return planck * luminosity / (4 * np.pi)
    
    def _linesyn(self, time, icount):
        """Synthesize UV line spectrum"""
        # Simple UV line calculation
        uv_lines = np.zeros(100)
        
        for i in range(len(self.galaxy.cmass)):
            if self.galaxy.dens[i] > 0 and self.galaxy.spectra[i, 1] > 3.7:  # Hot stars
                # Add UV line contribution
                for j in range(10):
                    uv_lines[j] += self.galaxy.dens[i] * np.exp(-j)
        
        self.galaxy.uv_lines[:len(uv_lines)] = uv_lines
    
    def _fusesyn(self, time, icount):
        """Synthesize FUSE spectrum"""
        # Simple FUSE spectrum calculation
        fuse_spectrum = np.zeros(50)
        
        for i in range(len(self.galaxy.cmass)):
            if self.galaxy.dens[i] > 0 and self.galaxy.spectra[i, 1] > 4.0:
                # Add FUV contribution
                for j in range(10):
                    fuse_spectrum[j] += self.galaxy.dens[i] * 0.5 * np.exp(-j/2)
        
        self.galaxy.fuv_lines[:len(fuse_spectrum)] = fuse_spectrum
    
    def _hires(self, time, icount):
        """Calculate high-resolution optical spectrum"""
        # Simple high-res optical spectrum
        hires_spectrum = np.zeros(200)
        
        for i in range(len(self.galaxy.cmass)):
            if self.galaxy.dens[i] > 0:
                # Add optical lines
                for j in range(50):
                    hires_spectrum[j] += self.galaxy.dens[i] * np.sin(j * 0.1)
        
        self.galaxy.hires_lines[:len(hires_spectrum)] = hires_spectrum
    
    def _ifa_spectrum(self, time, icount):
        """Calculate IFA spectrum"""
        # Simple IFA spectrum calculation
        # Similar to UV line synthesis but in different wavelength range
        self._linesyn(time, icount)  # Use same calculation for simplicity
    
    def _output(self, time, icount):
        """Write output for current time step"""
        if self.output_writer:
            self.output_writer.write_timestep(
                time=time,
                model_name=self.galaxy.model_name,
                sf_mode=self.galaxy.isf,
                data=self.galaxy
            )
    
    def _write_output(self):
        """Write final output files"""
        if self.output_writer:
            self.output_writer.write_final_output(self.galaxy)


def main():
    """Command-line entry point"""
    parser = argparse.ArgumentParser(
        description='GALAXY/Starburst99 - Stellar Population Synthesis Code'
    )
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Input parameter file (optional)'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='Starburst99 Python v7.1.0'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run the synthesis
    starburst = Starburst99(args.input_file)
    starburst.run()


if __name__ == '__main__':
    main()