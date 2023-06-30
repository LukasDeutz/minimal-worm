'''
Created on 15 Jun 2023

@author: amoghasiddhi
'''
# Built-in
from pathlib import Path
from sys import argv
from argparse import ArgumentParser, BooleanOptionalAction

# Third-party
from parameter_scan import ParameterGrid

# Local imports
from minimal_worm.experiments import Sweeper, Saver
from minimal_worm.experiments.undulation import UndulationExperiment
from minimal_worm.experiments.undulation import sweep_dir, log_dir, sim_dir, create_storage_dir
from minimal_worm.experiments.undulation.analyse_sweeps import analyse_a_b

def default_sweep_parameter():
    '''
    Default sweep hyper parameter
    '''            
    parser = ArgumentParser(description = 'sweep-parameter')

    parser.add_argument('--worker', type = int, default = 10,
        help = 'Number of processes')         
    parser.add_argument('--run', action=BooleanOptionalAction, default = True,
        help = 'If true, sweep is run. Set to false if sweep has already been run and cached.')     
    parser.add_argument('--pool', action=BooleanOptionalAction, default = True,
        help = 'If true, FrameSequences are pickled to disk') 
    parser.add_argument('--analyse', action=BooleanOptionalAction, default = True,
        help = 'If true, analyse pooled raw data')     
    parser.add_argument('--overwrite', action=BooleanOptionalAction, default = False,
        help = 'If true, already existing simulation results are overwritten')
    parser.add_argument('--debug', action=BooleanOptionalAction, default = False,
        help = 'If true, exception handling is turned off which is helpful for debugging')    
    parser.add_argument('--save_to_storage', action=BooleanOptionalAction, default = False,
        help = 'If true, results are saved to external storage filesystem specified in dirs.py')         

    return parser

def sweep_a_b(argv):
    '''
    Parameter sweep over time scale ratios a and b

    Show that swimming speed and energy are fully captured 
    by the system input time scale ratios.          
    '''    

    # parse sweep parameter
    sweep_parser = default_sweep_parameter()    

    sweep_parser.add_argument('--a', 
        type=float, nargs=3, default = [-2, 3, 1.0])    
    sweep_parser.add_argument('--b', 
        type=float, nargs=3, default = [-3, 0, 1.0])    
    sweep_parser.add_argument('--FK', nargs = '+', 
        default = [
            't', 'r', 'theta', 'd1', 'd2', 'd3', 'k', 'sig', 
            'k_norm', 'sig_norm', 'r_t', 'w', 'k_t', 'sig_t', 
            'W_dot', 'D_F_dot', 'D_I_dot', 'V_dot']
        )
    sweep_parser.add_argument('--FK_pool', nargs = '+', 
        default = [
            'r', 'k', 'sig', 'k_norm', 'sig_norm', 'r_t',
            'W_dot', 'D_F_dot', 'D_I_dot', 'V_dot']
        )

    sweep_param = sweep_parser.parse_known_args(argv)[0]    

    # parse model parameter and convert to dict
    model_parser = UndulationExperiment.parameter_parser()
    model_param = model_parser.parse_known_args(argv)[0]

    # print all command-line-arguments assuming that they
    # are different from the default option 
    cml_args = {k: v for k, v in vars(model_param).items() 
        if v != model_parser.get_default(k)}
    
    if len(cml_args) != 0: 
        print(cml_args)

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
                
    if sweep_param.run:
        # Run sweep
        Sweeper.run_sweep(
            sweep_param.worker, 
            PG, 
            UndulationExperiment.stw_control_sequence, 
            sweep_param.FK,
            log_dir, 
            sim_dir, 
            sweep_param.overwrite, 
            sweep_param.debug,
            'UExp')

    PG_filepath = PG.save(log_dir)
    print(f'Finished sweep! Save ParameterGrid to {PG_filepath}')

    # dt's number of decimal places 
    dp = len(str(model_param.dt).split('.')[1])  

    # Run sweep
    filename = Path(
        f'raw_data_'
        f'a_min={a_min}_a_max={a_max}_step_a={a_step}_'
        f'b_min={b_min}_b_max={b_max}_step_b={b_step}_'
        f'A={model_param.A}_lam={model_param.lam}_'
        f'N={model_param.N}_dt={model_param.dt:{dp}f}.h5')        
    
    h5_filepath = sweep_dir / filename

    if sweep_param.pool:        
        Sweeper.save_sweep_to_h5(PG, h5_filepath, sim_dir, sweep_param.FK_pool)

    if sweep_param.analyse:
        analyse_a_b(h5_filepath)
                
    return

if __name__ == '__main__':
        
    parser = ArgumentParser()
    parser.add_argument('-sweep',  
        choices = ['a_b'], help='Sweep to run')
        
    # Run function passed via command line
    args = parser.parse_known_args(argv)[0]    
    globals()['sweep_' + args.sweep](argv)





