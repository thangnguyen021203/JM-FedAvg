import torch, numpy, os
from torch.utils.data import DataLoader, TensorDataset, Subset
import torch.nn.functional as F
from torch.nn.utils import parameters_to_vector, vector_to_parameters
from Thread.Worker.BaseModel import *
import torchvision, torch.optim as optim
from tqdm import tqdm
from Thread.Worker.Helper import Helper

class Trainer:

    def __init__(self, model_type: type):
        self.device = Helper.get_device()
        print(f"Trainer initialized with device: {self.device}")

        # Instantiate and move model to device
        self.local_model : CNNModel_MNIST = model_type().to(self.device)

        self.dataset_type = model_type.__name__.split('_')[-1]
        self.batch_size = int(Helper.get_env_variable('BATCH_SIZE'))
        self.epoch_num = int(Helper.get_env_variable('EPOCH'))
        self.learning_rate = float(Helper.get_env_variable('LEARNING_RATE'))
        
        self.optimizer = optim.SGD(self.local_model.parameters(), lr=self.learning_rate, momentum=0.5)
        self.get_parameters()
        # self.optimizer = self.local_model.optimizer
        # self.lossf = self.local_model.loss

    def set_dataset_ID(self, ID: int, round_number: int):
        self.ID = ID
        self.root_dataset: type = getattr(torchvision.datasets, self.dataset_type)

        transform = torchvision.transforms.Compose([torchvision.transforms.ToTensor()])
        self.root_train_data = self.root_dataset(root="Thread/Worker/Data", train=True, download=True, transform=transform)
        self.root_test_data = self.root_dataset(root="Thread/Worker/Data", train=False, download=True, transform=transform)

        ATTEND_CLIENTS = int(Helper.get_env_variable('ATTEND_CLIENTS'))
        subset_num = int(Helper.get_env_variable('SUBSET_NUM'))

        self.data_num = len(self.root_train_data) // subset_num
        start = ((round_number * ATTEND_CLIENTS + self.ID) * self.data_num) % len(self.root_train_data)
        end = ((round_number * ATTEND_CLIENTS + self.ID + 1) * self.data_num) % len(self.root_train_data)

        if start < end:
            indices = range(start, end)
        else:
            indices = list(range(start, len(self.root_train_data))) + list(range(0, end))
        self.self_train_data = Subset(self.root_train_data, indices)

        self.test_data_num = len(self.root_test_data) // subset_num
        test_start = ((round_number * ATTEND_CLIENTS + self.ID) * self.test_data_num) % len(self.root_test_data)
        test_end = ((round_number * ATTEND_CLIENTS + self.ID + 1) * self.test_data_num) % len(self.root_test_data)

        if test_start < test_end:
            test_indices = range(test_start, test_end)
        else:
            test_indices = list(range(test_start, len(self.root_test_data))) + list(range(0, test_end))
        self.self_test_data = Subset(self.root_test_data, test_indices)

    @Helper.timing
    def load_parameters(self, parameters: numpy.ndarray[numpy.float32], round_ID: int):
        # Create Models directory if it doesn't exist
        models_dir = "Thread/Worker/Data/Models"
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
        
        self.local_model.cpu()
        tensor = torch.tensor(parameters, dtype=torch.float32, requires_grad=True)
        torch.save(self.local_model, f"{models_dir}/{round_ID}_old.pth")
        vector_to_parameters(tensor, self.local_model.parameters())
        torch.save(self.local_model, f"{models_dir}/{round_ID}_new.pth")
        self.local_model.to(self.device)

    def get_parameters(self) -> numpy.ndarray[numpy.float32]:
        self.local_model.cpu()
        params = parameters_to_vector(self.local_model.parameters()).detach().numpy()
        self.local_model.to(self.device)
        return params

    def __get_data__(self, data: Subset) -> TensorDataset:
        
        if self.root_dataset == torchvision.datasets.MNIST:
            origin_data = torch.stack([data.dataset[idx][0] for idx in data.indices])
            target_label = torch.tensor([data.dataset[idx][1] for idx in data.indices])
            return TensorDataset(origin_data, target_label)
    
        # Please input here any another root_dataset type (cifar10, cifar100, etc.)
        # elif self.root_dataset == torchvision.datasets.CIFAR10:
        #     pass

        else:
            raise Exception("There is no data available to get!")
        
    def __get_train_data__(self) -> TensorDataset:
        return self.__get_data__(self.self_train_data)
    
    def __get_test_data__(self) -> TensorDataset:
        return self.__get_data__(self.self_test_data)

    @Helper.timing
    def train(self):
        train_loader = DataLoader(self.__get_train_data__(), batch_size = self.batch_size)
        self.local_model.train()

        for epoch_idx in range(self.epoch_num):
            running_loss = 0.0
            correct = 0
            total = 0

            for data, target in tqdm(train_loader, unit=" data", leave=False):
                data, target = data.to(self.device), target.to(self.device)
                self.optimizer.zero_grad()
                output = self.local_model(data)
                # loss = self.lossf(output, target)
                loss = F.nll_loss(output, target)
                loss.backward()
                self.optimizer.step()

                running_loss += loss.item() * data.size(0)
                _, predicted = torch.max(output,1)
                correct += (predicted == target).sum().item()
                total += target.size(0)

            epoch_loss = running_loss / total
            epoch_acc = correct / total
            print(f"Epoch [{epoch_idx+1}/{self.epoch_num}], Loss: {epoch_loss:.4f}, Accuracy: {epoch_acc:.4f}")

    @torch.no_grad
    def test(self):
        self.local_model.eval()
        test_loader = DataLoader(self.__get_test_data__())

        test_loss = 0
        correct = 0

        for data, target in tqdm(test_loader, unit=" data", leave=False):
            data, target = data.to(self.device), target.to(self.device)
            output = self.local_model(data)
            # test_loss += self.lossf(output, target).item()
            test_loss += F.nll_loss(output, target, reduction="sum").item()
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()

        test_loss /= len(test_loader.dataset)
        accuracy = 100.0 * correct / len(test_loader.dataset)
        print(f'[Evaluation]: Test Loss = {test_loss:.4f}, Accuracy: {correct}/{len(test_loader.dataset)} ({accuracy:.0f}%)')

        return float(accuracy)

    # def train_model(self):

    #     train_loader = DataLoader(self.__get_train_data__(), batch_size = self.batch_size)
    #     test_loader = DataLoader(self.__get_test_data__())
        
    #     for epoch_idx in range(self.epoch_num):  
    #         self.local_model.train()
    #         self.train(train_loader)
    #         epoch_idx += 1
    #         self.local_model.eval()
    #         self.test(test_loader, epoch_idx)

    # def test_model(self):
    #     test_loader = DataLoader(self.__get_test_data__())
    #     self.local_model.eval()
    #     self.test(test_loader, epoch_idx=0)