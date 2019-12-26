from itertools import chain

import torch
import ujson as json
from torch.utils.data.dataset import Dataset


class MovieDataset(Dataset):
    def __init__(self, file_path):
        self.MAX_ACTOR_NUM = 64
        self.MAX_DIRECTOR_NUM = 8
        self.MAX_STORY_LEN = 100
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.actors = [[actor['id'] for actor in movie['actors']] for movie in data]
        self.directors = [[director['id'] for director in movie['directors']] for movie in data]
        self.categories = [movie['categories_id'] for movie in data]
        self.countries = [movie['countries_id'] for movie in data]
        self.story = [movie['story_parsed'][:self.MAX_STORY_LEN] for movie in data]
        self.score = [movie['score'] for movie in data]

        self.num_data = len(data)

    def __getitem__(self, index):
        actors = self.actors[index]
        directors = self.directors[index]
        categories = self.categories[index]
        countries = self.countries[index]
        story = self.story[index]
        score = self.score[index]
        if score > 0.5:
            score = [1]
        elif score < -0.5:
            score = [2]
        else:
            score = [0]
        return actors, directors, categories, countries, story, score
    
    def __len__(self):
        return self.num_data


class PadCollate:
    def __init__(self, pad_index=0, dim=0):
        self.dim = dim
        self.pad_index = pad_index

    def pad_collate(self, batch):
        def pad_tensor(vec, max_len, dim):
            pad_size = list(vec.shape)
            pad_size[dim] = max_len - vec.size(dim)
            return torch.cat([vec, torch.LongTensor(*pad_size).fill_(self.pad_index)], dim=dim)

        def pack_sentence(sequences):
            sequences_len = max(map(lambda x: len(x), sequences))
            sequences = [pad_tensor(torch.LongTensor(seq), sequences_len, self.dim) for seq in sequences]
            sequences = torch.cat(sequences)
            sequences = sequences.view(-1, sequences_len)
            return sequences

        sequences_list = zip(*batch)
        sequences_list = [pack_sentence(sequences) for sequences in sequences_list]
        return tuple(sequences_list)

    def __call__(self, batch):
        return self.pad_collate(batch)
