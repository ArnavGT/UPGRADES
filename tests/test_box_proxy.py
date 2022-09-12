from brownie import Box, BoxV2, Contract, ProxyAdmin, TransparentUpgradeableProxy
from scripts.helpful_scripts import get_account
from scripts.deploy_and_upgrade import upgrade, encode_function_data


def deploy():
    account = get_account()

    if not Box:
        box = Box.deploy({'from': account})
    box = Box[-1]

    if not ProxyAdmin:
        proxyAdmin = ProxyAdmin.deploy({'from': account})
    proxyAdmin = ProxyAdmin[-1]

    initializer = box.store
    encode_function_call = encode_function_data(initializer, 1)

    if not TransparentUpgradeableProxy:
        proxy = TransparentUpgradeableProxy.deploy(
            box.address, proxyAdmin.address, encode_function_call,
            {'from': account}
        )
    proxy = TransparentUpgradeableProxy[-1]

    return proxy, proxyAdmin, account


def test_proxy_delegates_Call():
    proxy, _, _ = deploy()
    proxy_box = Contract.from_abi("Box", proxy.address, Box.abi)

    assert proxy_box.retrieve() == 1


def test_proxy_uprades():
    proxy, proxyAdmin, account = deploy()

    boxV2 = BoxV2.deploy({'from': account})
    upgrade_tx = upgrade(account, proxy,
                         boxV2.address, proxyAdmin, None)

    proxy_boxV2 = Contract.from_abi("BoxV2", proxy.address, BoxV2.abi)
    proxy_boxV2.increment({'from': account})

    assert proxy_boxV2.retrieve() == 2
