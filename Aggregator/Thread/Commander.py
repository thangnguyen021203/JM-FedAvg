from Thread.Worker.Manager import Manager
import os, sys

def commander_thread(manager: Manager):
    
    print("Commander is on and wait for input!")

    while True:

        command = input()

        if command == 'stop':
            print("Aggregator stops!")
            manager.set_flag(manager.FLAG.STOP)
            sys.exit()
        
        elif command == 'round info':
            print("Attendee clients in round:")
            for client in manager.client_list:
                print(f"{client.round_ID} - {client.host}:{client.port}, neighbors: {client.neighbor_list}")
                print(f"DH_public_key: {client.DH_public_key}")
                print(f"RSA public key: e: {client.RSA_public_key.e}, n: {client.RSA_public_key.n}")
                print(f"Status: {"Online" if client.is_online else "Offline"}, dataset number: {client.local_datanum}")
                print("-----------")

        elif command == 'info':
            print(f"Aggregator address: {manager.host}:{manager.port}")
            print(f"Round number: {manager.round_number}")
            print(f"Clients connected: {len(manager.client_list)}")
            print(f"Timeout status: {'Timed out' if manager.timeout else 'Collecting updates'}")

        elif command == 'start':
            manager.round_number += 1
            print(f"Starting round {manager.round_number}")
            manager.set_flag(manager.FLAG.START_ROUND)
        
        elif command == 'cls':
            os.system('clear' if os.name != 'nt' else 'cls')
        
        elif command == 'restart':
            os.execv(sys.executable, ['python'] + sys.argv)

        elif command[:5] == 'abort':
            manager.abort_message == command[6:]
            manager.set_flag(manager.FLAG.ABORT)

        elif command == 'local models':
            for client in manager.client_list:
                print(f"Client {client.round_ID}:")
                print(f"Data number: {client.local_datanum}")
                print(f"Local model: {client.local_parameters}")
                print(f"Received time: {client.receipt.received_time}")
                print(f"Signed received data: {client.receipt.signed_received_data}")

        elif command == 'timeout':
            if manager.timeout:
                print("Collection period has ended")
            else:
                print(f"Collecting updates. Received: {manager.received_data}/{len(manager.client_list)}")

        elif command == 'cancel':
            print("Canceling timer and ending collection period")
            if hasattr(manager, 'timer'):
                manager.timer.cancel()
            manager.end_timer()

        elif command == 'client status':
            for client in manager.client_list:
                print(f"Client {client.round_ID} -> {"Online" if client.is_online else "Offline"}")

        elif command == 'secret points':
            for client in manager.client_list:
                print(f"Client {client.round_ID}: {', '.join([f"({point.x}, {point.y})" for point in client.secret_points])}")

        else:
            print("I'm currently supporting these commands: [stop, info, round info, cls, restart, abort <message>, local models, timeout, cancel, client status, secret points]")