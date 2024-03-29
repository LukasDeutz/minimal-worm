'''
Created on 5 Mar 2024

@author: amoghasiddhi
'''
# Built-in
from pathlib import Path
from sys import argv
from argparse import ArgumentParser, BooleanOptionalAction

#from decimal import Decimal

# Third-party
from parameter_scan import ParameterGrid
import pint
import numpy as np

# Local imports
from minimal_worm import FRAME_KEYS
from minimal_worm.worm import CONTROL_KEYS
from minimal_worm.experiments import Sweeper
from minimal_worm.experiments.undulation import UndulationExperiment
from minimal_worm.experiments.undulation import create_storage_dir
from minimal_worm.experiments.undulation.analyse_sweeps import analyse
from minimal_worm.experiments.undulation.thesis import default_sweep_parameter


def default_sweep_parameter():
    '''
    Default sweep hyper parameter
    '''            
    parser = ArgumentParser(description = 'sweep-parameter', allow_abbrev=False)

    parser.add_argument('--worker', type = int, default = 10,
        help = 'Number of processes')         
    parser.add_argument('--run', action=BooleanOptionalAction, default = True,
        help = 'If true, sweep is run. Set to false if sweep has already been run and cached.')     
    parser.add_argument('--pool', action=BooleanOptionalAction, default = True,
        help = 'If true, FrameSequences are pickled to disk')     
    parser.add_argument('--overwrite', action=BooleanOptionalAction, default = False,
        help = 'If true, already existing simulation results are overwritten')
    parser.add_argument('--debug', action=BooleanOptionalAction, default = False,
        help = 'If true, exception handling is turned off which is helpful for debugging')    
    parser.add_argument('--save_to_storage', action=BooleanOptionalAction, default = False,
        help = 'If true, results are saved to external storage filesystem specified in dirs.py')         
    
    # Frame keys
    parser.add_argument('--t', action=BooleanOptionalAction, default = True,
        help = 'If true, save time stamps')
    parser.add_argument('--r', action=BooleanOptionalAction, default = True,
        help = 'If true, save centreline coordinates')
    parser.add_argument('--theta', action=BooleanOptionalAction, default = False,
        help = 'If true, save Euler angles')    
    parser.add_argument('--d1', action=BooleanOptionalAction, default = True,
        help = 'If true, save director 1')
    parser.add_argument('--d2', action=BooleanOptionalAction, default = True,
        help = 'If true, save director 2')
    parser.add_argument('--d3', action=BooleanOptionalAction, default = True,
        help = 'If true, save director 3')
    parser.add_argument('--k', action=BooleanOptionalAction, default = True,
        help = 'If true, save curvature')
    parser.add_argument('--sig', action=BooleanOptionalAction, default = False,
        help = 'If true, saved shear-stretch')
    parser.add_argument('--k_norm', action=BooleanOptionalAction, default = False,
        help = 'If true, save L2 norm of the real and preferred curvature difference')
    parser.add_argument('--sig_norm', action=BooleanOptionalAction, default = False,
        help = 'If true, save L2 norm of the real and preferred shear-stretch difference')

    # Velocity keys
    parser.add_argument('--r_t', action=BooleanOptionalAction, default = False,
        help = 'If trues, save centreline velocity')
    parser.add_argument('--w', action=BooleanOptionalAction, default = False,
        help = 'If true, save angular velocity')
    parser.add_argument('--k_t', action=BooleanOptionalAction, default = False,
        help = 'If true, save curvature strain rate')
    parser.add_argument('--sig_t', action=BooleanOptionalAction, default = False,
        help = 'If true, save shear-stretch strain rate')
    
    # Forces and torque keys
    parser.add_argument('--f_F', action=BooleanOptionalAction, default = False,
        help = 'If true, save fluid drag force density')
    parser.add_argument('--l_F', action=BooleanOptionalAction, default = False,
        help = 'If true, save fluid drag torque density')
    parser.add_argument('--f_M', action=BooleanOptionalAction, default = False,
        help = 'If true, save muscle force density')
    parser.add_argument('--l_M', action=BooleanOptionalAction, default = False,
        help = 'If true, save muscle torque density')
    parser.add_argument('--N_force', action=BooleanOptionalAction, default = False,
        dest = 'N', help = 'If true, save internal force resultant')
    parser.add_argument('--M_torque', action=BooleanOptionalAction, default = False,
        dest = 'M', help = 'If true, save internal torque resultant')

    # Power keys
    parser.add_argument('--D_F_dot', action=BooleanOptionalAction, default = False,
        help = 'If true, save fluid dissipation rate')
    parser.add_argument('--D_I_dot', action=BooleanOptionalAction, default = False,
        help = 'If true, save internal dissipation rate')
    parser.add_argument('--W_dot', action=BooleanOptionalAction, default = False,
        help = 'If true, save mechanical muscle power')
    parser.add_argument('--V_dot', action=BooleanOptionalAction, default = False,
        help = 'If true, save potential rate')
    parser.add_argument('--V', action=BooleanOptionalAction, default = False,
        help = 'If true, save potential')
    
    # Control key
    parser.add_argument('--k0', action=BooleanOptionalAction, default = True,
        help = 'If true, save controls')
    parser.add_argument('--sig0', action=BooleanOptionalAction, default = False,
        help = 'If true, save controls')
    
    return parser

