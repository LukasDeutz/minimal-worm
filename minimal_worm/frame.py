import numpy as np

FRAME_KEYS = [
    't', # Time
    'r', # Centreline coordinates
    'theta', # Euler angles
    'd1', # Director 1
    'd2', # Director 2
    'd3', # Director 3
    'k', # Generalized curvature vector
    'sig', # Shear/stretch vector
    'k_norm', # L2 norm real and preferred curvature
    'sig_norm', # L2 norm real and preferred curvature    
]


VELOCITY_KEYS = [
    'r_t', # Centreline velocity 
    'w', # Angular velocity
    'k_t', # Curvature rate 
    'sig_t', # Shear/stretch rate    
    ]

FORCE_TORQUE_KEYS = [ 
    'f_F', # External fluid force line density
    'l_F', # External fluid torque line density
    'f_M', # Muscle force line density
    'l_M', # Muscle torque line density
    'N', # Internal force resultant
    'M', # Internal torque resultant
]

POWER_KEYS = [
    'D_F_dot', # Fluid dissipation rate
    'D_I_dot', # Internal dissipation rate   
    'W_dot', # Mechanical muscle power
    'V_dot', # Elastic potential rate 
    ]

FRAME_KEYS = FRAME_KEYS + VELOCITY_KEYS
FRAME_KEYS = FRAME_KEYS + FORCE_TORQUE_KEYS
FRAME_KEYS = FRAME_KEYS + POWER_KEYS
FRAME_KEYS.append('V') # Elastic potential energy     

class Frame(object):
    
    def __init__(self,
         **kwargs):

        assert all(k in FRAME_KEYS for k in kwargs.keys()) 

        for k, v in kwargs.items():
            setattr(self, k, v)
     
class FrameSequence():
        
    def __init__(self, frames):
                
        for k in FRAME_KEYS:                        
            if hasattr(frames[0], k):                        
                setattr(self,  k, np.array([getattr(F, k) for F in frames]))             
      
    def __len__(self):
        return self.r.shape[0]
    
    
                   
                   
                