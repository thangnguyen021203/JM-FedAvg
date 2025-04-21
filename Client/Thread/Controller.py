from Thread.Worker.Manager import Manager
from Thread.Worker.Thread_Controller import *
from time import sleep, time
import os, sys

def controller_thread(manager: Manager):

    total_training_time = 0

    print("Controller is on and at duty!")

    # Register with Trusted Party
    asyncio.run(send_CLIENT(manager))

    while True:

        flag = manager.get_flag()

        if flag == manager.FLAG.STOP:

            # Write total_training_time to Summary.txt
            summary_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Summary.txt")
            with open(summary_path, "a") as f:
                f.write(f"Total training time for client: {total_training_time} seconds\n")
            
            print("Got the STOP signal from Trusted party, please command 'stop' to quit!")
            sys.exit()

        elif flag == manager.FLAG.ABORT:

            asyncio.run(send_ABORT(manager.abort_message))
        
        elif flag == manager.FLAG.RE_REGISTER:

            asyncio.run(send_CLIENT(manager))
        
        elif flag == manager.FLAG.TRAIN:
    
            print(f"[Client {manager.round_ID}] Starting round {manager.round_number} with gs_mask: {manager.gs_mask}")
            asyncio.run(send_POINTS(manager))
            start_train = time()
            manager.start_train()
            end_train = time()
            total_training_time += end_train - start_train
            asyncio.run(send_LOCAL_MODEL(manager))

        sleep(5)