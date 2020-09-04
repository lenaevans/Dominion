import numpy as np

from keras.models import Model
from keras.layers import Input, Dense, Dropout, GlobalAveragePooling1D
from keras.layers.merge import concatenate
from keras.optimizers import Adam
from nn.network import Network

from typing import List


class DominionNetworkNoRecurrent(Network):
    def __init__(self, id=""):
        self.id = id

        cards = Input(shape=(None, 328), name="hand")
        game_state = Input(shape=(5591,), name="game_state")
        # feature extraction
        layer = GlobalAveragePooling1D()(cards)
        layer = Dropout(0.2)(layer)
        layer = concatenate([layer, game_state])
        layer = Dense(500)(layer)
        layer = Dropout(0.2)(layer)
        layer = Dense(250)(layer)
        layer = Dropout(0.2)(layer)
        layer = Dense(120)(layer)
        layer = Dropout(0.2)(layer)
        layer = Dense(60)(layer)
        layer = Dropout(0.2)(layer)
        layer = Dense(30)(layer)
        layer = Dropout(0.2)(layer)
        output = Dense(1, activation="tanh", name="win_est")(layer)
        aux_output = Dense(1, activation="linear", name="vp_est")(layer)
        model = Model(inputs=[cards, game_state], outputs=[output, aux_output])
        print(model.summary())

        model.compile(
            loss=["mean_squared_error", "mean_squared_error"],
            optimizer=Adam(learning_rate=0.00001),
            metrics=["accuracy"],
        )

        super().__init__(model)

    def get_save_file(self):
        return "model_128-4_64_64_A{}.h5".format(self.id)

    def get_name(self):
        return "A" + str(self.id)

    def update(
        self,
        hand: List[List[List[float]]],
        game_state: List[List[float]],
        rewards: List[float],
        points: List[float],
    ):
        self.model.train_on_batch(
            {"hand": np.array(hand), "game_state": np.array(game_state)},
            {"win_est": np.array(rewards), "vp_est": np.array(points)},
        )