def sweep_c_lam(argv):
    '''
    Parameter sweep over c and lam for fixed a and b
    '''    

    # Parse sweep parameter
    sweep_parser = default_sweep_parameter()    

    sweep_parser.add_argument('--c', 
        type=float, nargs=3, default = [0.5, 2.0, 0.25])    
    sweep_parser.add_argument('--lam', 
        type=float, nargs=3, default = [0.5, 2.0, 0.25])    

    sweep_param = sweep_parser.parse_known_args(argv)[0]    
    
    # The argumentparser for the sweep parameter has a boolean argument 
    # for ever frame key and control key which can be set to true
    # if it should be saved 
    FK = [k for k in FRAME_KEYS if getattr(sweep_param, k)]    
    CK = [k for k in CONTROL_KEYS if getattr(sweep_param, k)]

    print(f'FK={FK}')

    # Parse model parameter
    model_parser = UndulationExperiment.parameter_parser()
    model_param = model_parser.parse_known_args(argv)[0]

    # Simulation
    model_param.T = 10.0
    model_param.dt = 0.01
    model_param.N = 750
 
    # Customize parameter
    model_param.Ds_h = 0.01
    model_param.Ds_t = 0.01
    model_param.s0_h = 0.05
    model_param.s0_t = 0.95
    
    # Waveform
    model_param.use_c = True

    # Print all model parameter whose value has been
    # set via the command line
    cml_args = {k: v for k, v in vars(model_param).items() 
        if v != model_parser.get_default(k)}
    
    if len(cml_args) != 0: 
        print(cml_args)
    
    #===============================================================================
    # Init ParameterGrid 
    #===============================================================================
        
    # # Operating point
    # a, b = 1.0, np.round(10**(-2.5), 4) 
    #
    a = model_param.a.magnitude
    b = model_param.b.magnitude

    # Shape-factor and curvature amplitude     
    c_min, c_max = sweep_param.c[0], sweep_param.c[1]
    c_step = sweep_param.c[2]

    lam_min, lam_max = sweep_param.lam[0], sweep_param.lam[1]
    lam_step = sweep_param.lam[2]

    c_param = {'v_min': c_min, 'v_max': c_max + 0.1*c_step, 
        'N': None, 'step': c_step, 'round': 2}    

    lam_param = {'v_min': lam_min, 'v_max': lam_max + 0.1*lam_step, 
        'N': None, 'step': lam_step, 'round': 2}
    
    grid_param = {
        'c': c_param, 
        'lam': lam_param}
    
    sweep_parser = default_sweep_parameter()    
        
    PG = ParameterGrid(vars(model_param), grid_param)

    if sweep_param.save_to_storage:
        log_dir, sim_dir, sweep_dir = create_storage_dir()     
    else:
        from minimal_worm.experiments.undulation import sweep_dir, log_dir, sim_dir
        
    # Experiments are run using the Sweeper class for parallelization 
    if sweep_param.run:
        Sweeper.run_sweep(
            sweep_param.worker, 
            PG, 
            UndulationExperiment.stw_control_sequence, 
            FK,
            log_dir, 
            sim_dir, 
            sweep_param.overwrite, 
            sweep_param.debug,
            'UExp')

    PG_filepath = PG.save(log_dir)
    print(f'Finished sweep! Save ParameterGrid to {PG_filepath}')
        
    # Pool and save simulation results to hdf5
    filename = Path(
        f'raw_data_'
        f'a={round(a,3)}_b={round(b,3)}_'                
        f'c_min={c_min}_c_max={c_max}_c_step={c_step}_'
        f'lam_min={lam_min}_lam_max={lam_max}_lam_step={lam_step}_'
        f'N={model_param.N}_dt={model_param.dt}_'        
        f'T={model_param.T}.h5')
    
    h5_filepath = sweep_dir / filename

    if sweep_param.pool:        
        Sweeper.save_sweep_to_h5(PG, h5_filepath, sim_dir, FK, CK)
    
    return

    
