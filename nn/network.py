import numpy as np
from keras.models import load_model
from abc import ABC, abstractmethod
import os
from typing import List

save_dir = "../saved_models"


class Network(ABC):
    def __init__(self, model):
        self.model = model
        self.load()

        self.losses = np.zeros(5)
        self.num_losses = 0

    def eval_position(self, board_state):

        hand = board_state[0]
        if len(hand) == 0:
            print("Empty hand")
            hand = np.zeros((1, 33))

        hand_one_hot = board_state[1]
        if len(hand_one_hot) == 0:
            hand_one_hot = [0]

        pred = self.model.predict(
            [
                np.array([hand]),
                np.array([hand_one_hot]),
                np.array([board_state[2]]),
                np.array([board_state[3]]),
                np.array([board_state[4]]),
                np.array([board_state[5]]),
            ]
        )
        print(10 * pred[1][0][0])
        return pred[0][0][0]

    def update(
        self,
        hand: List[List[List[float]]],
        hand_one_hot: List[List[int]],
        kingdom: List[List[List[float]]],
        kingdom_one_hot: List[List[int]],
        opponent_states: List[List[List[float]]],
        game_state: List[List[float]],
        rewards: List[float],
        points: List[float],
    ):
        f = self.model.train_on_batch(
            {
                "hand": np.array(hand),
                "hand_one_hot": np.array(hand_one_hot),
                "kingdom": np.array(kingdom),
                "kingdom_one_hot": np.array(kingdom_one_hot),
                "opponent": np.array(opponent_states),
                "game_state": np.array(game_state),
            },
            {"win_est": np.array(rewards), "vp_est": np.array(points)},
            reset_metrics=True,
        )
        self.losses += np.array(f)
        self.num_losses += 1

    def get_summary(self):
        print(self.model.metrics_names)
        print(self.losses / self.num_losses)
        self.losses = np.zeros(5)
        self.num_losses = 0

    def load(self):
        model_path = os.path.join(save_dir, self.get_save_file())
        if os.path.isfile(model_path):
            self.model.load_weights(model_path, skip_mismatch=True)
            print("Loaded model from", model_path)

    def save(self):
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)
        model_path = os.path.join(save_dir, self.get_save_file())
        self.model.save(model_path)

    @abstractmethod
    def get_save_file(self):
        pass

    @abstractmethod
    def get_name(self):
        pass
