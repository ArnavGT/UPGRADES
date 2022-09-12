from brownie import Box, network, ProxyAdmin, TransparentUpgradeableProxy, Contract, BoxV2
from scripts.helpful_scripts import get_account
import eth_utils

'''
The Only disappointment about this upgrades is that you have to define a new contract container to interact
with, every single time you have upgraded the logic implementation because to use new functions,
you need the declared abi also.
'''


def main():
    account = get_account()
    print(f'Deploying to {network.show_active()} network...')

    # This box is the implementation contract, so we cannot run 'increment' function on this.
    box = Box.deploy({'from': account})
    print(box.retrieve())

    proxy_admin = ProxyAdmin.deploy({'from': account})

    # We need initializers instead of constrcutors and as Proxies dont have constructors.
    # So we use a initializer function inside the contract that sets the initial values.
    # To use a initializer, we need to set it up so that the proxy can recognize it:
    # The Function, and its first parameter(store value). and then we have to encode this.
    # initializer = box.store, *args = 1, etc... (for its parameters!)
    initializer = box.store
    box_encodedInitializer_func = encode_function_data(initializer, 10)

    # This here is deploying the proxy.
    # We give the logic contracts address first, then proxy admin's (could be us as well), then the intializer function's encoded input(encode_function_data function)
    proxy = TransparentUpgradeableProxy.deploy(
        box.address, proxy_admin.address, box_encodedInitializer_func, {'from': account, 'gas_limit': 10000000})  # Put in the gas limit.

    print(f'Proxy Deployed to {proxy}! You can now upgrade logic functions.')

    # Since we want to work with logic contract through the proxy and not directly, we need set up the contract to interact with it
    proxy_box = Contract.from_abi("Box", proxy.address, Box.abi)
    # This would work even though they are different contract because the proxy delegates calls to the box contract.
    # So, If we put in Box_v2 here, it would error out as the proxy's logic implementation is still set to box
    print(proxy_box.retrieve())

    # Now Lets do upgrades
    box_v2 = BoxV2.deploy({'from': account})

    # Its going to be empty without any initializer
    # boxV2_initializer_func = encode_function_data()
    # proxy_admin.upgrade(proxy, box_v2, {'from': account})

    upgrade_tx = upgrade(account, proxy, box_v2.address, proxy_admin)
    # To get the new contract with new abi defined.
    proxy_boxV2 = Contract.from_abi("BoxV2", proxy.address, BoxV2.abi)

    print(f'The Logic Implementation of proxy contract has been updated.')

    # call the implement function.
    proxy_boxV2.increment({'from': account})
    print(proxy_boxV2.retrieve())


def encode_function_data(initializer=None, *args):
    if len(args) == 0 or not initializer:
        return eth_utils.to_bytes(hexstr='0x')
    return initializer.encode_input(*args)  # In built brownie function.


def upgrade(account, proxy, _imp_address, _proxyAdmin=None, initializer=None, *args):
    transaction = None
    if _proxyAdmin:
        if initializer:
            encode_function_call = encode_function_data(
                initializer=initializer, *args)
            transaction = _proxyAdmin.upgradeToAndCall(
                proxy.address,
                _imp_address,
                encode_function_call,
                {'from': account}
            )
            transaction.wait(1)
        else:
            transaction = _proxyAdmin.upgrade(
                proxy.address, _imp_address, {'from': account})
            transaction.wait(1)
    else:
        if initializer:
            encode_function_call = encode_function_data(
                initializer=initializer, *args)
            transaction = proxy.upgradeToAndCall(
                _imp_address, encode_function_call, {'from': account}
            )
            transaction.wait(1)
        else:
            transaction = proxy.upgradeTo(_imp_address, {'from': account})
            transaction.wait(1)
    return transaction
