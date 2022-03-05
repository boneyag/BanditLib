import numpy as np
from Users.LearningUsers import LinUser, norm2, norm_matrix, get_eigen_vec
import matplotlib.pyplot as plt
import argparse


class AES:
    def __init__(self, feature_dim, delta=0.1):
        self.d = feature_dim
        self.x = np.zeros(self.d)        # center
        self.P = np.identity(n=self.d)   # shape
        self.I = np.identity(n=self.d)
        self.theta = norm2(np.random.randn(self.d))
        self.m = None
        self.delta = delta
        self.t = 1
        self.T = 1

    def gen_rand_direction(self):
        return norm2(np.random.randn(self.d))

    def reset(self):
        self.x = np.zeros(self.d)  # center
        self.P = np.identity(n=self.d)  # shape
        self.t = 1
        self.T = 1

    def check_alpha(self, user, left, right, g):
        alpha = - (self.t ** user.gamma * np.sqrt(2 * np.log(1 / self.delta))) \
                * norm_matrix(left - right, user.VInv) / norm_matrix(g, self.P)
        return alpha

    def prepare_user2(self, user):

        winner = get_eigen_vec(user.V, option='min')
        user.get_reward(winner)
        self.regret.append(1 - np.dot(user.theta_star, winner))

    def prepare_user(self, user, T0=0):
        for i in range(T0):
            winner = self.I[i % self.d]
            user.get_reward(winner)
            self.regret.append(1 - np.dot(user.theta_star, winner))
        self.t += T0

    def recommend(self, user=None):

        lambda12, u12 = get_eigen_vec(self.P, option='max2', return_eigen_value=True)

        g = np.dot(self.x, u12[1]) * u12[0] - np.dot(self.x, u12[0]) * u12[1]
        if np.linalg.norm(g) < 1e-6:
            g = (u12[0] + u12[1]) / np.sqrt(2)
        else:
            g = norm2(g)

        left, right = g, -g
        # q = 0.1
        # left = np.sqrt(1-q**2) * self.x + q * g
        # right = np.sqrt(1-q**2) * self.x - q * g

        alpha = self.check_alpha(user, left=left, right=right, g=2*g)

        self.t += 1
        return left, right, alpha

    def update(self, left, right, alpha, rewards):
        if rewards[0] < rewards[1]:
            g = left - right
        else:
            g = - left + right
        # do cut
        gt = g / norm_matrix(g, self.P)
        self.x -= (1 + self.d * alpha) / (1 + self.d) * (gt @ self.P)
        self.P -= 2 * (1 + self.d * alpha) / (1 + self.d) / (1 + alpha) * np.outer((gt @ self.P), (gt @ self.P))
        self.P *= (self.d ** 2 * (1 - alpha ** 2) / (self.d ** 2 - 1))

    def simulate(self, user, T=1000, T0=100, delta=0.1, cut_thres=1.0, plot=False, verbose=False):

        self.T = T
        self.delta = delta
        self.regret = []
        self.alpha = []
        self.cut = []
        self.prepare_user(user, T0)
        for i in range(T-T0):
            if verbose:
                print(self.t, np.linalg.eigh(user.V)[0])
            left, right, alpha = self.recommend(user=user)
            self.alpha.append(alpha)
            right_score, winner, _ = user.get_winner(left, right, learning=True)
            if alpha > - cut_thres / self.d:
                self.cut.append(i)
                if verbose:
                    print('proposed arms:', left, right)
                    print('cutting direction:', left - right)
                    print('current center:', self.x)
                    # print('check <g,x>:', (left - right) @ self.x)
                    print('current shape:', np.linalg.eigh(self.P)[0])
                self.update(left, right, alpha, [1 - right_score, right_score])
                if verbose:
                    print('after center:', self.x)
                    print('after shape:', np.linalg.eigh(self.P)[0])
                user.getReward(winner)
                self.regret.append(1)
            else:
                winner = norm2(self.x)
                user.getReward(winner)
                self.regret.append(1 - np.dot(user.theta_star, norm2(winner)))
        if plot:
            plt.plot(np.cumsum(self.regret))
            plt.show()

    def simulate2(self, user, T=10000, T0=1000, delta=0.1, cut_thres=1.0, plot=False, verbose=False):

        self.T = T
        self.delta = delta
        self.regret = []
        self.alpha = []
        self.cut = []

        for i in range(T):
            if verbose:
                print(self.t, np.linalg.eigh(user.V)[0])
            left, right, alpha = self.recommend(user=user)
            self.alpha.append(alpha)
            right_score, winner, _ = user.get_winner(left, right, learning=True)
            if alpha > - cut_thres / self.d:
                self.cut.append(i)
                if verbose:
                    print('proposed arms:', left, right)
                    print('cutting direction:', left - right)
                    print('current center:', self.x)
                    # print('check <g,x>:', (left - right) @ self.x)
                    print('current shape:', np.linalg.eigh(self.P)[0])
                self.update(left, right, alpha, [1 - right_score, right_score])
                if verbose:
                    print('after center:', self.x)
                    print('after shape:', np.linalg.eigh(self.P)[0])
                user.get_reward(winner)
                self.regret.append(1 - np.dot(user.theta_star, (left+right / 2)))
            elif self.t < T0:
                self.prepare_user2(user)
            else:
                winner = norm2(self.x)
                user.get_reward(winner)
                self.regret.append(1 - np.dot(user.theta_star, winner))
        if plot:
            plt.plot(np.cumsum(self.regret))
            plt.show()


