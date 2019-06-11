from iconservice import *
from .gameroom.gameroom import GameRoom

TAG = 'DiceGame'

def random(seed: str):
    input_data = seed.encode()
    hash = sha3_256(input_data)
    return int.from_bytes(hash, 'big')

def rangeN(n: int, min: int, max: int):
    return n % (max - min + 1) + min

class DiceGame(IconScoreBase):
    _GAME_ROOM = "game_room"
    _GAME_ROOM_LIST = "game_room_list"
    _IN_GAME_ROOM = "in_game_room"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._db = db
        self._DDB_game_room = DictDB(self._GAME_ROOM, db, value_type=str)
        self._DDB_in_game_room = DictDB(self._IN_GAME_ROOM, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()
    
    def _get_game_room_list(self):
        return ArrayDB(self._GAME_ROOM_LIST, self._db, value_type=str)

    def _crash_room(self, game_room_id: Address):
        game_room_to_crash_dict = json_loads(self._DDB_game_room[game_room_id])

        game_room_to_crash = GameRoom(Address.from_string(game_room_to_crash_dict['owner']), Address.from_string(game_room_to_crash_dict['game_room_id']), game_room_to_crash_dict['creation_time'],
                             game_room_to_crash_dict['participants'])
        participants_to_escape = game_room_to_crash.participants
        for partcipant in participants_to_escape:
            self._DDB_in_game_room.remove(Address.from_string(partcipant))

        self._DDB_game_room.remove(game_room_id)
        game_room_list = list(self._get_game_room_list())
        game_room_list.remove(json_dumps(game_room_to_crash_dict))
        for count in range(len(self._get_game_room_list())):
            self._get_game_room_list().pop()

        for game_room in game_room_list:
            self._get_game_room_list().put(game_room)

    @external
    def createRoom(self):
        # Check whether 'self.msg.sender' is now participating to game room or not
        if self._DDB_in_game_room[self.msg.sender] is not None:
            revert("You already joined to another room")

        # Create the game room & Get in to it & Set the prize_per_game value
        game_room = GameRoom(self.msg.sender, self.msg.sender, self.block.height)
        game_room.join(self.msg.sender)
        self._DDB_game_room[self.msg.sender] = str(game_room)

        game_room_list = self._get_game_room_list()
        game_room_list.put(str(game_room))
        self._DDB_in_game_room[self.msg.sender] = self.msg.sender

    @external
    def joinRoom(self, _gameRoomId: Address):
        # Check whether the game room with game_room_id is existent or not
        if self._DDB_game_room[_gameRoomId] is "":
            revert(f"There is no game room which has equivalent id to {_gameRoomId}")

        # Check the participant is already joined to another game_room
        if self._DDB_in_game_room[self.msg.sender] is not None:
            revert(f"You already joined to another game room : {self._DDB_in_game_room[self.msg.sender]}")

        game_room_dict = json_loads(self._DDB_game_room[_gameRoomId])
        game_room = GameRoom(Address.from_string(game_room_dict['owner']), Address.from_string(game_room_dict['game_room_id']), game_room_dict['creation_time'],
                             game_room_dict['participants'])
        game_room_list = self._get_game_room_list()

        # Check the game room's participants. Max : 2
        if game_room.is_full():
            revert(f"Full : Can not join to game room {_gameRoomId}")

        # Get in to the game room
        game_room.join(self.msg.sender)
        self._DDB_in_game_room[self.msg.sender] = _gameRoomId
        self._DDB_game_room[_gameRoomId] = str(game_room)

        game_room_index_gen = (index for index in range(len(game_room_list)) if game_room.game_room_id == Address.from_string(json_loads(game_room_list[index])['game_room_id']))

        try:
            index = next(game_room_index_gen)
            game_room_list[index] = str(game_room)
        except StopIteration:
            pass

    @external
    def escape(self):
        # Check whether 'self.msg.sender' is now participating to game room or not
        if self._DDB_in_game_room[self.msg.sender] is None:
            revert(f'No game room to escape')

        # Retrieve the game room ID & Check the game room status
        game_room_id_to_escape = self._DDB_in_game_room[self.msg.sender]
        game_room_to_escape_dict = json_loads(self._DDB_game_room[game_room_id_to_escape])
        game_room_to_escape = GameRoom(Address.from_string(game_room_to_escape_dict['owner']), Address.from_string(game_room_to_escape_dict['game_room_id']),
                                       game_room_to_escape_dict['creation_time'],
                                       game_room_to_escape_dict['participants'])

        # Escape from the game room
        if game_room_to_escape.owner == self.msg.sender:
            if not game_room_to_escape.is_full():
                game_room_to_escape.escape(self.msg.sender)
                self._crash_room(game_room_id_to_escape)
            else:
                revert("Owner can not escape from room which has the other participant")
        else:
            game_room_to_escape.escape(self.msg.sender)
            self._DDB_game_room[game_room_id_to_escape] = str(game_room_to_escape)

        # Set the in_game_room status of 'self.msg.sender' to None
        game_room_list = self._get_game_room_list()
        game_room_index_gen = (index for index in range(len(game_room_list)) if game_room_to_escape.game_room_id == Address.from_string(json_loads(game_room_list[index])['game_room_id']))

        try:
            index = next(game_room_index_gen)
            game_room_list[index] = str(game_room_to_escape)
        except StopIteration:
            pass

        self._DDB_in_game_room.remove(self.msg.sender)
