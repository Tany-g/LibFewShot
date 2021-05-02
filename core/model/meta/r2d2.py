import torch
from torch import nn

from core.utils import accuracy
from .meta_model import MetaModel


def computeGramMatrix(A, B):
    """
    Constructs a linear kernel matrix between A and B.
    We assume that each row in A and B represents a d-dimensional feature vector.

    Parameters:
      A:  a (n_batch, n, d) Tensor.
      B:  a (n_batch, m, d) Tensor.
    Returns: a (n_batch, n, m) Tensor.
    """

    assert (A.dim() == 3)
    assert (B.dim() == 3)
    assert (A.size(0) == B.size(0) and A.size(2) == B.size(2))

    return torch.bmm(A, B.transpose(1, 2))


def binv(b_mat):
    """
    Computes an inverse of each matrix in the batch.
    Pytorch 0.4.1 does not support batched matrix inverse.
    Hence, we are solving AX=I.

    Parameters:
      b_mat:  a (n_batch, n, n) Tensor.
    Returns: a (n_batch, n, n) Tensor.
    """

    id_matrix = b_mat.new_ones(b_mat.size(-1)).diag().expand_as(b_mat).to(b_mat.device)
    b_inv, _ = torch.solve(id_matrix, b_mat)

    return b_inv


def one_hot(indices, depth):
    """
    Returns a one-hot tensor.
    This is a PyTorch equivalent of Tensorflow's tf.one_hot.

    Parameters:
      indices:  a (n_batch, m) Tensor or (m) Tensor.
      depth: a scalar. Represents the depth of the one hot dimension.
    Returns: a (n_batch, m, depth) Tensor or (m, depth) Tensor.
    """

    encoded_indicie = torch.zeros(indices.size() + torch.Size([depth])).to(indices.device)
    index = indices.view(indices.size() + torch.Size([1]))
    encoded_indicie = encoded_indicie.scatter_(1, index, 1)

    return encoded_indicie


class R2D2_Layer(nn.Module):
    """
    ICLR 2019: Meta-learning with differentiable closed-form solvers
    https://arxiv.org/abs/1805.08136
    """

    def __init__(self, way_num=5, shot_num=5):
        super(R2D2_Layer, self).__init__()
        self.way_num = way_num
        self.shot_num = shot_num
        self.register_parameter('alpha', nn.Parameter(torch.tensor([1.])))
        self.register_parameter('beta', nn.Parameter(torch.tensor([0.])))
        self.register_parameter('gamma', nn.Parameter(torch.tensor([50.])))

    def forward(self, query, support, support_target):
        tasks_per_batch = query.size(0)
        n_support = support.size(1)
        support_target = support_target.squeeze()

        assert (query.dim() == 3)
        assert (support.dim() == 3)
        assert (query.size(0) == support.size(0) and query.size(2) == support.size(2))
        assert (n_support == self.way_num * self.shot_num)  # n_support must equal to n_way * n_shot

        support_labels_one_hot = one_hot(support_target.view(tasks_per_batch * n_support), self.way_num)
        support_labels_one_hot = support_labels_one_hot.view(tasks_per_batch, n_support, self.way_num)

        id_matrix = torch.eye(n_support).expand(tasks_per_batch, n_support, n_support).to(query.device)

        # Compute the dual form solution of the ridge regression.
        # W = X^T(X X^T - lambda * I)^(-1) Y
        ridge_sol = computeGramMatrix(support, support) + self.gamma * id_matrix
        ridge_sol = binv(ridge_sol)
        ridge_sol = torch.bmm(support.transpose(1, 2), ridge_sol)
        ridge_sol = torch.bmm(ridge_sol, support_labels_one_hot)

        # Compute the classification score.
        # score = W X
        logit = torch.bmm(query, ridge_sol)
        logit = self.alpha * logit + self.beta
        return logit, ridge_sol


class R2D2(MetaModel):
    def __init__(self, way_num, shot_num, query_num, feature, device):
        super(R2D2, self).__init__(way_num, shot_num, query_num, feature, device)
        self.loss_func = nn.CrossEntropyLoss()
        self.classifier = R2D2_Layer(self.way_num, self.shot_num)
        self._init_network()

    def set_forward(self, batch, ):
        image, global_target = batch
        image = image.to(self.device)

        feat = self.emb_func(image)
        support_feat, query_feat, support_target, query_target = self.split_by_episode(feat, mode=1)
        output, weight = self.classifier(query_feat, support_feat, support_target)

        output = output.contiguous().view(-1, self.way_num)
        acc = accuracy(output.squeeze(), query_target.contiguous().reshape(-1))
        return output, acc

    def set_forward_loss(self, batch, ):
        image, global_target = batch
        image = image.to(self.device)

        feat = self.emb_func(image)
        support_feat, query_feat, support_target, query_target = self.split_by_episode(feat, mode=1)
        output, weight = self.classifier(query_feat, support_feat, support_target)

        output = output.contiguous().view(-1, self.way_num)
        loss = self.loss_func(output, query_target.contiguous().reshape(-1))
        acc = accuracy(output.squeeze(), query_target.contiguous().reshape(-1))
        return output, acc, loss

    def train_loop(self, emb_support, support_target, W):
        raise NotImplementedError

    def test_loop(self, *args, **kwargs):
        raise NotImplementedError

    def set_forward_adaptation(self, *args, **kwargs):
        raise NotImplementedError
