from __future__ import annotations
from typing import Dict, List

import Game
import Player
from utils import catinlist, getcard, players_around
from nn.network_definition import DominionNetwork


class Card:
    def __init__(
        self,
        name: str,
        categories: List[str],
        cost: int,
        buypower: int = 0,
        vpoints: int = 0,
        actions: int = 0,
        buys: int = 0,
        coins: int = 0,
        draws: int = 0,
    ):
        self.name = name
        self.categories = categories
        self.cost = cost
        self.buys = buys
        self.actions = actions
        self.buypower = buypower
        self.coins = coins
        self.vpoints = vpoints
        self.draws = draws

        for category in self.categories:
            assert category in [
                "curse",
                "victory",
                "action",
                "coin",
                "attack",
                "reaction",
                "duration",
            ]

    def get_points(self, player: Player.Player):
        return self.vpoints

    def onbuy(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        return

    def ongain(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        return

    def ontrash(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        return

    def ondiscard(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        return

    def onuse(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        player.purse += self.buypower
        return

    def react(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        return False

    def use(self, player: Player.Player, trash: List[Card]):
        player.played.append(self)
        player.hand.remove(self)

    def augment(self, player: Player.Player, draw: bool = True):
        player.actions += self.actions
        player.buys += self.buys
        player.purse += self.coins
        if draw:
            for i in range(self.draws):
                player.draw()

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        return 0


class Copper(Card):
    def __init__(self):
        Card.__init__(self, "Copper", ["coin"], cost=0, buypower=1)


class Silver(Card):
    def __init__(self):
        Card.__init__(self, "Silver", ["coin"], cost=3, buypower=2)


class Gold(Card):
    def __init__(self):
        Card.__init__(self, "Gold", ["coin"], cost=6, buypower=3)


class Platinum(Card):
    def __init__(self):
        Card.__init__(self, "Platinum", ["coin"], cost=9, buypower=5)


class IllGottenGains(Card):
    def __init__(self):
        Card.__init__(self, "Ill-Gotten Gains", ["coin"], cost=5, buypower=1)

    def ongain(
        self,
        this_player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        for player in players_around(game.players, this_player, inclusive=False):
            if len(game.supply["Curse"]) > 0:
                player.discard.append(game.supply["Curse"].pop())

    @staticmethod
    def yes_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        player.hand.append(game.supply["Copper"].pop())
        return 0

    @staticmethod
    def no_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        return 0

    def onuse(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        player.purse += self.buypower

        if len(game.supply["Copper"]) > 0:
            if player.yesnoinput(
                "Would you like to gain a copper to your hand?",
                game,
                network,
                callbacks={
                    True: IllGottenGains.yes_callback,
                    False: IllGottenGains.no_callback,
                },
                mock=mock,
            ):
                IllGottenGains.yes_callback(player, game, network, mock)


class Treasure_Trove(Card):
    def __init__(self):
        Card.__init__(self, "Treasure Trove", ["coin"], cost=5, buypower=2)

    def onuse(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        player.purse += self.buypower

        if len(game.supply["Gold"]) > 0:
            player.discard.append(game.supply["Gold"].pop())
        if len(game.supply["Copper"]) > 0:
            player.discard.append(game.supply["Copper"].pop())


class Cache(Card):
    def __init__(self):
        Card.__init__(self, "Cache", ["coin"], cost=5, buypower=3)

    def ongain(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        for _ in range(2):
            if len(game.supply["Copper"]) > 0:
                player.discard.append(game.supply["Copper"].pop())


class Bank(Card):
    def __init__(self):
        Card.__init__(self, "Bank", ["coin"], cost=7)

    def onuse(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        player.purse += 1
        for card in player.played:
            if "coin" in card.categories:
                player.purse += 1


class Harem(Card):
    def __init__(self):
        Card.__init__(self, "Harem", ["coin", "victory"], cost=6, buypower=2, vpoints=2)


class Curse(Card):
    def __init__(self):
        Card.__init__(self, "Curse", ["curse"], cost=0, vpoints=-1)


class Estate(Card):
    def __init__(self):
        Card.__init__(self, "Estate", ["victory"], cost=2, vpoints=1)


class Duchy(Card):
    def __init__(self):
        Card.__init__(self, "Duchy", ["victory"], cost=5, vpoints=3)


class Province(Card):
    def __init__(self):
        Card.__init__(self, "Province", ["victory"], cost=8, vpoints=6)


class Colony(Card):
    def __init__(self):
        Card.__init__(self, "Colony", ["victory"], cost=11, vpoints=10)


class Gardens(Card):
    def __init__(self):
        Card.__init__(self, "Gardens", ["victory"], cost=4)

    def get_points(self, player: Player.Player):
        return len(player.stack()) // 10


class Duke(Card):
    def __init__(self):
        Card.__init__(self, "Duke", ["victory"], cost=5)

    def get_points(self, player: Player.Player):
        duchies = 0
        for card in player.stack():
            if card.name == "Duchy":
                duchies += 1
        return duchies


class Feodum(Card):
    def __init__(self):
        Card.__init__(self, "Feodum", ["victory"], cost=4)

    def get_points(self, player: Player.Player):
        silvers = 0
        for card in player.stack():
            if card.name == "Silver":
                silvers += 1
        return silvers // 3

    def ontrash(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        for _ in range(3):
            if len(game.supply["Silver"]) > 0:
                player.discard.append(game.supply["Silver"].pop())


class Tunnel(Card):
    def __init__(self):
        Card.__init__(self, "Tunnel", ["victory", "reaction"], cost=3, vpoints=2)

    def ondiscard(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        if len(game.supply["Gold"]) > 0:
            player.discard.append(game.supply["Gold"].pop())


class Silk_Road(Card):
    def __init__(self):
        Card.__init__(self, "Silk Road", ["victory"], cost=4)

    def get_points(self, player: Player.Player):
        victory_cards = 0
        for card in player.stack():
            if "victory" in card.categories:
                victory_cards += 1
        return victory_cards // 4


class Fairgrounds(Card):
    def __init__(self):
        Card.__init__(self, "Fairgrounds", ["victory"], cost=6)

    def get_points(self, player: Player.Player):
        card_names = set()
        for card in player.stack():
            card_names.add(card.name)
        return 2 * len(card_names) // 5


class Farmland(Card):
    def __init__(self):
        Card.__init__(self, "Farmland", ["victory"], cost=6, vpoints=2)

    def onbuy(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ):
        if len(player.hand) > 0:
            trashcard = player.choose_discard(
                player.name + ", choose a card from your hand to discard: ",
                game,
                network,
                trash_card=True,
                mock=mock,
            )
            c = getcard(trashcard, game.supply, player.hand, "your hand")
            if c:
                game.trash.append(c)
                c.ontrash(player, game, network, mock)
                player.hand.remove(c)
            else:
                raise ValueError()
            player.gain_card(
                game, network, c.cost + 2, exact=True, mock=mock,
            )


class Great_Hall(Card):
    def __init__(self):
        Card.__init__(
            self,
            "Great Hall",
            ["victory", "action"],
            cost=3,
            vpoints=1,
            draws=1,
            actions=1,
        )


class Mill(Card):
    def __init__(self):
        Card.__init__(
            self, "Mill", ["victory", "action"], cost=4, vpoints=1, draws=1, actions=1
        )

    @staticmethod
    def yes_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        for _ in range(2):
            dis_card = player.choose_discard(
                player.name + ", choose a card from your hand to discard: ",
                game,
                network,
                mock=mock,
            )
            c = getcard(dis_card, game.supply, player.hand, "your hand")
            if c:
                player.discard.append(c)
                c.ondiscard(player, game, network, mock)
                player.hand.remove(c)
            else:
                raise ValueError()
        player.purse += 2
        return 0

    @staticmethod
    def no_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        return 0

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if len(player.hand) > 2:
            if player.yesnoinput(
                "Would you like to discard 2 cards for 2 coins?",
                game,
                network,
                callbacks={True: Mill.yes_callback, False: Mill.no_callback},
                mock=mock,
            ):
                Mill.yes_callback(player, game, network, mock)
        return 0


class Nobles(Card):
    def __init__(self):
        Card.__init__(self, "Nobles", ["victory", "action"], cost=6, vpoints=2)

    @staticmethod
    def yes_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        if not mock:
            player.draw()
            player.draw()
            player.draw()
        return 3

    @staticmethod
    def no_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        player.actions += 2
        return 0

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if player.yesnoinput(
            "Would you like to draw three cards?",
            game,
            network,
            callbacks={True: Nobles.yes_callback, False: Nobles.no_callback},
            mock=mock,
        ):
            return Nobles.yes_callback(player, game, network, mock)
        else:
            return Nobles.no_callback(player, game, network, mock)


class Woodcutter(Card):
    def __init__(self):
        Card.__init__(self, "Woodcutter", ["action"], cost=3, buys=1, coins=2)


class Smithy(Card):
    def __init__(self):
        Card.__init__(self, "Smithy", ["action"], cost=4, draws=3)


class Laboratory(Card):
    def __init__(self):
        Card.__init__(self, "Laboratory", ["action"], cost=5, actions=1, draws=2)


class Village(Card):
    def __init__(self):
        Card.__init__(self, "Village", ["action"], cost=3, actions=2, draws=1)


class Festival(Card):
    def __init__(self):
        Card.__init__(self, "Festival", ["action"], cost=5, actions=2, buys=1, coins=2)


class Market(Card):
    def __init__(self):
        Card.__init__(
            self, "Market", ["action"], cost=5, draws=1, actions=1, buys=1, coins=1
        )


class Chancellor(Card):
    def __init__(self):
        Card.__init__(self, "Chancellor", ["action"], cost=3, coins=2)

    @staticmethod
    def yes_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        player.discard = player.discard + player.deck
        player.deck = []
        return 0

    @staticmethod
    def no_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        return 0

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if player.yesnoinput(
            "Would you like to discard your entire deck?",
            game,
            network,
            callbacks={True: Chancellor.yes_callback, False: Chancellor.no_callback},
            mock=mock,
        ):
            Chancellor.yes_callback(player, game, network, mock)
        return 0


class Workshop(Card):
    def __init__(self):
        Card.__init__(self, "Workshop", ["action"], cost=3)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        player.gain_card(game, network, 4, mock=mock)
        return 0


class Moneylender(Card):
    def __init__(self):
        Card.__init__(self, "Moneylender", ["action"], cost=4)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:

        has_copper = False
        for card in player.hand:
            if "Copper" in card.name:
                has_copper = True
        if has_copper:
            c = getcard("Copper", game.supply, player.hand, "your hand")
            game.trash.append(c)
            player.hand.remove(c)
            player.purse += 3
        return 0


class Chapel(Card):
    def __init__(self):
        Card.__init__(self, "Chapel", ["action"], cost=2)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        trashed = 0
        while trashed < 4 and len(player.hand) > 0:
            trashcard = player.choose_discard(
                player.name + ", choose a card from your hand to discard: ",
                game,
                network,
                optional=True,
                trash_card=True,
                mock=mock,
            )
            if trashcard is None:
                break
            c = getcard(trashcard, game.supply, player.hand, "your hand")
            if c:
                game.trash.append(c)
                c.ontrash(player, game, network, mock)
                player.hand.remove(c)
                trashed += 1
            else:
                raise ValueError()
        return 0


class Cellar(Card):
    def __init__(self):
        Card.__init__(self, "Cellar", ["action"], cost=2, actions=1)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        discarded = 0
        while len(player.hand) > 0:
            dis_card = player.choose_discard(
                player.name + ", choose a card from your hand to discard: ",
                game,
                network,
                additional_draw=1,
                optional=True,
                mock=mock,
            )
            if dis_card is None:
                break
            c = getcard(dis_card, game.supply, player.hand, "your hand")
            if c:
                player.discard.append(c)
                c.ondiscard(player, game, network, mock)
                player.hand.remove(c)
                discarded += 1
        for _ in range(discarded):
            if not mock:
                player.draw()
        return discarded


class Remodel(Card):
    def __init__(self):
        Card.__init__(self, "Remodel", ["action"], cost=4)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if len(player.hand) > 0:
            this_card = player.choose_discard(
                player.name + ", choose a card from your hand to discard: ",
                game,
                network,
                trash_card=True,
                mock=mock,
            )
            if this_card:
                c = getcard(this_card, game.supply, player.hand, "your hand")
                game.trash.append(c)
                player.hand.remove(c)
                c.ontrash(player, game, network, mock)
                player.gain_card(
                    game, network, c.cost + 2, mock=mock,
                )
        return 0


class Adventurer(Card):
    def __init__(self):
        Card.__init__(self, "Adventurer", ["action"], cost=6)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        coins_added = 0
        if not mock:
            while (player.deck or player.discard) and coins_added < 2:
                player.draw()
                if "coin" in player.hand[-1].categories:
                    coins_added += 1
                else:
                    player.aside.append(player.hand.pop())
        return 2


class Feast(Card):
    def __init__(self):
        Card.__init__(self, "Feast", ["action"], cost=4)

    def use(self, player: Player.Player, trash: List[Card]):
        trash.append(self)
        player.hand.remove(self)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        player.gain_card(game, network, 5, mock=mock)
        return 0


class Mine(Card):
    def __init__(self):
        Card.__init__(self, "Mine", ["action"], cost=5)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if "coin" in catinlist(player.hand):
            this_card = player.choose_discard(
                player.name + ", choose a card from your hand to trash: ",
                game,
                network,
                constraint="coin",
                optional=True,
                trash_card=True,
                mock=mock,
            )
            if this_card:
                c = getcard(this_card, game.supply, player.hand, "your hand", ["coin"])
                if c:
                    game.trash.append(c)
                    c.ontrash(player, game, network, mock)
                    player.hand.remove(c)
                    player.gain_card(
                        game,
                        network,
                        c.cost + 3,
                        constraint="coin",
                        mock=mock,
                        destination="hand",
                    )
                else:
                    raise ValueError()
        return 0


class Library(Card):
    def __init__(self):
        Card.__init__(self, "Library", ["action"], cost=5)

    @staticmethod
    def yes_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        player.aside.append(player.hold.pop())
        return 0

    @staticmethod
    def no_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        player.hand.append(player.hold.pop())
        return 0

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if not mock:
            while (player.deck or player.discard) and len(player.hand) < 7:
                player.draw(player.hold)
                if "action" in player.hold[-1].categories:
                    if player.yesnoinput(
                        "You drew "
                        + player.hold[-1].name
                        + ".  Would you like to keep it?",
                        game,
                        network,
                        ", set it aside",
                        ", add to my hand",
                        callbacks={
                            True: Library.yes_callback,
                            False: Library.no_callback,
                        },
                        mock=mock,
                    ):
                        Library.yes_callback(player, game, network, mock)
                    else:
                        Library.no_callback(player, game, network, mock)
        return max(7 - len(player.hand), 0)


class Moat(Card):
    def __init__(self):
        Card.__init__(self, "Moat", ["action", "reaction"], cost=2, draws=2)

    def react(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> bool:
        player.show(lead="\n")
        return player.yesnoinput(
            player.name
            + ", you have a "
            + self.name
            + " in your hand.  Do you want to block the attack?",
            game,
            network,
            mock=mock,
        )


class Council_Room(Card):
    def __init__(self):
        Card.__init__(self, "Council Room", ["action"], cost=5, draws=4, buys=1)

    def play(
        self,
        this_player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        for player in players_around(game.players, this_player, inclusive=False):
            player.draw()
        return 0


class Witch(Card):
    def __init__(self):
        Card.__init__(self, "Witch", ["action", "attack"], cost=5, draws=2)

    def play(
        self,
        this_player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        for player in players_around(game.players, this_player, inclusive=False):
            if len(game.supply["Curse"]) > 0:
                if not mock:
                    for c in player.hand:
                        if c.react(player, game, network, mock):
                            break
                else:
                    player.discard.append(game.supply["Curse"].pop())
        return 0


class Bureaucrat(Card):
    def __init__(self):
        Card.__init__(self, "Bureaucrat", ["action", "attack"], cost=4)

    def play(
        self,
        this_player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if len(game.supply["Silver"]) > 0:
            this_player.deck.insert(0, game.supply["Silver"].pop())

        for player in players_around(game.players, this_player, inclusive=False):
            for c in player.hand:
                if c.react(player, game, network, mock) or mock:
                    break
            else:
                if "victory" in catinlist(player.hand):
                    putback = player.choose_discard(
                        player.name
                        + ", which victory card"
                        + " do you want to put on top of your deck?\n--> ",
                        game,
                        network,
                        constraint="victory",
                        ondeck=True,
                        mock=mock,
                    )
                    c = getcard(
                        putback, game.supply, player.hand, "your hand", ["victory"]
                    )
                    if c:
                        player.hand.remove(c)
                        player.deck.insert(0, c)
                    else:
                        raise ValueError()
                else:
                    player.show(lead="\n\n")
        return 0


class Militia(Card):
    def __init__(self):
        Card.__init__(self, "Militia", ["action", "attack"], cost=4, coins=2)

    def play(
        self,
        this_player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        for player in players_around(game.players, this_player, inclusive=False):
            has_moat = False
            if len(player.hand) > 3:
                for c in player.hand:
                    if c.react(player, game, network, mock) or mock:
                        has_moat = True
                        break
                else:
                    player.show(lead="\n\n")
                    while len(player.hand) > 3:
                        dis_card = player.choose_discard(
                            player.name + ", choose a card from your hand to discard: ",
                            game,
                            network,
                            mock=mock,
                        )

                        print("Discard " + dis_card)
                        if dis_card:
                            c = getcard(dis_card, game.supply, player.hand, "your hand")
                            if c:
                                player.hand.remove(c)
                                c.ondiscard(player, game, network, mock)
                                player.discard.append(c)
                            else:
                                raise ValueError()

            if (not mock) and (len(player.hand) > 3) and (not has_moat):
                raise ValueError()

        return 0


class Spy(Card):
    def __init__(self):
        Card.__init__(self, "Spy", ["action", "attack"], cost=4, draws=1, actions=1)

    @staticmethod
    def yes_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        player.discard.append(player.hold.pop())
        return 0

    @staticmethod
    def no_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        player.deck.insert(0, player.hold.pop())
        return 0

    def play(
        self,
        this_player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        for player in players_around(game.players, this_player, inclusive=True):
            for c in player.hand:
                if c.react(player, game, network, mock) or mock:
                    break
            else:
                player.draw(player.hold)
                if len(player.hold) != 1:
                    continue
                else:
                    this_player.hprint(
                        "The first card in the deck of "
                        + player.name
                        + " is "
                        + player.hold[0].name
                    )
                    if this_player.yesnoinput(
                        this_player.name
                        + ", do you want "
                        + player.name
                        + " to discard this?",
                        game,
                        network,
                        ", discard",
                        ", keep",
                        applyto=player,
                        callbacks={True: Spy.yes_callback, False: Spy.no_callback},
                        mock=mock,
                    ):
                        Spy.yes_callback(player, game, network, mock)
                    else:
                        Spy.no_callback(player, game, network, mock)
        return 0


class Thief(Card):
    def __init__(self):
        Card.__init__(self, "Thief", ["action", "attack"], cost=4)

    @staticmethod
    def yes_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        player.discard.append(player.hold.pop())
        return 0

    @staticmethod
    def no_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        game.trash.append(player.hold.pop())
        return 0

    def play(
        self,
        this_player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if not mock:
            for player in players_around(game.players, this_player, inclusive=False):
                has_reaction = False
                for c in player.hand:
                    if c.react(player, game, network, mock) or mock:
                        has_reaction = True
                if not has_reaction:
                    for i in range(2):
                        player.draw(player.hold)

                    coin_idx = []
                    for idx, card in enumerate(player.hold):
                        if "coin" in card.categories:
                            coin_idx.append(idx)
                        else:
                            player.hold.remove(card)
                            player.discard.append(card)

                    # TODO: Make this a model decision
                    if len(coin_idx) == 2:
                        if this_player.yesnoinput(
                            "Would you like to trash the other card?",
                            game,
                            network,
                            mock=mock,
                        ):
                            c = player.hold[coin_idx[0]]
                            player.hold.remove(c)
                            player.discard.append(c)
                        else:
                            c = player.hold[coin_idx[1]]
                            player.hold.remove(c)
                            player.discard.append(c)

                    this_player.hold.append(player.hold.pop())

                    if this_player.yesnoinput(
                        "Do you want to steal it?",
                        game,
                        network,
                        ", it's mine!",
                        ", leave it in the trash.",
                        callbacks={True: Thief.yes_callback, False: Thief.no_callback},
                        mock=mock,
                    ):
                        Thief.yes_callback(this_player, game, network, mock)
                    else:
                        Thief.no_callback(this_player, game, network, mock)

                    player.discard = player.discard + player.hold
                    player.hold = []
        return 0


class Throne_Room(Card):
    def __init__(self):
        Card.__init__(self, "Throne Room", ["action"], cost=4)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:

        d = 0
        choice = player.choose_action(game, network, mock=mock, optional=False)
        if choice:
            c = getcard(choice, game.supply, player.hand, " your hand", ["action"])
            c.use(player, game.trash)
            c.augment(player)
            d += c.play(player, game, network, mock)
            player.show()
            c.augment(player)
            d += c.play(player, game, network, mock)
        return d


class Poacher(Card):
    def __init__(self):
        Card.__init__(self, "Poacher", ["action"], cost=4, draws=1, actions=1, coins=1)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        empty_piles = 0
        for stack in game.supply:
            if len(game.supply[stack]) == 0:
                empty_piles += 1

        for _ in range(empty_piles):
            if len(player.hand) > 0:
                dis_card = player.choose_discard(
                    "choose a card from your hand to discard", game, network, mock=mock,
                )
                c = getcard(dis_card, game.supply, player.hand, "your hand")
                if c:
                    player.hand.remove(c)
                    c.ondiscard(player, game, network, mock)
                    player.discard.append(c)
                else:
                    raise ValueError()
        return 0


class Vassal(Card):
    def __init__(self):
        Card.__init__(self, "Vassal", ["action"], cost=3, coins=2)

    @staticmethod
    def yes_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        card = player.hold.pop()
        player.hand.append(card)
        card.augment(player)
        card.play(player, game, network, mock)
        return 0

    @staticmethod
    def no_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        card = player.hold.pop()
        player.discard.append(card)
        return 0

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if not mock:
            b = player.draw(player.hold)
            if not b:
                return 0
            if "action" in b.categories:
                if player.yesnoinput(
                    "Would you like to play " + b.name,
                    game,
                    network,
                    callbacks={True: Vassal.yes_callback, False: Vassal.no_callback},
                    mock=mock,
                ):
                    Vassal.yes_callback(player, game, network, mock)
                else:
                    Vassal.no_callback(player, game, network, mock)
        return 0


class Artisan(Card):
    def __init__(self):
        Card.__init__(self, "Artisan", ["action"], cost=6)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:

        player.gain_card(game, network, 5, mock=mock, destination="hand")

        dis_card = player.choose_discard(
            " which card do you want to put on top of your deck?\n--> ",
            game,
            network,
            ondeck=True,
            mock=mock,
        )
        c = getcard(dis_card, game.supply, player.hand, "your hand")
        player.hand.remove(c)
        player.deck.insert(0, c)
        return 0


class Courtyard(Card):
    def __init__(self):
        Card.__init__(self, "Courtyard", ["action"], cost=2, draws=3)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if len(player.hand) > 0:
            dis_card = player.choose_discard(
                " which card do you want to put on top of your deck?\n--> ",
                game,
                network,
                ondeck=True,
                mock=mock,
            )
            c = getcard(dis_card, game.supply, player.hand, "your hand")
            player.hand.remove(c)
            player.deck.insert(0, c)
        return 0


class Shanty_Town(Card):
    def __init__(self):
        Card.__init__(self, "Shanty Town", ["action"], cost=3, actions=2)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if "action" not in catinlist(player.hand):
            if not mock:
                player.draw()
                player.draw()
            return 2
        return 0


class Baron(Card):
    def __init__(self):
        Card.__init__(self, "Baron", ["action"], cost=4, buys=1)

    @staticmethod
    def yes_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        c = getcard("Estate", game.supply, player.hand, "your hand")
        if c:
            player.hand.remove(c)
            player.discard.append(c)
            player.purse += 4
        return 0

    @staticmethod
    def no_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        return 0

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        discarded = False

        for card in player.hand:
            if card.name == "Estate":
                if player.yesnoinput(
                    "discard estate?",
                    game,
                    network,
                    callbacks={True: Baron.yes_callback, False: Baron.no_callback},
                    mock=mock,
                ):
                    Baron.yes_callback(player, game, network, mock)
                    discarded = True
                    break

        if not discarded:
            if len(game.supply["Estate"]) > 0:
                player.discard.append(game.supply["Estate"].pop())

        return 0


class Conspirator(Card):
    def __init__(self):
        Card.__init__(self, "Conspirator", ["action"], cost=4, coins=2)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if player.actions_played > 2:
            if not mock:
                player.draw()
                player.actions += 1
            return 1
        return 0


class Ironworks(Card):
    def __init__(self):
        Card.__init__(self, "Ironworks", ["action"], cost=4)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        card = player.gain_card(game, network, 4, mock=mock)
        c = CardNameMap[card]

        drawn = 0
        if "action" in c.categories:
            player.actions += 1
        if "coin" in c.categories:
            player.purse += 1
        if "victory" in c.categories:
            drawn += 1
            if not mock:
                player.draw()
        return drawn


class Mining_Village(Card):
    def __init__(self):
        Card.__init__(self, "Mining Village", ["action"], cost=4, actions=1, draws=2)

    @staticmethod
    def yes_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        has_mining_village = False
        for c in player.played:
            if c.name == "Mining Village":
                has_mining_village = True

        if not has_mining_village:
            return 0

        c = getcard("Mining Village", game.supply, player.played, "your hand")
        game.trash.append(c)
        player.played.remove(c)
        player.purse += 1
        return 0

    @staticmethod
    def no_callback(
        player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        return 0

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if player.yesnoinput(
            "trash?",
            game,
            network,
            callbacks={
                True: Mining_Village.yes_callback,
                False: Mining_Village.no_callback,
            },
            mock=mock,
        ):
            Mining_Village.yes_callback(player, game, network, mock)
        return 0


class Upgrade(Card):
    def __init__(self):
        Card.__init__(self, "Upgrade", ["action"], cost=5, actions=1, draws=1)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        if len(player.hand) > 0:
            this_card = player.choose_discard(
                player.name + ", choose a card from your hand to discard: ",
                game,
                network,
                trash_card=True,
                mock=mock,
            )
            if this_card:
                c = getcard(this_card, game.supply, player.hand, "your hand")
                game.trash.append(c)
                player.hand.remove(c)
                c.ontrash(player, game, network, mock)
                player.gain_card(
                    game, network, c.cost + 1, exact=True, mock=mock,
                )
        return 0


class Trading_Post(Card):
    def __init__(self):
        Card.__init__(self, "Trading Post", ["action"], cost=5)

    def play(
        self,
        player: Player.Player,
        game: Game.Game,
        network: DominionNetwork,
        mock: bool,
    ) -> int:
        trashed = 0
        while (len(player.hand) > 0) and (trashed < 2):
            this_card = player.choose_discard(
                player.name + ", choose a card from your hand to discard: ",
                game,
                network,
                trash_card=True,
                mock=mock,
            )
            if this_card:
                c = getcard(this_card, game.supply, player.hand, "your hand")
                game.trash.append(c)
                player.hand.remove(c)
                c.ontrash(player, game, network, mock)
                trashed += 1

        if len(game.supply["Silver"]) > 0:
            player.hand.append(game.supply["Silver"].pop())

        return 0


"""class Bandit(Action_card):
    def __init__(self):
        Card.__init__(self, "Vassal", ["actin"], cost=5)

    def play(
        self, this_player: Player.Player, game: Game.Game, network: DominionNetwork, mock: bool
    ) -> int:
        if len(supply["Gold"]) > 0:
            this_player.discard.append(supply["Gold"].pop())

        for player in players_around(players, this_player, inclusive=False):
            for c in player.hand:
                if c.react(player, mock) or mock:
                    break
            else:
                for i in range(2):
                    player.draw(player.hold)
                this_player.hprint((player.name, namesinlist(player.hold)))



                if "coin" in catinlist(player.hold):
                    while True:
                        burn = input(
                            "Which card would you like "
                            + player.name
                            + " to trash?\n-->"
                        )
                        c = getcard(
                            burn, supply, player.hold, " the top 2 cards", ["coin"]
                        )
                        if c:
                            player.hold.remove(c)
                            break
                    if this_player.yesnoinput(
                        "Do you want to steal it?",
                        ", it's mine!",
                        ", leave it in the trash.",
                        mock=mock,
                    ):
                        this_player.discard.append(c)
                    else:
                        trash.append(c)
                player.discard = player.discard + player.hold
                player.hold = []"""


CardNameMap = {
    "Curse": Curse(),
    "Copper": Copper(),
    "Estate": Estate(),
    "Cellar": Cellar(),
    "Chapel": Chapel(),
    "Moat": Moat(),
    "Silver": Silver(),
    "Chancellor": Chancellor(),
    "Village": Village(),
    "Woodcutter": Woodcutter(),
    "Workshop": Workshop(),
    "Gardens": Gardens(),
    "Bureaucrat": Bureaucrat(),
    "Feast": Feast(),
    "Militia": Militia(),
    "Moneylender": Moneylender(),
    "Remodel": Remodel(),
    "Smithy": Smithy(),
    "Spy": Spy(),
    "Thief": Thief(),
    "Throne Room": Throne_Room(),
    "Duchy": Duchy(),
    "Market": Market(),
    "Council Room": Council_Room(),
    "Festival": Festival(),
    "Laboratory": Laboratory(),
    "Library": Library(),
    "Mine": Mine(),
    "Witch": Witch(),
    "Gold": Gold(),
    "Adventurer": Adventurer(),
    "Province": Province(),
    "Duke": Duke(),
    "Poacher": Poacher(),
    "Vassal": Vassal(),
    "Artisan": Artisan(),
    "Courtyard": Courtyard(),
    "Shanty Town": Shanty_Town(),
    "Baron": Baron(),
    "Platinum": Platinum(),
    "Colony": Colony(),
    "Ill-Gotten Gains": IllGottenGains(),
    "Treasure Trove": Treasure_Trove(),
    "Cache": Cache(),
    "Harem": Harem(),
    "Feodum": Feodum(),
    "Tunnel": Tunnel(),
    "Silk Road": Silk_Road(),
    "Fairgrounds": Fairgrounds(),
    "Farmland": Farmland(),
    "Great Hall": Great_Hall(),
    "Mill": Mill(),
    "Bank": Bank(),
    "Conspirator": Conspirator(),
    "Ironworks": Ironworks(),
    "Mining Village": Mining_Village(),
    "Nobles": Nobles(),
    "Upgrade": Upgrade(),
    "Trading Post": Trading_Post(),
}

CardIndexMap: Dict[str, int] = {}

current_idx = 0
for key in CardNameMap:
    CardIndexMap[key] = current_idx
    current_idx += 1