def sweep_a_b(argv):
    '''
    Parameter sweep over time scale ratios a and b

    Show that swimming speed and energy are fully captured 
    by the system input time scale ratios.          
    '''    

    # Parse sweep parameter
    sweep_parser = default_sweep_parameter()    

    sweep_parser.add_argument('--a', 
        type=float, nargs=3, default = [-2, 3, 0.2])    
    sweep_parser.add_argument('--b', 
        type=float, nargs=3, default = [-3, 0, 0.2])    

    sweep_param = sweep_parser.parse_known_args(argv)[0]    
    
    # The argumentparser for the sweep parameter has a boolean argument 
    # for ever frame key and control key which can be set to true
    # if it should be saved 
    FK = [k for k in FRAME_KEYS if getattr(sweep_param, k)]    
    CK = [k for k in CONTROL_KEYS if getattr(sweep_param, k)]

    # Parse model parameter
    model_parser = UndulationExperiment.parameter_parser()
    model_param = model_parser.parse_known_args(argv)[0]

    # Simulation
    model_param.T = 5.0
    model_param.dt = 0.001
    model_param.N = 750
 
    # Customize parameter
    model_param.Ds_h = 0.01
    model_param.Ds_t = 0.01
    model_param.s0_h = 0.05
    model_param.s0_t = 0.95

    # Waveform
    model_param.c = 1.0
    model_param.use_c = True
    
    # Print all model parameter whose value has been
    # set via the command line
    cml_args = {k: v for k, v in vars(model_param).items() 
        if v != model_parser.get_default(k)}
    
    if len(cml_args) != 0: 
        print(cml_args)

    # Create the ParameterGrid over which we want to run
    # the undulation experiments
    a_min, a_max = sweep_param.a[0], sweep_param.a[1]
    a_step = sweep_param.a[2]

    b_min, b_max = sweep_param.b[0], sweep_param.b[1]
    b_step = sweep_param.b[2]

    a_param = {'v_min': a_min, 'v_max': a_max + 0.1*a_step, 
        'N': None, 'step': a_step, 'round': 4, 'log': True}    

    b_param = {'v_min': b_min, 'v_max': b_max + 0.1*b_step, 
        'N': None, 'step': b_step, 'round': 5, 'log': True}

    grid_param = {'a': a_param, 'b': b_param}
    
    PG = ParameterGrid(vars(model_param), grid_param)

    if sweep_param.save_to_storage:
        log_dir, sim_dir, sweep_dir = create_storage_dir()     
    else:
        from minimal_worm.experiments.undulation import sweep_dir, log_dir, sim_dir
        
    # Experiments are run using the Sweeper class for parallelization 
    if sweep_param.run:
        Sweeper.run_sweep(
            sweep_param.worker, 
            PG, 
            UndulationExperiment.stw_control_sequence, 
            FK,
            log_dir, 
            sim_dir, 
            sweep_param.overwrite, 
            sweep_param.debug,
            'UExp')

    PG_filepath = PG.save(log_dir)
    print(f'Finished sweep! Save ParameterGrid to {PG_filepath}')
        
    # Pool and save simulation results to hdf5
    filename = Path(
        f'raw_data_'
        f'a_min={a_min}_a_max={a_max}_a_step={a_step}_'
        f'b_min={b_min}_b_max={b_max}_b_step={b_step}_'
        f'A={model_param.A}_lam={model_param.lam}_'
        f'T={model_param.T}_'        
        f'N={model_param.N}_dt={model_param.dt}.h5')
    
    h5_filepath = sweep_dir / filename

    if sweep_param.pool:        
        Sweeper.save_sweep_to_h5(PG, h5_filepath, sim_dir, FK, CK)
                
    return

