from torch import nn
from torch.nn import functional as F
import torch


class MoviePredict(nn.Module):
    def __init__(self, voca_num, actor_num, director_num, category_num, country_num,
            embedding_dim=64, filter_num=32, filters=[1,2,3,4],
            dropout=0.3, embedding_dropout=0.1):

        super(MoviePredict, self).__init__()
        
        self.embedding_dim = embedding_dim
        self.word_embedding = nn.Embedding(voca_num, embedding_dim, padding_idx=0)
        self.actor_embedding = nn.Embedding(actor_num, embedding_dim, padding_idx=0)
        self.director_embedding = nn.Embedding(director_num, embedding_dim, padding_idx=0)
        self.category_embedding = nn.Embedding(category_num, embedding_dim)
        self.country_embedding = nn.Embedding(country_num, embedding_dim)

        self.actor_linear = nn.Linear(embedding_dim, embedding_dim, bias=False)
        self.director_linear = nn.Linear(embedding_dim, embedding_dim, bias=False)
        self.graph_linear = nn.Linear(embedding_dim, embedding_dim)
        self.graph_layernorm = nn.LayerNorm(embedding_dim)
        self.graph_batchnorm = nn.BatchNorm1d(embedding_dim)

        self.meta_linear = nn.Linear(embedding_dim*2, embedding_dim)
        self.meta_norm = nn.BatchNorm1d(embedding_dim)

        self.sentence_conv = nn.ModuleList(
            [nn.Conv1d(1, filter_num, (filter_, embedding_dim)) for filter_ in filters])
        self.conv_norm = nn.BatchNorm1d(filter_num)

        # self.num_layers = 4
        # self.gru = nn.GRU(embedding_dim, embedding_dim, num_layers=self.num_layers, batch_first=True, bidirectional=True)
        
        self.output_linear = nn.Linear(filter_num*len(filters) + embedding_dim*3, 3)
        # self.output_linear = nn.Linear(embedding_dim*2 + embedding_dim*3, 3)

        self.dropout = nn.Dropout(dropout)

    def forward(self, actors, directors, categories, countries, story):
        word_embs = self.word_embedding(story)
        actor_embs = self.actor_embedding(actors)
        director_embs = self.director_embedding(directors)
        category_emb = self.category_embedding(categories).mean(dim=1)
        country_emb = self.country_embedding(countries).mean(dim=1)

        # conv => norm => activation => dropout => pool
        # sentence_vector = [self.conv_norm(conv(word_embs.unsqueeze(1)).squeeze(3)) for conv in self.sentence_conv]
        sentence_vector = [conv(word_embs.unsqueeze(1)).squeeze(3) for conv in self.sentence_conv]
        sentence_vector = [self.dropout(torch.relu(out)) for out in sentence_vector]
        sentence_vector = [F.adaptive_max_pool1d(out, 1).squeeze(2) for out in sentence_vector]
        sentence_vector = torch.cat(sentence_vector, dim=1)

        # _, sentence_vector = self.gru(word_embs)
        # sentence_vector = sentence_vector.view(self.num_layers, 2, -1, self.embedding_dim)
        # sentence_vector = sentence_vector[-1].transpose(0, 1)
        # sentence_vector = sentence_vector.contiguous().view(-1, 2*self.embedding_dim)
        
        actor_embs = self.dropout(torch.relu(self.actor_linear(actor_embs)))
        director_embs = self.dropout(torch.relu(self.director_linear(actor_embs)))
        # graph_vector = self.graph_layernorm(actor_embs.mean(dim=1) + director_embs.mean(dim=1))
        graph_vector = actor_embs.mean(dim=1) + director_embs.mean(dim=1)
        # graph_vector = self.dropout(torch.relu(self.graph_batchnorm(self.graph_linear(graph_vector))))
        graph_vector = self.dropout(torch.relu(self.graph_linear(graph_vector)))

        output = torch.cat([sentence_vector, graph_vector, category_emb, country_emb], dim=1)
        output = self.output_linear(output)
        return output
