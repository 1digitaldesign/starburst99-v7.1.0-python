"""Tests for the galaxy_module.py"""

import unittest
import numpy as np
from pathlib import Path

from ..core.galaxy_module import GalaxyModel, TrackData, ModelParameters, flin, integer_to_string, exp10, linear_interp
from ..core.constants import *


class TestModelParameters(unittest.TestCase):
    """Test ModelParameters dataclass"""
    
    def test_default_initialization(self):
        """Test default parameter values"""
        params = ModelParameters()
        self.assertEqual(params.name, "default")
        self.assertEqual(params.sf_mode, 0)
        self.assertEqual(params.total_mass, 1.0)
        self.assertEqual(params.sf_rate, 1.0)
        self.assertEqual(params.num_intervals, 1)
        self.assertEqual(params.exponents, [2.35])
        self.assertEqual(params.mass_limits, [1.0, 100.0])
        self.assertEqual(params.sn_cutoff, 8.0)
        self.assertEqual(params.bh_cutoff, 120.0)
        self.assertEqual(len(params.outputs), 15)
        self.assertTrue(all(params.outputs))
    
    def test_custom_initialization(self):
        """Test custom parameter values"""
        params = ModelParameters(
            name="test_model",
            sf_mode=1,
            total_mass=10.0,
            sf_rate=5.0,
            num_intervals=2,
            exponents=[2.35, 2.70],
            mass_limits=[0.1, 10.0, 150.0]
        )
        self.assertEqual(params.name, "test_model")
        self.assertEqual(params.sf_mode, 1)
        self.assertEqual(params.total_mass, 10.0)
        self.assertEqual(params.sf_rate, 5.0)
        self.assertEqual(params.num_intervals, 2)
        self.assertEqual(params.exponents, [2.35, 2.70])
        self.assertEqual(params.mass_limits, [0.1, 10.0, 150.0])


class TestTrackData(unittest.TestCase):
    """Test TrackData class"""
    
    def setUp(self):
        """Set up test data"""
        self.track = TrackData()
    
    def test_initialization(self):
        """Test track data initialization"""
        self.track.init(num_masses=5, num_points=100)
        
        self.assertEqual(self.track.num_masses, 5)
        self.assertEqual(self.track.num_points, 100)
        self.assertEqual(self.track.init_mass.shape, (5,))
        self.assertEqual(self.track.age.shape, (5, 100))
        self.assertEqual(self.track.mass.shape, (5, 100))
        self.assertEqual(self.track.log_lum.shape, (5, 100))
        self.assertEqual(self.track.log_teff.shape, (5, 100))
        self.assertEqual(self.track.h_frac.shape, (5, 100))
    
    def test_cleanup(self):
        """Test track data cleanup"""
        self.track.init(num_masses=5, num_points=100)
        self.track.cleanup()
        
        self.assertIsNone(self.track.init_mass)
        self.assertIsNone(self.track.age)
        self.assertIsNone(self.track.mass)
        self.assertIsNone(self.track.log_lum)
    
    def test_get_mass_index(self):
        """Test finding mass index"""
        self.track.init(num_masses=5, num_points=10)
        self.track.init_mass = np.array([1.0, 5.0, 10.0, 20.0, 50.0])
        
        # Test exact matches
        self.assertEqual(self.track.get_mass_index(1.0), 0)
        self.assertEqual(self.track.get_mass_index(10.0), 2)
        self.assertEqual(self.track.get_mass_index(50.0), 4)
        
        # Test interpolation
        self.assertEqual(self.track.get_mass_index(7.5), 1)  # Closer to 5.0
        self.assertEqual(self.track.get_mass_index(15.0), 2)  # Closer to 10.0
        
        # Test with None init_mass
        track_empty = TrackData()
        self.assertEqual(track_empty.get_mass_index(10.0), -1)
    
    def test_interpolate_in_time(self):
        """Test time interpolation of track data"""
        self.track.init(num_masses=2, num_points=5)
        
        # Set up test data
        self.track.age[0, :] = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        self.track.mass[0, :] = np.array([10.0, 9.5, 9.0, 8.5, 8.0])
        self.track.log_lum[0, :] = np.array([2.0, 2.1, 2.2, 2.3, 2.4])
        
        # Test interpolation at time 1.5
        result = self.track.interpolate_in_time(0, 1.5)
        self.assertAlmostEqual(result['mass'], 9.25)
        self.assertAlmostEqual(result['log_lum'], 2.15)
        
        # Test interpolation at exact point
        result = self.track.interpolate_in_time(0, 2.0)
        self.assertAlmostEqual(result['mass'], 9.0)
        self.assertAlmostEqual(result['log_lum'], 2.2)
        
        # Test edge cases
        result = self.track.interpolate_in_time(0, 0.0)  # Start of range
        self.assertAlmostEqual(result['mass'], 10.0)
        
        result = self.track.interpolate_in_time(0, 5.0)  # End of range (above max)
        # When time > max, it extrapolates between last two points
        self.assertAlmostEqual(result['mass'], 7.5)  # Extrapolated value
        
        # Test with None age
        track_empty = TrackData()
        result = track_empty.interpolate_in_time(0, 1.0)
        self.assertEqual(result, {})
        
        # Test with invalid mass index
        result = self.track.interpolate_in_time(10, 1.0)
        self.assertEqual(result, {})
        
        # Test no time variation (t0 == t1)
        self.track.age[0, :] = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        result = self.track.interpolate_in_time(0, 1.0)
        self.assertAlmostEqual(result['mass'], 10.0)


