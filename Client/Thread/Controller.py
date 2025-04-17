from Thread.Worker.Manager import Manager
from Thread.Worker.Thread_Controller import *
from time import sleep

def controller_thread(manager: Manager):

    print("Controller is on and at duty!")

    # Register with Trusted Party
    asyncio.run(send_CLIENT(manager))

    while True:

        flag = manager.get_flag()

        if flag == manager.FLAG.STOP:

            print("Got the STOP signal from Trusted party, please command 'stop' to quit!")

        elif flag == manager.FLAG.ABORT:

            asyncio.run(send_ABORT(manager.abort_message))
        
        elif flag == manager.FLAG.RE_REGISTER:

            asyncio.run(send_CLIENT(manager))
        
        elif flag == manager.FLAG.TRAIN:

            print(f"[Client {manager.round_ID}] Starting round {manager.round_number} with gs_mask: {manager.gs_mask}")
            asyncio.run(send_POINTS(manager))
            manager.start_train()
            asyncio.run(send_LOCAL_MODEL(manager))

        sleep(5)