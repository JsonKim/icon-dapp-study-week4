import os

from iconsdk.builder.transaction_builder import (
    DeployTransactionBuilder,
    CallTransactionBuilder,
    TransactionBuilder)
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.icon_service import IconService
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from iconservice import Address
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS

DIR_PATH = os.path.abspath(os.path.dirname(__file__))


class TestDiceGame(IconIntegrateTestBase):
    TEST_HTTP_ENDPOINT_URI_V3 = "http://127.0.0.1:9000/api/v3"
    SCORE_PROJECT= os.path.abspath(os.path.join(DIR_PATH, '..'))

    def setUp(self):
        super().setUp()

        self.icon_service = None
        # if you want to send request to network, uncomment next line and set self.TEST_HTTP_ENDPOINT_URI_V3
        # self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))

        self.test1_wallet = self._test1
        self.test2_wallet = self._wallet_array[0]
        self.test3_wallet = self._wallet_array[1]

        # install SCORE
        self._score_address = self._deploy_score()['scoreAddress']

    def _deploy_score(self, to: str = SCORE_INSTALL_ADDRESS) -> dict:
        # Generates an instance of transaction for deploying SCORE.
        transaction = DeployTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(to) \
            .step_limit(100_000_000_000) \
            .nid(3) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(gen_deploy_data_content(self.SCORE_PROJECT)) \
            .build()

        # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._test1)

        # process the transaction in local
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])
        self.assertTrue('scoreAddress' in tx_result)

        return tx_result

    def _create_room(self, _from: KeyWallet):
        transaction_create_room = CallTransactionBuilder() \
            .from_(_from.get_address()) \
            .to(self._score_address) \
            .step_limit(10_000_000) \
            .nid(3) \
            .nonce(100) \
            .method("createRoom") \
            .params('') \
            .build()

        signed_transaction_create_room = SignedTransaction(transaction_create_room, _from)
        tx_result_create_room = self.process_transaction(signed_transaction_create_room, self.icon_service)
        return tx_result_create_room

    def _escape(self, _from: KeyWallet):
        transaction_escape_room = CallTransactionBuilder() \
            .from_(_from.get_address()) \
            .to(self._score_address) \
            .step_limit(10_000_000) \
            .nid(3) \
            .nonce(100) \
            .method("escape") \
            .params({}) \
            .build()

        signed_transaction_escape_room = SignedTransaction(transaction_escape_room, _from)
        tx_result_escape_room = self.process_transaction(signed_transaction_escape_room, self.icon_service)
        return tx_result_escape_room

    def _join_room(self, _from: KeyWallet, _game_room_id: Address):
        transaction_join_room = CallTransactionBuilder() \
            .from_(_from.get_address()) \
            .to(self._score_address) \
            .step_limit(10_000_000) \
            .nid(3) \
            .nonce(100) \
            .method("joinRoom") \
            .params({'_gameRoomId': f'{_game_room_id}'}) \
            .build()

        signed_transaction_join_room = SignedTransaction(transaction_join_room, _from)
        tx_result_join_room = self.process_transaction(signed_transaction_join_room, self.icon_service)
        return tx_result_join_room

    def _play(self, _from: KeyWallet):
        transaction_play = CallTransactionBuilder() \
            .from_(_from.get_address()) \
            .to(self._score_address) \
            .step_limit(10_000_000) \
            .nid(3) \
            .nonce(100) \
            .method("play") \
            .params({}) \
            .build()

        signed_transaction_play = SignedTransaction(transaction_play, _from)
        tx_result_play = self.process_transaction(signed_transaction_play, self.icon_service)
        return tx_result_play

    def _play_call(self, _from: KeyWallet):
        call = CallBuilder().from_(_from.get_address()) \
            .to(self._score_address) \
            .method("play") \
            .build()

        # Sends the call request
        response = self.process_call(call, self.icon_service)
        return response

    def test_score_update(self):
        # update SCORE
        tx_result = self._deploy_score(self._score_address)

        self.assertEqual(self._score_address, tx_result['scoreAddress'])

    def test_create_room_and_escape(self):
        tx_result_create_room = self._create_room(self.test1_wallet)
        self.assertTrue('status' in tx_result_create_room)
        self.assertEqual(1, tx_result_create_room['status'])

        tx_result_escape = self._escape(self.test1_wallet)
        self.assertTrue('status' in tx_result_escape)
        self.assertEqual(1, tx_result_escape['status'])

    def test_create_room_twice(self):
        tx_result_create_room = self._create_room(self.test1_wallet)
        self.assertTrue('status' in tx_result_create_room)
        self.assertEqual(1, tx_result_create_room['status'])

        tx_result_create_room = self._create_room(self.test1_wallet)
        self.assertTrue('status' in tx_result_create_room)
        self.assertEqual(0, tx_result_create_room['status'])

    def test_create_room_and_join(self):
        tx_result_create_room = self._create_room(self.test1_wallet)
        self.assertTrue('status' in tx_result_create_room)
        self.assertEqual(1, tx_result_create_room['status'])

        tx_result_join_room = self._join_room(self.test2_wallet, self.test1_wallet.get_address())
        self.assertTrue('status' in tx_result_join_room)
        self.assertEqual(1, tx_result_join_room['status'])

        # 방장 먼저 나가면 실패
        tx_result_escape = self._escape(self.test1_wallet)
        self.assertTrue('status' in tx_result_escape)
        self.assertEqual(0, tx_result_escape['status'])

        tx_result_escape = self._escape(self.test2_wallet)
        self.assertTrue('status' in tx_result_escape)
        self.assertEqual(1, tx_result_escape['status'])

        # 나간 방 또 나가면 실패
        tx_result_escape = self._escape(self.test2_wallet)
        self.assertTrue('status' in tx_result_escape)
        self.assertEqual(0, tx_result_escape['status'])
 
        tx_result_escape = self._escape(self.test1_wallet)
        self.assertTrue('status' in tx_result_escape)
        self.assertEqual(1, tx_result_escape['status'])

    def test_create_play(self):
        # 방에 없는 유저가 플레이하면 실패
        tx_result_play = self._play(self.test1_wallet)
        self.assertTrue('status' in tx_result_play)
        self.assertEqual(0, tx_result_play['status'])

        tx_result_create_room = self._create_room(self.test1_wallet)
        self.assertTrue('status' in tx_result_create_room)
        self.assertEqual(1, tx_result_create_room['status'])

        # 혼자 있으면 플레이 실패
        tx_result_play = self._play(self.test1_wallet)
        self.assertTrue('status' in tx_result_play)
        self.assertEqual(0, tx_result_play['status'])

        tx_result_join_room = self._join_room(self.test2_wallet, self.test1_wallet.get_address())
        self.assertTrue('status' in tx_result_join_room)
        self.assertEqual(1, tx_result_join_room['status'])

        # join 한 유저가 플레이
        tx_result_play = self._play_call(self.test2_wallet)
        print(tx_result_play)
