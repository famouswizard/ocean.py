"""Web3Helper module to provide convenient functions."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from eth_utils import big_endian_to_int

from ocean_lib.web3_internal.utils import (
    add_ethereum_prefix_and_hash_msg,
    generate_multi_value_hash,
    split_signature
)
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_overrides.signature import SignatureFix
from ocean_lib.web3_internal.web3_provider import Web3Provider


class Web3Helper(object):
    """This class provides convenient web3 functions"""

    DEFAULT_NETWORK_NAME = 'development'
    _network_name_map = {
        1: 'Main',
        2: 'Morden',
        3: 'Ropsten',
        4: 'Rinkeby',
        42: 'Kovan',
        100: 'xDai',
    }

    @staticmethod
    def get_network_name(network_id=None):
        """
        Return the network name based on the current ethereum network id.
        Return `development` for every network id that is not mapped.

        :param network_id: Network id, int
        :return: Network name, str
        """
        if not network_id:
            network_id = Web3Helper.get_network_id()
        return Web3Helper._network_name_map.get(network_id, Web3Helper.DEFAULT_NETWORK_NAME)

    @staticmethod
    def get_network_id():
        """
        Return the ethereum network id calling the `web3.version.network` method.

        :return: Network id, int
        """
        return int(Web3Provider.get_web3().version.network)

    @staticmethod
    def sign_hash(msg_hash, account):
        """
        This method use `personal_sign`for signing a message. This will always prepend the
        `\x19Ethereum Signed Message:\n32` prefix before signing.

        :param msg_hash:
        :param account: Account
        :return: signature
        """
        wallet = Wallet(Web3Provider.get_web3(), account.key, account.password,
                        account.address)
        s = wallet.sign(msg_hash)
        return s.signature.hex()

    @staticmethod
    def ec_recover(message, signed_message):
        """
        This method does not prepend the message with the prefix `\x19Ethereum Signed Message:\n32`.
        The caller should add the prefix to the msg/hash before calling this if the signature was
        produced for an ethereum-prefixed message.

        :param message:
        :param signed_message:
        :return:
        """
        w3 = Web3Provider.get_web3()
        v, r, s = split_signature(w3, w3.toBytes(hexstr=signed_message))
        signature_object = SignatureFix(vrs=(v, big_endian_to_int(r), big_endian_to_int(s)))
        return w3.eth.account.recoverHash(message, signature=signature_object.to_hex_v_hacked())

    @staticmethod
    def personal_ec_recover(message, signed_message):
        prefixed_hash = add_ethereum_prefix_and_hash_msg(message)
        return Web3Helper.ec_recover(prefixed_hash, signed_message)

    @staticmethod
    def unlock_account(account):
        """
        Unlock the account.

        :param account: Account
        :return:
        """
        return Web3Provider.get_web3().personal.unlockAccount(account.address, account.password)

    @staticmethod
    def get_ether_balance(address):
        """
        Get balance of an ethereum address.

        :param address: address, bytes32
        :return: balance, int
        """
        return Web3Provider.get_web3().eth.getBalance(address, block_identifier='latest')

    @staticmethod
    def to_wei(ether_value):
        return Web3Provider.get_web3().toWei(ether_value, 'ether')

    @staticmethod
    def from_wei(wei_value):
        return Web3Provider.get_web3().fromWei(wei_value, 'ether')

    @staticmethod
    def generate_multi_value_hash(types, values):
        return generate_multi_value_hash(types, values)

    @staticmethod
    def send_ether(from_account, to_address, ether_amount):
        w3 = Web3Provider.get_web3()
        if not w3.isChecksumAddress(to_address):
            to_address = w3.toChecksumAddress(to_address)

        tx = {
            'from': from_account.address,
            'to': to_address,
            'value': Web3Helper.to_wei(ether_amount),
            'gas': 500000}
        wallet = Wallet(w3, from_account.key, from_account.password, from_account.address)
        raw_tx = wallet.sign_tx(tx)
        tx_hash = w3.eth.sendRawTransaction(raw_tx)
        receipt = w3.eth.waitForTransactionReceipt(tx_hash, timeout=30)
        return receipt
