from Thread.Worker.Manager import Manager
from Thread.Worker.Helper import Helper
from Thread.Worker.Thread_Controller import *
from time import sleep, time
import os, sys
from Thread.Worker.Unmasker import Unmasker

def controller_thread(manager: Manager):

    total_time_aggregation = 0

    print("Controller is on and at duty!")

    # Register with Trusted Party
    asyncio.run(send_AGG_REGIS(manager))

    while True:

        flag = manager.get_flag()

        if flag == manager.FLAG.STOP:

            summary_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Summary.txt")
            with open(summary_path, "a") as f:
                f.write(f"Total aggregation time: {total_time_aggregation} seconds\n")
                f.write(f"Total calculation secrets time: {Unmasker.total_calSecret_time} seconds\n")

            print("Got the STOP signal from Trusted party, please command 'stop' to quit!")
            sys.exit()  # Changed from quit() to sys.exit()

        elif flag == manager.FLAG.ABORT:

            asyncio.run(send_ABORT(manager.abort_message))
        
        elif flag == manager.FLAG.START_ROUND:

            asyncio.run(send_GLOB_MODEL(manager))
            manager.start_timer(int(Helper.get_env_variable("TIMEOUT_SECONDS")))

        elif flag == manager.FLAG.AGGREGATE:
            asyncio.run(send_STATUS(manager))
            start_aggregate = time()
            manager.aggregate()
            end_aggregate = time()
            total_time_aggregation += end_aggregate - start_aggregate
            asyncio.run(send_AGG_MODEL(manager))

        elif flag == manager.FLAG.RE_REGISTER:

            asyncio.run(send_AGG_REGIS(manager))

        sleep(5)