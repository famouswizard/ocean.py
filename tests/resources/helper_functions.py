#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import json
import os
import pathlib
import uuid
import logging
import logging.config

import coloredlogs
import yaml
from ocean_utils.agreements.service_factory import ServiceDescriptor
from web3 import Web3

from ocean_lib.assets.asset import Asset
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.factory import FactoryContract
from ocean_lib.web3_internal import Web3Helper
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.utils import get_account

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.web3_provider import Web3Provider
from tests.resources.mocks.data_provider_mock import DataProviderMock

PUBLISHER_INDEX = 1
CONSUMER_INDEX = 0


def get_resource_path(dir_name, file_name):
    base = os.path.realpath(__file__).split(os.path.sep)[1:-1]
    if dir_name:
        return pathlib.Path(os.path.join(os.path.sep, *base, dir_name, file_name))
    else:
        return pathlib.Path(os.path.join(os.path.sep, *base, file_name))


def get_publisher_account():
    return get_account(0)


def get_consumer_account():
    return get_account(1)


def new_factory_contract():
    factory = FactoryContract(address=None)
    address = factory.deploy(
        ContractHandler.artifacts_path,
        Web3.toChecksumAddress(os.environ.get('MINTER_ADDRESS', '0xe2DD09d719Da89e5a3D0F2549c7E24566e947260'))
    )

    return FactoryContract(address=address)


def get_publisher_ocean_instance(use_provider_mock=False):
    data_provider = DataProviderMock if use_provider_mock else None
    ocn = Ocean(data_provider=data_provider)
    account = get_publisher_account()
    ocn.main_account = account

    return ocn


def get_consumer_ocean_instance(use_provider_mock=False):
    data_provider = DataProviderMock if use_provider_mock else None
    ocn = Ocean(data_provider=data_provider)
    account = get_consumer_account()
    ocn.main_account = account

    return ocn


def get_ddo_sample():
    return Asset(json_filename=get_resource_path('ddo', 'ddo_sa_sample.json'))


def get_sample_ddo_with_compute_service():
    path = get_resource_path('ddo', 'ddo_with_compute_service.json')  # 'ddo_sa_sample.json')
    assert path.exists(), f"{path} does not exist!"
    with open(path, 'r') as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)


def get_algorithm_ddo():
    path = get_resource_path('ddo', 'ddo_algorithm.json')
    assert path.exists(), f"{path} does not exist!"
    with open(path, 'r') as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)


def get_computing_metadata():
    path = get_resource_path('ddo', 'computing_metadata.json')
    assert path.exists(), f"{path} does not exist!"
    with open(path, 'r') as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)


def get_registered_ddo(ocean_instance, account):
    metadata = get_metadata()
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    ServiceDescriptor.access_service_descriptor(
        ocean_instance.assets._build_access_service(
            metadata,
            Web3Helper.to_wei(1),
            account
        ),
        DataServiceProvider.get_download_endpoint(ocean_instance.config)
    )

    asset = ocean_instance.assets.create(metadata, account)
    return asset


def log_event(event_name):
    def _process_event(event):
        print(f'Received event {event_name}: {event}')

    return _process_event


def get_metadata():
    path = get_resource_path('ddo', 'valid_metadata.json')
    assert path.exists(), f"{path} does not exist!"
    with open(path, 'r') as file_handle:
        metadata = file_handle.read()
    return json.loads(metadata)


def setup_logging(default_path='logging.yaml', default_level=logging.INFO, env_key='LOG_CFG'):
    """Logging setup."""
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as file:
            try:
                config = yaml.safe_load(file.read())
                logging.config.dictConfig(config)
                coloredlogs.install()
                logging.info(f'Logging configuration loaded from file: {path}')
            except Exception as ex:
                print(ex)
                print('Error in Logging Configuration. Using default configs')
                logging.basicConfig(level=default_level)
                coloredlogs.install(level=default_level)
    else:
        logging.basicConfig(level=default_level)
        coloredlogs.install(level=default_level)
