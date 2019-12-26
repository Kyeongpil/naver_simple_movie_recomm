import torch
from torch.nn import CrossEntropyLoss as TrainLoss
from torch.nn import CrossEntropyLoss as ValidLoss
from torch.nn.utils import clip_grad_norm_
from torch.optim import Adam
from torch.optim.lr_scheduler import StepLR
from model.dataset import MovieDataset, PadCollate
from torch.utils.data import DataLoader
from model.model import MoviePredict
import pickle


epochs = 20
batch_size = 128
lr = 1e-3


with open('./meta_data.pkl', 'rb') as f:
    data = pickle.load(f)
    voca_num = len(data['vocab'])
    actor_num = len(data['actors'])
    director_num = len(data['directors'])
    category_num = len(data['categories'])
    country_num = len(data['countries'])
    scaler = data['scaler']
    data_transformer = data['data_transformer']

movie_dataset = MovieDataset('./train_data.json')
dataloader = DataLoader(movie_dataset, collate_fn=PadCollate(), batch_size=batch_size, shuffle=True)
movie_dataset = MovieDataset('./valid_data.json')
valid_dataloader = DataLoader(movie_dataset, collate_fn=PadCollate(), batch_size=batch_size, shuffle=True)

device = torch.device('cuda:0')
model = MoviePredict(voca_num, actor_num, director_num, category_num, country_num)
model.to(device)
criterion = TrainLoss()
valid_criterion = ValidLoss()
optim = Adam(model.parameters(), lr=lr, weight_decay=1e-6)
scheduler = StepLR(optim, step_size=5, gamma=0.1)

for e in range(epochs):
    model.train()
    for i, (*inputs, score) in enumerate(dataloader):
        optim.zero_grad()
        inputs = [input_.to(device) for input_ in inputs]
        score = score.to(device).contiguous().view(-1)
        

        predicted = model(*inputs)
        
        loss = criterion(predicted, score)
        loss.backward()
        clip_grad_norm_(model.parameters(), 5.0)
        optim.step()

    valid_loss = 0.0
    acc = 0.0
    model.eval()
    total_num = 0
    for *inputs, score in valid_dataloader:
        batch_size = score.size(0)
        inputs = [input_.to(device) for input_ in inputs]
        score = score.to(device).contiguous().view(-1)
        predicted = model(*inputs)
        valid_loss += valid_criterion(predicted, score).item()*batch_size
        predicted = predicted.argmax(dim=1)
        acc += torch.eq(predicted, score).sum()
        total_num += batch_size
    
    valid_loss /= total_num
    acc /= total_num
    print(f"{e} - {loss.item():.4f}, {valid_loss:.4f}, acc: {acc:.4f}")

    scheduler.step()
        