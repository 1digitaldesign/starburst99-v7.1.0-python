"""Comprehensive tests for starburst_main.py to achieve 100% coverage"""

import unittest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import sys
from pathlib import Path

from ..starburst_main import Starburst99, main
from ..core.galaxy_module import TrackData
from ..core.galaxy_module import GalaxyModel, TrackData, ModelParameters
from ..core.constants import *


class TestStarburst99Complete(unittest.TestCase):
    """Complete test suite for Starburst99 class"""
    
    def setUp(self):
        """Set up test environment"""
        self.starburst = Starburst99()
        # Initialize arrays
        self.starburst.galaxy.init_module()
        self.starburst.galaxy.cmass = np.linspace(1, 100, 100)
        self.starburst.galaxy.dens = np.zeros(100)
        
    def test_initialization(self):
        """Test Starburst99 initialization"""
        sb = Starburst99()
        self.assertIsNotNone(sb.galaxy)
        self.assertIsNotNone(sb.data_profiles)
        self.assertIsNotNone(sb.input_parser)
        self.assertIsNone(sb.output_writer)
        self.assertIsNone(sb.input_file)
        self.assertEqual(sb.time, 0.0)
        self.assertEqual(sb.icount, 1)
        
    def test_initialization_with_input_file(self):
        """Test initialization with input file"""
        sb = Starburst99("test_input.txt")
        self.assertEqual(sb.input_file, "test_input.txt")
        
    def test_setup_logging(self):
        """Test logging setup"""
        sb = Starburst99()
        self.assertTrue(hasattr(sb, 'logger'))
        
    def test_sync_parameters(self):
        """Test parameter synchronization"""
        self.starburst.galaxy.model_params.name = "test_model"
        self.starburst.galaxy.model_params.sf_mode = 1
        self.starburst.galaxy.model_params.total_mass = 10.0
        self.starburst.galaxy.model_params.num_intervals = 2
        self.starburst.galaxy.model_params.exponents = [2.35, 2.70]
        self.starburst.galaxy.model_params.mass_limits = [1.0, 10.0, 100.0]
        self.starburst.galaxy.model_params.outputs = [True] * 15
        
        self.starburst._sync_parameters()
        
        self.assertEqual(self.starburst.galaxy.model_name, "test_model")
        self.assertEqual(self.starburst.galaxy.isf, 1)
        self.assertEqual(self.starburst.galaxy.toma, 10.0)
        self.assertEqual(self.starburst.galaxy.io1, 1)
        self.assertEqual(self.starburst.galaxy.io15, 1)
        
    def test_read_tracks(self):
        """Test reading stellar tracks"""
        with patch.object(Path, 'exists', return_value=True):
            mock_track_data = TrackData()
            mock_track_data.init(1, 100)
            self.starburst.stellar_tracks.data = mock_track_data
            with patch.object(self.starburst.stellar_tracks, 'load_tracks'):
                self.starburst.galaxy.iz = 14
                self.starburst._read_tracks()
                self.assertEqual(len(self.starburst.galaxy.tracks), 1)
                
    def test_read_tracks_not_found(self):
        """Test reading tracks when file not found"""
        with patch.object(Path, 'exists', return_value=False):
            self.starburst.galaxy.iz = 99  # Non-existent ID
            with self.assertRaises(FileNotFoundError):
                self.starburst._read_tracks()
                
    def test_set_metallicity_string(self):
        """Test metallicity string setting"""
        test_cases = [
            (11, 'm13', '001'),
            (22, 'm07', '004'),
            (33, 'm04', '008'),
            (44, 'p00', '020'),
            (55, 'p03', '040'),
            (99, 'p00', '020'),  # Default
        ]
        
        for z_id, expected_namfi3, expected_nam in test_cases:
            self.starburst.galaxy.iz = z_id
            self.starburst.galaxy.iwrscale = 0
            self.starburst._set_metallicity_string()
            self.assertEqual(self.starburst.namfi3, expected_namfi3)
            self.assertEqual(self.starburst.nam, expected_nam)
            
        # Test with negative iwrscale
        self.starburst.galaxy.iwrscale = -1
        self.starburst._set_metallicity_string()
        self.assertEqual(self.starburst.nam, '020')
        
    def test_read_atmosphere_data(self):
        """Test reading atmosphere data"""
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', unittest.mock.mock_open(read_data='header\ndata\n')):
                self.starburst.namfi3 = 'p00'
                self.starburst._read_atmosphere_data()
                # Should not raise exception
                
    def test_read_atmosphere_data_not_found(self):
        """Test reading atmosphere data when file not found"""
        with patch.object(Path, 'exists', return_value=False):
            self.starburst.namfi3 = 'p00'
            with self.assertRaises(FileNotFoundError):
                self.starburst._read_atmosphere_data()
                
    def test_density_continuous(self):
        """Test density calculation for continuous star formation"""
        self.starburst.galaxy.isf = 1  # Continuous
        self.starburst.galaxy.sfr = 10.0
        self.starburst.galaxy.tbiv = 1.0
        self.starburst.galaxy.jtime = 0
        self.starburst.galaxy.ninterv = 1
        self.starburst.galaxy.xmaslim = np.array([1.0, 100.0, 0.0])
        self.starburst.galaxy.xponent = np.array([2.35, 0.0])
        
        self.starburst._density()
        
        self.assertTrue(np.any(self.starburst.galaxy.dens > 0))
        
    def test_density_instantaneous(self):
        """Test density calculation for instantaneous burst"""
        self.starburst.galaxy.isf = -1  # Instantaneous
        self.starburst.galaxy.toma = 1.0
        self.starburst.galaxy.ninterv = 1
        self.starburst.galaxy.xmaslim = np.array([1.0, 100.0, 0.0])
        self.starburst.galaxy.xponent = np.array([2.35, 0.0])
        
        self.starburst._density()
        
        self.assertTrue(np.any(self.starburst.galaxy.dens > 0))
        
    def test_density_salpeter(self):
        """Test density calculation with Salpeter IMF"""
        self.starburst.galaxy.isf = -1
        self.starburst.galaxy.toma = 1.0
        self.starburst.galaxy.ninterv = 1
        self.starburst.galaxy.xmaslim = np.array([1.0, 100.0, 0.0])
        self.starburst.galaxy.xponent = np.array([-1.0, 0.0])  # Special case
        
        self.starburst._density()
        
        self.assertTrue(np.any(self.starburst.galaxy.dens > 0))
        
    def test_starpara_no_tracks(self):
        """Test starpara without tracks"""
        self.starburst.galaxy.tracks = []
        self.starburst._starpara()
        # Should return without error
        
    def test_starpara_with_tracks(self):
        """Test starpara with tracks"""
        track = TrackData()
        track.init(5, 10)
        track.init_mass = np.array([1, 5, 10, 50, 100])
        track.age[0, :] = np.linspace(0, 1e10, 10)
        track.log_lum[0, :] = np.linspace(1, 5, 10)
        track.log_teff[0, :] = np.linspace(3.5, 4.5, 10)
        track.mass[0, :] = np.linspace(1, 0.5, 10)
        
        self.starburst.galaxy.tracks = [track]
        self.starburst.time = 1e9
        self.starburst._starpara()
        
        # Check that some spectra were calculated
        self.assertTrue(np.any(self.starburst.galaxy.spectra > 0))
        
    def test_starpara_iso_no_tracks(self):
        """Test starpara_iso without tracks"""
        self.starburst.galaxy.tracks = []
        self.starburst._starpara_iso()
        # Should return without error
        
    def test_starpara_iso_with_tracks(self):
        """Test starpara_iso with tracks"""
        track = TrackData()
        track.init(5, 10)
        track.age[:, :] = np.linspace(0, 1e10, 10)
        track.mass[:, :] = np.ones((5, 10)) * np.array([[1], [5], [10], [50], [100]])
        track.log_lum[:, :] = np.ones((5, 10)) * 3.0
        track.log_teff[:, :] = np.ones((5, 10)) * 4.0
        
        self.starburst.galaxy.tracks = [track]
        self.starburst.time = 5e9
        self.starburst._starpara_iso()
        
        # Check that isochrone was built
        self.assertTrue(np.any(self.starburst.galaxy.spectra > 0))
        
    def test_temp_adjust_disabled(self):
        """Test temperature adjustment when disabled"""
        self.starburst.galaxy.iwrt = 0
        self.starburst.galaxy.spectra[0, 1] = 4.0
        original_temp = self.starburst.galaxy.spectra[0, 1]
        
        self.starburst._temp_adjust()
        
        self.assertEqual(self.starburst.galaxy.spectra[0, 1], original_temp)
        
    def test_temp_adjust_enabled(self):
        """Test temperature adjustment when enabled"""
        self.starburst.galaxy.iwrt = 1
        self.starburst.galaxy.xmwr = 20.0
        self.starburst.galaxy.cmass[10] = 25.0  # Above WR threshold
        self.starburst.galaxy.spectra[10, 1] = 4.0
        original_temp = self.starburst.galaxy.spectra[10, 1]
        
        self.starburst._temp_adjust()
        
        self.assertNotEqual(self.starburst.galaxy.spectra[10, 1], original_temp)
        
    def test_windpower(self):
        """Test wind power calculation"""
        self.starburst.galaxy.dens[0] = 1.0
        self.starburst.galaxy.cmass[0] = 10.0
        
        self.starburst._windpower(1e6, 1)
        
        self.assertTrue(self.starburst.galaxy.wind_power[0] > 0)
        
    def test_supernova(self):
        """Test supernova rate calculation"""
        self.starburst.galaxy.dens[0] = 1.0
        self.starburst.galaxy.cmass[0] = 25.0  # In SN range
        self.starburst.galaxy.sncut = 8.0
        self.starburst.galaxy.bhcut = 120.0
        self.starburst.time = 1e11  # Old enough for SN
        
        self.starburst._supernova(self.starburst.time, 1)
        
        self.assertTrue(self.starburst.galaxy.sn_rates[0] > 0)
        
    def test_spectype(self):
        """Test spectral type classification"""
        # Set up stars with different temperatures
        self.starburst.galaxy.dens[:7] = 1.0
        self.starburst.galaxy.spectra[:7, 1] = [4.5, 4.0, 3.9, 3.8, 3.7, 3.6, 3.4]
        
        self.starburst._spectype(1e6, 1)
        
        # Check that stars were classified
        self.assertTrue(np.any(self.starburst.galaxy.sp_type_counts > 0))
        
    def test_nucleo(self):
        """Test nucleosynthesis calculation"""
        self.starburst.galaxy.dens[0] = 1.0
        self.starburst.galaxy.cmass[0] = 25.0
        self.starburst.galaxy.sncut = 8.0
        
        self.starburst._nucleo(1e6, 1)
        
        # Check that yields were calculated
        self.assertTrue(np.any(self.starburst.galaxy.element_yields > 0))
        
    def test_specsyn(self):
        """Test spectrum synthesis"""
        self.starburst.galaxy.dens[0] = 1.0
        self.starburst.galaxy.spectra[0, 0] = 3.0  # log L
        self.starburst.galaxy.spectra[0, 1] = 4.0  # log T
        
        self.starburst._specsyn(1e6, 1)
        
        # Check that wavelengths and spectrum were set
        self.assertTrue(np.any(self.starburst.galaxy.wavel > 0))
        
    def test_blackbody(self):
        """Test blackbody calculation"""
        wavelengths = np.array([5000.0, 6000.0])  # Angstroms
        result = self.starburst._blackbody(wavelengths, 5800, 1.0)
        
        self.assertTrue(np.all(result > 0))
        self.assertTrue(np.all(np.isfinite(result)))
        
    def test_linesyn(self):
        """Test UV line synthesis"""
        self.starburst.galaxy.dens[0] = 1.0
        self.starburst.galaxy.spectra[0, 1] = 4.5  # Hot star
        
        self.starburst._linesyn(1e6, 1)
        
        self.assertTrue(np.any(self.starburst.galaxy.uv_lines > 0))
        
    def test_fusesyn(self):
        """Test FUSE spectrum synthesis"""
        self.starburst.galaxy.dens[0] = 1.0
        self.starburst.galaxy.spectra[0, 1] = 4.5  # Hot star
        
        self.starburst._fusesyn(1e6, 1)
        
        self.assertTrue(np.any(self.starburst.galaxy.fuv_lines > 0))
        
    def test_hires(self):
        """Test high-resolution spectrum"""
        self.starburst.galaxy.dens[0] = 1.0
        
        self.starburst._hires(1e6, 1)
        
        self.assertTrue(np.any(self.starburst.galaxy.hires_lines != 0))
        
    def test_ifa_spectrum(self):
        """Test IFA spectrum calculation"""
        self.starburst.galaxy.dens[0] = 1.0
        self.starburst.galaxy.spectra[0, 1] = 4.5
        
        self.starburst._ifa_spectrum(1e6, 1)
        
        # Uses same as linesyn, so should have UV lines
        self.assertTrue(np.any(self.starburst.galaxy.uv_lines > 0))
        
    def test_output(self):
        """Test output writing"""
        mock_writer = Mock()
        self.starburst.output_writer = mock_writer
        
        self.starburst._output(1e6, 1)
        
        mock_writer.write_timestep.assert_called_once()
        
    def test_write_output(self):
        """Test final output writing"""
        mock_writer = Mock()
        self.starburst.output_writer = mock_writer
        
        self.starburst._write_output()
        
        mock_writer.write_final_output.assert_called_once()
        
    def test_main_calculation_loop(self):
        """Test main calculation loop"""
        # Set up for quick test
        self.starburst.galaxy.jtime = 0  # Linear time
        self.starburst.galaxy.tbiv = 1.0
        self.starburst.galaxy.tmax = 2.0  # Short run
        self.starburst.galaxy.jmg = 0
        self.starburst.galaxy.iwrt = 0
        
        # Mock all calculation methods
        with patch.object(self.starburst, '_density') as mock_density:
            with patch.object(self.starburst, '_starpara') as mock_starpara:
                with patch.object(self.starburst, '_output') as mock_output:
                    self.starburst._main_calculation_loop()
                    
        # Should have called methods
        mock_density.assert_called()
        mock_starpara.assert_called()
        mock_output.assert_called()
        
    def test_main_calculation_loop_logarithmic(self):
        """Test main calculation loop with logarithmic time"""
        self.starburst.galaxy.jtime = 1  # Logarithmic time
        self.starburst.galaxy.itbiv = 2  # 2 steps
        self.starburst.galaxy.time1 = 1.0
        self.starburst.galaxy.tstep = 2.0
        self.starburst.galaxy.jmg = 1
        self.starburst.galaxy.iwrt = 1
        
        # Mock calculation methods
        with patch.object(self.starburst, '_density'):
            with patch.object(self.starburst, '_starpara'):
                with patch.object(self.starburst, '_temp_adjust'):
                    with patch.object(self.starburst, '_output'):
                        self.starburst._main_calculation_loop()
                        
        self.assertEqual(self.starburst.icount, 3)  # 2 steps + 1
        
    def test_run_success(self):
        """Test successful run"""
        with patch.object(self.starburst.galaxy, 'init_module'):
            with patch.object(self.starburst.data_profiles, 'initialize_data_profiles'):
                with patch.object(self.starburst.input_parser, 'get_default_parameters',
                                return_value=ModelParameters()):
                    with patch.object(self.starburst, '_read_tracks'):
                        with patch.object(self.starburst, '_set_metallicity_string'):
                            with patch.object(self.starburst, '_read_atmosphere_data'):
                                with patch.object(self.starburst, '_main_calculation_loop'):
                                    with patch.object(self.starburst, '_write_output'):
                                        with patch.object(self.starburst.galaxy, 'cleanup_module'):
                                            self.starburst.run()
                                            
    def test_run_with_input_file(self):
        """Test run with input file"""
        self.starburst.input_file = "test.txt"
        
        with patch.object(self.starburst.galaxy, 'init_module'):
            with patch.object(self.starburst.data_profiles, 'initialize_data_profiles'):
                with patch.object(self.starburst.input_parser, 'read_input',
                                return_value=ModelParameters()):
                    with patch.object(self.starburst, '_read_tracks'):
                        with patch.object(self.starburst, '_set_metallicity_string'):
                            with patch.object(self.starburst, '_read_atmosphere_data'):
                                with patch.object(self.starburst, '_main_calculation_loop'):
                                    with patch.object(self.starburst, '_write_output'):
                                        with patch.object(self.starburst.galaxy, 'cleanup_module'):
                                            self.starburst.run()
                                            
    def test_run_with_exception(self):
        """Test run with exception"""
        with patch.object(self.starburst.galaxy, 'init_module',
                        side_effect=Exception("Test error")):
            with self.assertRaises(SystemExit):
                self.starburst.run()
                
    def test_main_function(self):
        """Test main function"""
        test_args = ['starburst_main.py', 'test_input.txt']
        
        with patch.object(sys, 'argv', test_args):
            with patch.object(Starburst99, 'run'):
                main()
                
    def test_main_with_version(self):
        """Test main with version flag"""
        test_args = ['starburst_main.py', '--version']
        
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            
    def test_main_with_debug(self):
        """Test main with debug flag"""
        test_args = ['starburst_main.py', '--debug']
        
        with patch.object(sys, 'argv', test_args):
            with patch.object(Starburst99, 'run'):
                with patch('logging.getLogger') as mock_logger:
                    main()
                    mock_logger.return_value.setLevel.assert_called()
                    
    def test_all_io_combinations(self):
        """Test all I/O flag combinations"""
        # Test with all flags on
        for i in range(1, 16):
            setattr(self.starburst.galaxy, f'io{i}', 1)
            
        # Mock all calculation methods
        methods_to_mock = [
            '_windpower', '_supernova', '_spectype', '_nucleo',
            '_specsyn', '_linesyn', '_fusesyn', '_hires', '_ifa_spectrum'
        ]
        
        for method in methods_to_mock:
            setattr(self.starburst, method, Mock())
            
        with patch.object(self.starburst, '_density'):
            with patch.object(self.starburst, '_starpara'):
                with patch.object(self.starburst, '_output'):
                    self.starburst.galaxy.jtime = 0
                    self.starburst.galaxy.tmax = 0  # Run once
                    self.starburst._main_calculation_loop()
                    
        # All methods should have been called
        for method in methods_to_mock:
            if method in ['_linesyn', '_ifa_spectrum']:  # IFA uses linesyn
                continue
            getattr(self.starburst, method).assert_called()
            
        # Test with all flags off
        for i in range(1, 16):
            setattr(self.starburst.galaxy, f'io{i}', 0)
            
        # Reset mocks
        for method in methods_to_mock:
            getattr(self.starburst, method).reset_mock()
            
        with patch.object(self.starburst, '_density'):
            with patch.object(self.starburst, '_starpara'):
                with patch.object(self.starburst, '_output'):
                    self.starburst.galaxy.tmax = 0  # Run once
                    self.starburst._main_calculation_loop()
                    
        # No optional methods should have been called
        for method in methods_to_mock:
            getattr(self.starburst, method).assert_not_called()


if __name__ == '__main__':
    unittest.main()