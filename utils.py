def namesinlist(cardlist):
    namelist = []
    for c in cardlist:
        namelist.append(c.name)
    return namelist


def catinlist(cardlist):
    catlist = set()
    for c in cardlist:
        for cat in c.categories:
            catlist.add(cat)
    return list(catlist)


def getcard(
    name,
    supply,
    target_list=None,
    target_name="the supply anymore",
    categories=["curse", "victory", "action", "coin", "attack", "reaction", "duration"],
    upto=100,
):
    if name not in supply:
        print(name + " is not in this game.")
        raise ValueError
    if not target_list:
        target_list = supply[name]
    nameslist = namesinlist(target_list)
    if name not in nameslist:
        print("There is no " + name + " in " + target_name)
        raise ValueError
    i = nameslist.index(name)
    c = target_list[i]
    category_match = False
    for cat in c.categories:
        if cat in categories:
            category_match = True
            break

    if not category_match:
        catstring = categories[0]
        for i in categories[1:]:
            catstring = catstring + " or " + categories[i]
        print(name + " is not a " + catstring + " card.")
        raise ValueError
    if c.cost > upto:
        print(name + " costs " + str(c.cost))
        raise ValueError
    return c


def players_around(players, this_player, inclusive=False):
    around = players[this_player.order :] + players[: this_player.order]
    if inclusive:
        return around[:]
    else:
        return around[1:]
