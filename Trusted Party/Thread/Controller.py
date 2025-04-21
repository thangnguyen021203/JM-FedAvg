from Thread.Worker.Manager import Manager, Round_Manager
from Thread.Worker.Thread_Controller import *
from time import sleep, time
import os, sys

ATTEND_CLIENTS = Helper.get_env_variable('ATTEND_CLIENTS')

def controller_thread(manager: Manager):

    total_time_convergence = 0

    print("Controller is on and at duty!")
    stop_rounds = False

    # Get next command from stdinput
    while True:
        
        flag = manager.get_flag()

        if flag == manager.FLAG.STOP:

            print("Got the ABORT signal, send the STOP signal...")
            sys.exit()

        # When training is complete, send STOP signals to all clients and Aggregator
        elif flag == manager.FLAG.TRAINING_COMPLETE:

            total_time_convergence = time() - total_time_convergence

            print("Training complete! Sending STOP signals to all clients and Aggregator...")
            manager.stop_message = "Training complete. Target accuracy achieved."
            
            # Write results to file before sending STOP
            summary_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Summary.txt")
            with open(summary_path, "a") as f:
                f.write(f"Training completed successfully in {manager.current_round-1} rounds\n")
                f.write(f"Total time to convergence: {total_time_convergence} seconds\n")
                
            # Send STOP to all clients and aggregator
            asyncio.run(send_STOP(manager))
            
            # Now set flag to STOP and continue processing
            manager.set_flag(manager.FLAG.STOP)


        # Init the round
        elif flag == manager.FLAG.START_ROUND:
            
            if manager.current_round == 1:
                total_time_convergence = time()

            manager.round_manager = Round_Manager(manager.choose_clients(ATTEND_CLIENTS), manager.get_current_round())
            asyncio.run(send_DH_PARAM(manager))
            asyncio.run(send_ROUND_INFO_client(manager))
            asyncio.run(send_ROUND_INFO_aggregator(manager))

            # Increment the round number after starting a new round
            manager.current_round += 1
        else:

            pass

        sleep(5)