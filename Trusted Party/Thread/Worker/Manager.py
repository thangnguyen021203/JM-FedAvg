from Thread.Worker.Helper import Helper
from Thread.Worker.BaseModel import *           # This can be removed
import random, numpy
from sympy import randprime, primitive_root
from copy import deepcopy
import asyncio

class RSA_public_key:
    
    def __init__(self, e, n):
        self.e = e
        self.n = n

class Client_info:
        
    def __init__(self, ID: int, host: str, port: int, rsa_public_key: RSA_public_key):
        # Unique attributes
        self.ID = ID
        self.host = host
        self.port = port
        self.RSA_public_key = rsa_public_key
        self.choose_possibility = 100
        # Round attributes
        self.round_ID = 0
        self.DH_public_key = 0
        self.neighbor_list = None

    def set_DH_public_key(self, DH_public_key: int):
        self.DH_public_key = DH_public_key

    def set_round_information(self, client_round_ID: int, neighbor_round_ID_list: list[int]):
        self.round_ID = client_round_ID
        self.neighbor_list = neighbor_round_ID_list

class Aggregator_info:

    def __init__(self, host: str, port: int, public_key: RSA_public_key, base_model_class: type):
        self.host = host
        self.port = port
        self.RSA_public_key = public_key
        self.base_model_class = base_model_class

# class Commiter:

#     def __init__(self):
#         self.p = randprime(1 << 63, 1 << 64)
#         self.h = primitive_root(self.p)
#         self.k = random.randint(1 << 63, 1 << 64)
#         self.r = None

class DH_params:

    def __init__(self):
        DH_param_list = open("Thread/Worker/Data/DH_params.csv", "r", encoding="UTF-8").readlines()[1:]
        DH_param_pair = DH_param_list[random.randint(0, len(DH_param_list)-1)].split(",")
        self.q, self.g = int(DH_param_pair[1]), int(DH_param_pair[2])

