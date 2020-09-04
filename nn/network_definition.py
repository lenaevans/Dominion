from keras.models import Model
from keras.layers import Bidirectional, LSTM, Input, Dense, Dropout, Embedding
from keras.layers.merge import concatenate
from keras.optimizers import Adam
from nn.network import Network


class DominionNetwork(Network):
    def __init__(self, id=""):
        self.id = id

        cards_input = Input(shape=(None, 33), name="hand")
        card_one_hot = Input(shape=(None,), name="hand_one_hot", dtype="int32")
        kingdom_input = Input(shape=(None, 33), name="kingdom")
        kingdom_one_hot = Input(shape=(None,), name="kingdom_one_hot", dtype="int32")
        opponent_input = Input(shape=(None, 5), name="opponent")
        game_state = Input(shape=(10,), name="game_state")

        embed = Embedding(300, 50, input_length=card_one_hot.shape[1])

        cards_embed = embed(card_one_hot)
        kingdom_embed = embed(kingdom_one_hot)

        cards_embed = Bidirectional(LSTM(25, return_sequences=True))(cards_embed)
        cards_embed = Dropout(0.2)(cards_embed)
        cards_embed = Bidirectional(LSTM(12))(cards_embed)
        cards_embed = Dropout(0.2)(cards_embed)

        kingdom_embed = Bidirectional(LSTM(25, return_sequences=True))(kingdom_embed)
        kingdom_embed = Dropout(0.2)(kingdom_embed)
        kingdom_embed = Bidirectional(LSTM(12))(kingdom_embed)
        kingdom_embed = Dropout(0.2)(kingdom_embed)

        cards = Bidirectional(LSTM(25, return_sequences=True))(cards_input)
        cards = Dropout(0.2)(cards)
        cards = Bidirectional(LSTM(12))(cards)
        cards = Dropout(0.2)(cards)

        kingdom = Bidirectional(LSTM(25, return_sequences=True))(kingdom_input)
        kingdom = Dropout(0.2)(kingdom)
        kingdom = Bidirectional(LSTM(12))(kingdom)
        kingdom = Dropout(0.2)(kingdom)

        opponent = Bidirectional(LSTM(25, return_sequences=True))(opponent_input)
        opponent = Dropout(0.2)(opponent)
        opponent = Bidirectional(LSTM(12))(opponent)
        opponent = Dropout(0.2)(opponent)

        # feature extraction
        layer = concatenate(
            [cards_embed, cards, kingdom_embed, kingdom, opponent, game_state]
        )
        layer = Dense(100)(layer)
        layer = Dropout(0.2)(layer)
        layer = Dense(50)(layer)
        layer = Dropout(0.2)(layer)
        layer = Dense(25)(layer)
        layer = Dropout(0.2)(layer)
        output = Dense(1, activation="tanh", name="win_est")(layer)
        aux_output = Dense(1, activation="linear", name="vp_est")(layer)
        model = Model(
            inputs=[
                cards_input,
                card_one_hot,
                kingdom_input,
                kingdom_one_hot,
                opponent_input,
                game_state,
            ],
            outputs=[output, aux_output],
        )
        print(model.summary())

        model.compile(
            loss={"win_est": "mean_squared_error", "vp_est": "mean_squared_error"},
            loss_weights={"win_est": 1.0, "vp_est": 0.001},
            optimizer=Adam(learning_rate=0.0001),
            metrics=["accuracy"],
        )

        super().__init__(model)

    def get_save_file(self):
        return "model_128-4_64_64_B{}.h5".format(self.id)

    def get_name(self):
        return "B" + str(self.id)
