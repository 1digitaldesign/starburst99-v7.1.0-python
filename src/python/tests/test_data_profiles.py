"""Tests for the data_profiles.py module"""

import unittest
import numpy as np

from ..core.data_profiles import DataProfiles


class TestDataProfiles(unittest.TestCase):
    """Test DataProfiles class"""
    
    def setUp(self):
        """Set up test data"""
        self.profiles = DataProfiles()
    
    def test_initialization(self):
        """Test DataProfiles initialization"""
        self.assertFalse(self.profiles.is_initialized)
        self.assertIsNone(self.profiles.xprof)
        self.assertIsNone(self.profiles.yprof)
        self.assertIsNone(self.profiles.xrange)
        self.assertIsNone(self.profiles.gamma)
        self.assertIsNone(self.profiles.ymass)
        self.assertIsNone(self.profiles.yh)
        self.assertIsNone(self.profiles.yhe)
        self.assertIsNone(self.profiles.yc)
        self.assertIsNone(self.profiles.yn)
        self.assertIsNone(self.profiles.yo)
    
    def test_initialize_data_profiles(self):
        """Test data profiles initialization"""
        self.profiles.initialize_data_profiles()
        
        self.assertTrue(self.profiles.is_initialized)
        
        # Check array shapes
        self.assertEqual(self.profiles.xprof.shape, (5, 99))
        self.assertEqual(self.profiles.yprof.shape, (5, 99))
        self.assertEqual(self.profiles.xrange.shape, (50,))
        self.assertEqual(self.profiles.gamma.shape, (50,))
        self.assertEqual(self.profiles.ymass.shape, (5, 1))
        self.assertEqual(self.profiles.yh.shape, (5, 1))
        self.assertEqual(self.profiles.yhe.shape, (5, 1))
        self.assertEqual(self.profiles.yc.shape, (5, 1))
        self.assertEqual(self.profiles.yn.shape, (5, 1))
        self.assertEqual(self.profiles.yo.shape, (5, 1))
        
        # Check first few values of xprof
        expected_xprof_start = [0.0, 0.5, 1.0, 1.5, 2.0]
        np.testing.assert_array_almost_equal(
            self.profiles.xprof[0, :5], expected_xprof_start
        )
        
        # Check first few values of yprof
        expected_yprof_start = [0.0, 0.1, 0.2, 0.3, 0.4]
        np.testing.assert_array_almost_equal(
            self.profiles.yprof[0, :5], expected_yprof_start
        )
        
        # Check values in extended range
        self.assertAlmostEqual(self.profiles.xprof[0, 20], 10.0)
        self.assertAlmostEqual(self.profiles.xprof[0, 21], 10.5)
        self.assertAlmostEqual(self.profiles.yprof[0, 20], 2.0)
        self.assertAlmostEqual(self.profiles.yprof[0, 21], 2.1, places=6)
        
        # Check xrange values
        expected_xrange_start = [10.0, 912.0, 913.0, 1300.0, 1500.0]
        np.testing.assert_array_almost_equal(
            self.profiles.xrange[:5], expected_xrange_start
        )
        
        # Check gamma values
        expected_gamma_start = [0.0, 0.0, 2.11e-4, 5.647, 9.35]
        np.testing.assert_array_almost_equal(
            self.profiles.gamma[:5], expected_gamma_start
        )
        
        # Check abundance arrays
        expected_ymass = [15.0, 20.0, 25.0, 40.0, 60.0]
        np.testing.assert_array_almost_equal(
            self.profiles.ymass[:, 0], expected_ymass
        )
        
        expected_yh = [0.7, 0.6, 0.5, 0.4, 0.3]
        np.testing.assert_array_almost_equal(
            self.profiles.yh[:, 0], expected_yh
        )
        
        expected_yhe = [0.28, 0.38, 0.48, 0.58, 0.68]
        np.testing.assert_array_almost_equal(
            self.profiles.yhe[:, 0], expected_yhe
        )
    
    def test_is_initialized_check(self):
        """Test is_initialized_check method"""
        self.assertFalse(self.profiles.is_initialized_check())
        
        self.profiles.initialize_data_profiles()
        self.assertTrue(self.profiles.is_initialized_check())
    
    def test_get_profile(self):
        """Test get_profile method"""
        # Before initialization
        self.assertIsNone(self.profiles.get_profile('xprof'))
        self.assertIsNone(self.profiles.get_profile('yprof'))
        
        # After initialization
        self.profiles.initialize_data_profiles()
        
        # Test getting 1D profiles
        xrange_profile = self.profiles.get_profile('xrange')
        self.assertIsNotNone(xrange_profile)
        self.assertEqual(xrange_profile.shape, (50,))
        
        gamma_profile = self.profiles.get_profile('gamma')
        self.assertIsNotNone(gamma_profile)
        self.assertEqual(gamma_profile.shape, (50,))
        
        # Test getting 2D profiles with index
        xprof_0 = self.profiles.get_profile('xprof', index=0)
        self.assertIsNotNone(xprof_0)
        self.assertEqual(xprof_0.shape, (99,))
        self.assertEqual(xprof_0[0], 0.0)
        self.assertEqual(xprof_0[1], 0.5)
        
        yprof_0 = self.profiles.get_profile('yprof', index=0)
        self.assertIsNotNone(yprof_0)
        self.assertEqual(yprof_0.shape, (99,))
        self.assertEqual(yprof_0[0], 0.0)
        self.assertEqual(yprof_0[1], 0.1)
        
        # Test getting abundance profiles
        ymass_profile = self.profiles.get_profile('ymass', index=0)
        self.assertIsNotNone(ymass_profile)
        self.assertEqual(ymass_profile.shape, (5,))
        np.testing.assert_array_almost_equal(
            ymass_profile, [15.0, 20.0, 25.0, 40.0, 60.0]
        )
        
        # Test invalid profile type
        invalid_profile = self.profiles.get_profile('invalid_type')
        self.assertIsNone(invalid_profile)
        
        # Test getting abundance profiles with different indices
        ymass_profile_0 = self.profiles.get_profile('ymass', index=0)
        self.assertIsNotNone(ymass_profile_0)
        
        # Test yh
        yh_profile = self.profiles.get_profile('yh', index=0)
        self.assertIsNotNone(yh_profile)
        np.testing.assert_array_almost_equal(
            yh_profile, [0.7, 0.6, 0.5, 0.4, 0.3]
        )
        
        # Test yhe
        yhe_profile = self.profiles.get_profile('yhe', index=0)
        self.assertIsNotNone(yhe_profile)
        np.testing.assert_array_almost_equal(
            yhe_profile, [0.28, 0.38, 0.48, 0.58, 0.68]
        )
        
        # Test yc
        yc_profile = self.profiles.get_profile('yc', index=0)
        self.assertIsNotNone(yc_profile)
        np.testing.assert_array_almost_equal(
            yc_profile, [0.001, 0.002, 0.003, 0.004, 0.005]
        )
        
        # Test yn
        yn_profile = self.profiles.get_profile('yn', index=0)
        self.assertIsNotNone(yn_profile)
        np.testing.assert_array_almost_equal(
            yn_profile, [0.001, 0.002, 0.003, 0.004, 0.005]
        )
        
        # Test yo
        yo_profile = self.profiles.get_profile('yo', index=0)
        self.assertIsNotNone(yo_profile)
        np.testing.assert_array_almost_equal(
            yo_profile, [0.008, 0.007, 0.006, 0.005, 0.004]
        )


if __name__ == '__main__':
    unittest.main()