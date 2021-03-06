#! /usr/bin/python
# -*- encoding: utf-8 -*-

"""Events of playing cards.

Contains play minions, spells and weapons.
"""

from .base import GameEvent
from ..utils.debug import verbose

__author__ = 'fyabc'


class PlayCard(GameEvent):
    def __init__(self, game, card, player_id=None):
        super(PlayCard, self).__init__(game)
        self.card = card
        self.player_id = player_id if player_id is not None else game.current_player_id

    def __str__(self):
        return '{}(P{}, {})'.format(super().__str__(), self.player_id, self.card)

    def _happen(self):
        self._message()

        player = self.game.players[self.player_id]

        # todo: change it to `UseCrystal` event
        player.remain_crystal -= self.card.cost

        if self.card.overload > 0:
            player.next_locked_crystal += self.card.overload

        # todo: change it to `RemoveCardFromHand` event
        player.hand.remove(self.card)

    def _message(self):
        verbose('P{} play a card {}!'.format(self.player_id, self.card))


class AddMinionToDesk(GameEvent):
    def __init__(self, game, minion, index, player_id=None):
        """

        :param game:
        :param minion: the minion or its id.
        :param index: the location of the minion to be insert.
            The minion will at before `location`.
            [FIXME]: The location may be changed in battle cry, this problem should be fixed in future.
        :param player_id: The player id to add the minion.
        """

        super(AddMinionToDesk, self).__init__(game)

        if isinstance(minion, (int, str)):
            # Create a new card
            self.minion = self.game.create_card(minion, player_id)
        else:
            # Move an exist card
            self.minion = minion
        self.index = index
        self.player_id = player_id if player_id is not None else game.current_player_id

    def __str__(self):
        return '{}(P{}, {}=>Loc{})'.format(super().__str__(), self.player_id, self.minion, self.index)

    def _happen(self):
        player = self.game.players[self.player_id]

        if player.desk_full:
            # If the desk is full, disable this event.
            verbose('The desk is full, not add {} to desk!'.format(self.minion))
            self.disable()
            return

        self.minion.change_location(self.minion.DESK)
        player.desk.insert(self.index, self.minion)

        # Set timestamp of summon.
        self.minion.timestamp = self.game.summon_number
        self.game.summon_number += 1

    def _message(self):
        pass


class CompleteMinionToDesk(GameEvent):
    """The event that complete minion to desk.
    
    [NOTE] This is different from `AddMinionToDesk`.    
    This is just a stub event.
    """

    def __init__(self, game, minion, index, player_id=None):
        super().__init__(game)
        self.minion = minion
        self.index = index
        self.player_id = player_id if player_id is not None else game.current_player_id

    def __str__(self):
        return '{}(P{}, {}=>Loc{})'.format(super().__str__(), self.player_id, self.minion, self.index)


def add_minion_to_desk(game, minion, index, player_id=None):
    """The whole process to add minion to desk.

    Include AddMinionToDesk and CompleteMinionToDesk.
    If a card want to add a minion to desk, it should use this instead of AddMinionToDesk and CompleteMinionToDesk.
    """

    if isinstance(minion, (int, str)):
        # Create a new card
        minion = game.create_card(minion, player_id)

    if player_id is None:
        player_id = game.current_player_id

    game.add_event_quick(AddMinionToDesk, minion, index, player_id)
    game.add_event_quick(CompleteMinionToDesk, minion, index, player_id)


class SummonMinion(PlayCard):
    """Summon a minion from hand. This is a user operation."""

    def __init__(self, game, card, index, player_id=None, target=None):
        super(SummonMinion, self).__init__(game, card, player_id)
        self.index = index
        self.target = target

    @property
    def minion(self):
        return self.card

    def __str__(self):
        return '{}(P{}, {}=>Loc{})'.format(GameEvent.__str__(self), self.player_id, self.minion, self.index)

    def _happen(self):
        """The resolve order of summon a minion:
    
        0. SummonMinion -> Cause other events
        1. AddMinionToDesk
        2. run_battle_cry
        3. CompleteMinionToDesk (Trigger handlers like Knife Juggler (飞刀杂耍者))
        TODO: 4. TriggerSecret
        """

        super(SummonMinion, self)._happen()

        # [NOTE] Add minion to desk **BEFORE** battle cry.
        # [WARNING] todo: here must be test carefully.
        self.game.add_event_quick(AddMinionToDesk, self.minion, self.index, self.player_id)

        self.minion.run_battle_cry(self.player_id, self.index, self.target)

        self.game.add_event_quick(CompleteMinionToDesk, self.minion, self.index, self.player_id)

    def _message(self):
        verbose('P{} summon a minion {} to location {}!'.format(self.player_id, self.minion, self.index))


class RunSpell(GameEvent):
    """Run a spell. The spell may not be played from the hand."""

    def __init__(self, game, spell, player_id, target=None):
        super().__init__(game)
        self.spell = spell
        self.player_id = player_id
        self.target = target

    def __str__(self):
        return '{}(P{}, {}=>{})'.format(super().__str__(), self.player_id, self.spell, self.target)

    def _happen(self):
        # todo: may more things to do here?
        self.spell.change_location(self.spell.CEMETERY)
        self.spell.play(self.player_id, self.target)

    def _message(self):
        verbose('P{} run a spell {} to {}!'.format(self.player_id, self.spell, self.target))


class PlaySpell(PlayCard):
    """Play a spell from the hand. This is a user operation."""

    def __init__(self, game, spell, target=None, player_id=None):
        super(PlaySpell, self).__init__(game, spell, player_id)
        self.target = target

    @property
    def spell(self):
        return self.card

    def __str__(self):
        return '{}(P{}, {}=>{})'.format(GameEvent.__str__(self), self.player_id, self.spell, self.target)

    def _happen(self):
        super()._happen()

        self.game.add_event_quick(RunSpell, self.spell, self.player_id, self.target)

    def _message(self):
        verbose('P{} play a spell {} to {}!'.format(self.player_id, self.spell, self.target))


__all__ = [
    'PlayCard',
    'AddMinionToDesk',
    'CompleteMinionToDesk',
    'add_minion_to_desk',
    'SummonMinion',
    'RunSpell',
    'PlaySpell',
]