def sweep_a_b_list(argv):
    '''
    Simulate small number of a and b values
    '''

    # Parse sweep parameter
    sweep_parser = default_sweep_parameter()    

    sweep_parser.add_argument('--a', type=float, nargs='+')    
    sweep_parser.add_argument('--b', type=float, nargs='+')    

    sweep_param = sweep_parser.parse_known_args(argv)[0]    
    
    # The argumentparser for the sweep parameter has a boolean argument 
    # for ever frame key and control key which can be set to true
    # if it should be saved 
    FK = [k for k in FRAME_KEYS if getattr(sweep_param, k)]    
    CK = [k for k in CONTROL_KEYS if getattr(sweep_param, k)]

    # Parse model parameter
    model_parser = UndulationExperiment.parameter_parser()
    model_param = model_parser.parse_known_args(argv)[0]

    # Simulation
    model_param.T = 5.0
    model_param.dt = 0.001
    model_param.N = 750
 
    # Customize parameter
    model_param.Ds_h = 0.01
    model_param.Ds_t = 0.01
    model_param.s0_h = 0.05
    model_param.s0_t = 0.95

    # Waveform
    model_param.c = 1.0
    model_param.use_c = True
    
    # Print all model parameter whose value has been
    # set via the command line
    cml_args = {k: v for k, v in vars(model_param).items() 
        if v != model_parser.get_default(k)}
    
    if len(cml_args) != 0: 
        print(cml_args)

    # Create the ParameterGrid over which we want to run
    # the undulation experiments

    a_arr, b_arr = sweep_param.a, sweep_param.b
         
    a_param = {'v_arr': a_arr, 'round': 4, 'log': False}
    b_param = {'v_arr': b_arr, 'round': 5, 'log': False}

    grid_param = {('a', 'b'): (a_param, b_param)}
    
    PG = ParameterGrid(vars(model_param), grid_param)

    if sweep_param.save_to_storage:
        log_dir, sim_dir, sweep_dir = create_storage_dir()     
    else:
        from minimal_worm.experiments.undulation import sweep_dir, log_dir, sim_dir
        
    # Experiments are run using the Sweeper class for parallelization 
    if sweep_param.run:
        Sweeper.run_sweep(
            sweep_param.worker, 
            PG, 
            UndulationExperiment.stw_control_sequence, 
            FK,
            log_dir, 
            sim_dir, 
            sweep_param.overwrite, 
            sweep_param.debug,
            'UExp')

    PG_filepath = PG.save(log_dir)
    print(f'Finished sweep! Save ParameterGrid to {PG_filepath}')
        
    # Pool and save simulation results to hdf5
    filename = Path(
        f'raw_data_'
        f'a_arr={np.round(a_arr,4)}_'
        f'b_arr={np.round(b_arr, 3)}_'
        f'A={model_param.A}_lam={model_param.lam}_'
        f'T={model_param.T}_'        
        f'N={model_param.N}_dt={model_param.dt}.h5')
    
    h5_filepath = sweep_dir / filename

    if sweep_param.pool:        
        Sweeper.save_sweep_to_h5(PG, h5_filepath, sim_dir, FK, CK)
                
    return


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('-sweep',  
        choices = ['c_lam', 'a_b', 'a_b_list'], help='Sweep to run')
            
    # Run function passed via command line
    args = parser.parse_known_args(argv)[0]    
    globals()['sweep_' + args.sweep](argv)



    
    
    



    