class Manager():

    class FLAG:
        class NONE:
            # Default value
            pass
        class START_ROUND:
            # When get initiation signal user
            pass
        class STOP:
            # Used to indicate situation that needs process stopping
            pass
        class TRAINING_COMPLETE:
            # Used to indicate training is complete
            pass

    def __init__(self):
        # FL parameters
            # Communication
        self.client_list : list[Client_info] = list()
        self.aggregator_info = None
            # Public parameters
        # self.commiter = Commiter()
        self.current_round = 0
        # self.last_commitment: numpy.ndarray[numpy.int64] = None
        self.gs_mask = random.randint(1, 2 ** 64)
            # Controller
        self.flag = self.FLAG.NONE
        self.stop_message = ""
        # Round parameters
        self.round_manager : Round_Manager = None
        # Model accuracy tracking
        self.client_accuracies = {}  # Dict to store client_round_ID -> accuracy
        self.accuracy_threshold = Helper.get_env_variable("ACCURACY_THRESHOLD") 
        self.completion_threshold = Helper.get_env_variable("CLIENT_PERCENT_THRESHOLD") 
        # Track participated clients in each round
        self.participated_clients = set()  # Set of client IDs that participated in the current round

    def stop(self, message: str):
        self.stop_message = message
        self.set_flag(self.FLAG.STOP)

    def get_flag(self) -> type:
        if self.flag == Manager.FLAG.NONE:
            return Manager.FLAG.NONE
        print(f"Get flag of {self.flag.__name__}")
        return_flag = self.flag
        self.flag = Manager.FLAG.NONE
        return return_flag

    def set_flag(self, flag: type) -> None:
        self.flag = flag
        print(f"Set flag to {self.flag.__name__}")

    def clear_client(self) -> None:
        self.client_list.clear()
    
    def clear_aggregator(self) -> None:
        self.aggregator_info = None
        # self.last_commitment = None

    def register_aggregator(self, host: str, port: int, public_key: RSA_public_key, base_model_class: type):
        self.aggregator_info = Aggregator_info(host, port, public_key, base_model_class)

    # def set_last_model_commitment(self, model_commitment: numpy.ndarray[numpy.int64]):
    #     self.last_commitment = model_commitment

    def __get_client_by_ID__(self, client_ID: int) -> Client_info | None:
        for client_info in self.client_list:
            if client_info.ID == client_ID:
                return client_info
        return None
    
    def __get_client_by_round_ID__(self, client_round_ID: int) -> Client_info | None:
        for client_info in self.client_list:
            if client_info.round_ID == client_round_ID:
                return client_info
        return None

    def add_client(self, client_id: int, host: str, port: int, rsa_public_key: RSA_public_key) -> None:
        self.client_list.append(Client_info(client_id, host, port, rsa_public_key))

    def get_current_round(self) -> int:
        return self.current_round

    # def get_commiter(self) -> Commiter:
    #     return self.commiter
    
    def choose_clients(self, client_num: int) -> list[Client_info]:
        # Implementation remains for backwards compatibility
        if client_num > len(self.client_list):
            client_num = len(self.client_list)
        
        # Before selecting clients, update their selection points based on previous participation
        if self.current_round > 0:  # Only update points after the first round
            self.update_client_selection_points()
            
        return_list = list()
        client_list = deepcopy(self.client_list)
        
        # Print client selection probabilities for this round
        print(f"\n----- Round {self.current_round} Client Selection Probabilities -----")
        for client in client_list:
            print(f"Client ID: {client.ID} - Probability points: {client.choose_possibility}")
        print("--------------------------------------------------------\n")
        
        # Thêm Ping Client vào đây
        from Thread.Worker.Thread_Controller import send_PING
        for client in client_list:
            try:
                asyncio.run(send_PING(client))
            except ConnectionRefusedError:
                client_list.remove(client)


        for i in range(client_num):
            chosen_one = random.choices(client_list, weights=[max(client.choose_possibility, 0) for client in client_list])[0]
            client_list.remove(chosen_one)
            return_list.append(chosen_one)
            
        # Store the IDs of selected clients for this round
        self.participated_clients = {client.ID for client in return_list}
        
        return return_list
    
    def update_client_selection_points(self):
        """Update client selection points based on participation in the previous round"""
        for client in self.client_list:
            if client.ID in self.participated_clients:
                # Client participated in the previous round: -25 points
                client.choose_possibility -= 25
                print(f"Client {client.ID} participated in previous round: -25 points (now {client.choose_possibility})")
            else:
                # Client did not participate in the previous round: +25 points
                client.choose_possibility += 25
                print(f"Client {client.ID} did not participate in previous round: +25 points (now {client.choose_possibility})")
        # Sau khi đã cập nhật xong:
        if any(client.choose_possibility <= 0 for client in self.client_list):
            for client in self.client_list:
                client.choose_possibility += 25
                print("Có client có possibility <= 0, đã cộng thêm 25 cho tất cả clients.")

    def record_client_accuracy(self, client_round_id: int, accuracy: float) -> None:
        """Record a client's accuracy for the current round"""
        self.client_accuracies[client_round_id] = accuracy
        print(f"Received accuracy from client {client_round_id}: {accuracy:.2f}%")
        
        # Get the actual client ID from round ID - look in round_manager.client_list instead
        client = None
        if self.round_manager:
            client = self.round_manager.__get_client_by_round_ID__(client_round_id)
                # If not found in round_manager, try the main client list as fallback
        if not client:
            client = self.__get_client_by_round_ID__(client_round_id)
           
        client_id = client.ID if client else f"RoundID-{client_round_id}"
                # Write to Summary.txt
        import os
        summary_path = os.path.abspath(os.path.join(__file__, "..", "..", "..", "..", "Summary.txt"))
                # Format: "Round X Client Y Accuracy Z%"
        summary_entry = f"Round {self.current_round } Client {client_id} Accuracy {accuracy:.2f}%\n"
                # Append the information to Summary.txt
        with open(summary_path, 'a') as f:
            f.write(summary_entry)
           
        print(f"Client accuracy information saved to Summary.txt: {summary_entry.strip()}")
                # Check if all clients have reported their accuracy
        if len(self.client_accuracies) == len(self.round_manager.client_list):
            self.evaluate_model_performance()
    

    def evaluate_model_performance(self) -> None:
        """Evaluate if training should complete or continue to next round"""
        if not self.client_accuracies:
            print("No accuracy data available for evaluation")
            return
            
        # Count clients meeting the accuracy threshold
        clients_meeting_threshold = sum(1 for acc in self.client_accuracies.values() if acc >= self.accuracy_threshold)
        total_clients = len(self.client_accuracies)
        percentage_meeting_threshold = clients_meeting_threshold / total_clients
        
        print(f"\n----- Model Performance Evaluation -----")
        print(f"Round {self.current_round} - Clients meeting {self.accuracy_threshold}% threshold: "
              f"{clients_meeting_threshold}/{total_clients} ({percentage_meeting_threshold*100:.1f}%)")
        
        if percentage_meeting_threshold >= self.completion_threshold:
            print(f"Training complete! {percentage_meeting_threshold*100:.1f}% clients "
                  f"have accuracy >= {self.accuracy_threshold}%")
            # Set flag to complete training
            self.set_flag(self.FLAG.TRAINING_COMPLETE)
        else:
            print(f"Training will continue to next round. Only {percentage_meeting_threshold*100:.1f}% "
                  f"clients met the accuracy threshold (target: {self.completion_threshold*100:.1f}%)")
            # Reset accuracy tracking for next round
            self.client_accuracies = {}
            # Set flag to start a new round
            self.set_flag(self.FLAG.START_ROUND)
    
class Round_Manager():

    def __init__(self, client_list: list[Client_info], round_number: int):
        self.client_list = client_list
        self.round_number = round_number
        
        # Create graph and add round information for clients
        # Please insert here to specify the neighbor_num more useful
        # neighbor_num = min(30, len(self.client_list)-1)
        neighbor_num = int(Helper.get_env_variable("NUM_NEIGHBORS"))
        graph = Helper.build_graph(len(self.client_list), min(neighbor_num, len(self.client_list)))
        for round_ID in range(len(self.client_list)):
            self.client_list[round_ID].set_round_information(round_ID, graph[round_ID])

        self.dh_params = DH_params()

    def get_DH_params(self) -> DH_params:
        return self.dh_params
    
    def set_DH_public_key(self, client_ID: int, DH_public_key: int) -> None:
        self.__get_client_by_ID__(client_ID).set_DH_public_key(DH_public_key)

    def __get_client_by_ID__(self, client_ID: int) -> Client_info | None:
        for client_info in self.client_list:
            if client_info.ID == client_ID:
                return client_info
        return None
    
    def __get_client_by_round_ID__(self, client_round_ID: int) -> Client_info | None:
        for client_info in self.client_list:
            if client_info.round_ID == client_round_ID:
                return client_info
        return None

    def get_neighbor_information(self, client_id: int) -> list:
        
        client = self.__get_client_by_ID__(client_id)
        neighbor_information = list()
        for neighbor_round_id in client.neighbor_list:
            neighbor = self.__get_client_by_round_ID__(neighbor_round_id)
            neighbor_information.append((neighbor_round_id, neighbor.host, neighbor.port, neighbor.DH_public_key))
        return neighbor_information