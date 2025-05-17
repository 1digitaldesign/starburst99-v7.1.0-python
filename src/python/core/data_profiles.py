"""Data profiles module for spectrum data profile handling"""

import numpy as np
from typing import Optional


class DataProfiles:
    """
    Class containing data structures and routines for handling spectral data
    profiles used in the galaxy/starburst population synthesis code.
    """
    
    def __init__(self):
        """Initialize the DataProfiles class with default values"""
        self.is_initialized = False
        
        # Data arrays
        self.xprof = None
        self.yprof = None
        self.xrange = None
        self.gamma = None
        self.ymass = None
        self.yh = None
        self.yhe = None
        self.yc = None
        self.yn = None
        self.yo = None
        
    def initialize_data_profiles(self):
        """
        Initialize spectral data profiles.
        
        This method sets up the necessary data structures for handling
        spectral profiles in the synthesis calculations.
        """
        # Initialize arrays
        self.xprof = np.zeros((5, 99), dtype=np.float32)
        self.yprof = np.zeros((5, 99), dtype=np.float32)
        self.xrange = np.zeros(50, dtype=np.float32)
        self.gamma = np.zeros(50, dtype=np.float32)
        self.ymass = np.zeros((5, 1), dtype=np.float32)
        self.yh = np.zeros((5, 1), dtype=np.float32)
        self.yhe = np.zeros((5, 1), dtype=np.float32)
        self.yc = np.zeros((5, 1), dtype=np.float32)
        self.yn = np.zeros((5, 1), dtype=np.float32)
        self.yo = np.zeros((5, 1), dtype=np.float32)
        
        # Initialize xprof first 20 values
        self.xprof[0, 0:20] = [
            0.0, 0.5, 1.0, 1.5, 2.0,
            2.5, 3.0, 3.5, 4.0, 4.5,
            5.0, 5.5, 6.0, 6.5, 7.0,
            7.5, 8.0, 8.5, 9.0, 9.5
        ]
        
        # Add values from 21 to 99
        for i in range(20, 99):
            self.xprof[0, i] = 10.0 + 0.5 * (i - 20)
        
        # Initialize yprof first 20 values
        self.yprof[0, 0:20] = [
            0.0, 0.1, 0.2, 0.3, 0.4,
            0.5, 0.6, 0.7, 0.8, 0.9,
            1.0, 1.1, 1.2, 1.3, 1.4,
            1.5, 1.6, 1.7, 1.8, 1.9
        ]
        
        # Add values from 21 to 99
        for i in range(20, 99):
            self.yprof[0, i] = 2.0 + 0.1 * (i - 20)
        
        # Initialize xrange
        self.xrange[0:20] = [
            10.0, 912.0, 913.0, 1300.0, 1500.0,
            1800.0, 2200.0, 2600.0, 3200.0, 3800.0,
            4200.0, 4400.0, 5800.0, 7000.0, 9000.0,
            12000.0, 14000.0, 20000.0, 30000.0, 50000.0
        ]
        
        # Initialize gamma
        self.gamma[0:15] = [
            0.0, 0.0, 2.11e-4, 5.647, 9.35,
            9.847, 10.582, 16.101, 24.681, 41.016,
            66.842, 76.013, 42.095, 9.755, 5.161
        ]
        
        # Initialize abundance arrays
        self.ymass[:, 0] = [15.0, 20.0, 25.0, 40.0, 60.0]
        self.yh[:, 0] = [0.7, 0.6, 0.5, 0.4, 0.3]
        self.yhe[:, 0] = [0.28, 0.38, 0.48, 0.58, 0.68]
        self.yc[:, 0] = [0.001, 0.002, 0.003, 0.004, 0.005]
        self.yn[:, 0] = [0.001, 0.002, 0.003, 0.004, 0.005]
        self.yo[:, 0] = [0.008, 0.007, 0.006, 0.005, 0.004]
        
        self.is_initialized = True
        
    def is_initialized_check(self) -> bool:
        """Check if data profiles have been initialized"""
        return self.is_initialized
    
    def get_profile(self, profile_type: str, index: int = 0) -> Optional[np.ndarray]:
        """
        Get a specific profile array
        
        Args:
            profile_type: Type of profile ('xprof', 'yprof', 'xrange', etc.)
            index: Index for multi-dimensional arrays (default 0)
            
        Returns:
            Profile array if available, None otherwise
        """
        if not self.is_initialized:
            return None
            
        if profile_type == 'xprof':
            return self.xprof[index]
        elif profile_type == 'yprof':
            return self.yprof[index]
        elif profile_type == 'xrange':
            return self.xrange
        elif profile_type == 'gamma':
            return self.gamma
        elif profile_type == 'ymass':
            return self.ymass[:, index]
        elif profile_type == 'yh':
            return self.yh[:, index]
        elif profile_type == 'yhe':
            return self.yhe[:, index]
        elif profile_type == 'yc':
            return self.yc[:, index]
        elif profile_type == 'yn':
            return self.yn[:, index]
        elif profile_type == 'yo':
            return self.yo[:, index]
        else:
            return None