from brownie import network, config, interface
from scripts.helpful_scripts import getAccount
from web3 import Web3


def getWeth():
    # get weth token by depositing some eth tokens
    account = getAccount()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.deposit({"from": account, "value": Web3.toWei(0.09, "ether")})
    tx.wait(1)
    print("recieved 0.1 weth token")
    return tx


def main():
    getWeth()