class TestGalaxyModel(unittest.TestCase):
    """Test GalaxyModel class"""
    
    def setUp(self):
        """Set up test model"""
        self.galaxy = GalaxyModel()
    
    def test_initialization(self):
        """Test galaxy model initialization"""
        self.assertIsInstance(self.galaxy.model_params, ModelParameters)
        self.assertEqual(self.galaxy.model_name, "default")
        self.assertEqual(self.galaxy.isf, 0)
        self.assertEqual(self.galaxy.toma, 1.0)
        self.assertEqual(self.galaxy.sfr, 1.0)
        self.assertEqual(self.galaxy.ninterv, 1)
        self.assertTrue(hasattr(self.galaxy, 'logger'))
    
    def test_init_module(self):
        """Test module initialization"""
        self.galaxy.init_module()
        
        self.assertIsNotNone(self.galaxy.cmass)
        self.assertIsNotNone(self.galaxy.dens)
        self.assertIsNotNone(self.galaxy.wavel)
        self.assertIsNotNone(self.galaxy.spectra)
        self.assertIsNotNone(self.galaxy.wind_power)
        self.assertIsNotNone(self.galaxy.sn_rates)
        
        self.assertEqual(self.galaxy.cmass.shape, (NPGRID,))
        self.assertEqual(self.galaxy.dens.shape, (NPGRID,))
    
    def test_cleanup_module(self):
        """Test module cleanup"""
        self.galaxy.init_module()
        
        # Add some tracks with cleanup method
        track1 = TrackData()
        track1.init(5, 10)
        track2 = TrackData()
        track2.init(3, 8)
        self.galaxy.tracks = [track1, track2]
        
        self.galaxy.cleanup_module()
        
        self.assertIsNone(self.galaxy.cmass)
        self.assertIsNone(self.galaxy.dens)
        self.assertIsNone(self.galaxy.wavel)
        self.assertIsNone(self.galaxy.spectra)
        self.assertEqual(len(self.galaxy.tracks), 0)
    
    def test_open_file(self):
        """Test file opening with error handling"""
        # Test non-existent file
        result = self.galaxy.open_file(10, "nonexistent.txt", status='old')
        self.assertFalse(result)
        
        # Test with Path object
        result = self.galaxy.open_file(10, Path("test.txt"), status='new')
        self.assertTrue(result)
        
        # Test exception handling  
        # Mock a pathlib exception
        import unittest.mock
        with unittest.mock.patch('pathlib.Path.exists', side_effect=Exception("Test exception")):
            result = self.galaxy.open_file(10, "error.txt", status='old')
            self.assertFalse(result)
    
    def test_error_handler(self):
        """Test error handling"""
        # Test non-fatal error
        self.galaxy.error_handler("Test warning", routine="test", fatal=False)
        self.assertIn("WARNING", self.galaxy.error_message)
        
        # Test fatal error
        with self.assertRaises(RuntimeError):
            self.galaxy.error_handler("Test error", routine="test", fatal=True)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_flin(self):
        """Test linear interpolation function"""
        # Test normal interpolation
        result = flin(1.5, 1.0, 2.0, 10.0, 20.0)
        self.assertAlmostEqual(result, 15.0)
        
        # Test edge cases
        result = flin(1.0, 1.0, 2.0, 10.0, 20.0)
        self.assertAlmostEqual(result, 10.0)
        
        result = flin(2.0, 1.0, 2.0, 10.0, 20.0)
        self.assertAlmostEqual(result, 20.0)
        
        # Test division by zero protection
        result = flin(1.5, 1.0, 1.0, 10.0, 20.0)
        self.assertAlmostEqual(result, 10.0)
    
    def test_integer_to_string(self):
        """Test integer to string conversion"""
        self.assertEqual(integer_to_string(123), "123")
        self.assertEqual(integer_to_string(-456), "-456")
        self.assertEqual(integer_to_string(0), "0")
    
    def test_exp10(self):
        """Test exp10 function"""
        self.assertAlmostEqual(exp10(0), 1.0)
        self.assertAlmostEqual(exp10(1), 10.0)
        self.assertAlmostEqual(exp10(2), 100.0)
        self.assertAlmostEqual(exp10(-1), 0.1)
        
        # Test with numpy array
        arr = np.array([0, 1, 2])
        result = exp10(arr)
        np.testing.assert_array_almost_equal(result, [1.0, 10.0, 100.0])
    
    def test_linear_interp(self):
        """Test linear interpolation function"""
        x_arr = np.array([0.0, 1.0, 2.0, 3.0])
        y_arr = np.array([0.0, 2.0, 4.0, 6.0])
        
        # Test interpolation
        self.assertAlmostEqual(linear_interp(0.5, x_arr, y_arr), 1.0)
        self.assertAlmostEqual(linear_interp(1.5, x_arr, y_arr), 3.0)
        self.assertAlmostEqual(linear_interp(2.5, x_arr, y_arr), 5.0)
        
        # Test edge cases
        self.assertAlmostEqual(linear_interp(-1.0, x_arr, y_arr), 0.0)  # Below range
        self.assertAlmostEqual(linear_interp(4.0, x_arr, y_arr), 6.0)   # Above range


if __name__ == '__main__':
    unittest.main()