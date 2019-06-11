from iconservice import *


class GameRoom:

    def __init__(self, owner: Address, game_room_id: Address, creation_time: int, participants: list = None):
        self.owner = owner
        self.game_room_id = game_room_id
        self.creation_time = creation_time
        if participants is None:
            self.participants = []
        else:
            self.participants = participants

    def join(self, participant: Address):
        self.participants.append(str(participant))

    def escape(self, participant_to_escape: Address):
        self.participants.remove(str(participant_to_escape))

    def is_full(self):
        return len(self.participants) >= 2

    def __str__(self):
        response = {
            'owner': f'{self.owner}',
            'game_room_id': f'{self.game_room_id}',
            'creation_time': self.creation_time,
            'participants': self.participants,
        }
        return json_dumps(response)