if __name__ == '__main__':

    # environment settings
    parser = argparse.ArgumentParser(description="BAIR test")
    parser.add_argument('--rho', default=1)
    parser.add_argument('--alpha', default=1)
    parser.add_argument('--dp', default=1)
    parser.add_argument('--m', default=1)
    parser.add_argument('--min_gap', default=0.5)
    parser.add_argument('--num_trials', default=1000)
    parser.add_argument('--T', default=1000)
    parser.add_argument('--alg', default='bair')
    parser.add_argument('--delta', default=0.1)
    parser.add_argument('--K', default=2)
    parser.add_argument('--N0', default=1)
    parser.add_argument('--max_ite', default=1000)

    args = vars(parser.parse_args())

    d, T, T0, delta, gamma, cut_thres = 5, 10000, 1000, 0.2, 0.2, 1.0
    user = LinUser(feature_dim=d, V0=1.0 * np.identity(n=d))
    ell = AES(feature_dim=d)
    rand_seq1 = [(int(np.random.rand() > 0.5) * 2 - 1) for t in range(T + 1)]
    rand_seq2 = []
    for i in range(len(rand_seq1)):
        rand_seq2.append(rand_seq1[i] * (int(np.random.rand() > 0.2) * 2 - 1))
    regret = []
    fig, ax = plt.subplots()
    start, colors, gamma = 0, ['r-.', 'b-.', 'g-.'], [0.2, 0.1, 0.0]
    for i in range(len(gamma)):
        user.reset()
        ell.reset()
        user.set_beta(beta_left=[t ** gamma[i] * rand_seq1[t] for t in range(1, T + 1)],
                      beta_right=[t ** gamma[i] * rand_seq2[t] for t in range(1, T + 1)])
        ell.simulate2(user=user, T=T, T0=T0, delta=delta, cut_thres=cut_thres, verbose=False)
        # dbgd.simulate(user=user, prepare_user=T0, T=T)
        regret.append(np.cumsum(ell.regret))
        ax.plot(regret[-1][start:], colors[i], label='BES gamma=' + str(gamma[i]))

    ax.set_title('Regret curves of AES for learning users')
    ax.set_xlabel("t")
    ax.set_ylabel("Regret(t)")
    ax.legend(fontsize=12)
    plt.show()

