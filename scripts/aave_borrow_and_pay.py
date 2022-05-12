from brownie import interface, network, config
from eth_account import Account
from web3 import Web3
from scripts.getWeth import getWeth
from scripts.helpful_scripts import getAccount


"""  to deposit into the aave contract, you have to interact with lendingpool. 
    the lendingPoolAddressProvider return the lendingPool Address which is the passed into the lendPool interface.
    this returns the which is where the funds are deposited.
    the ERC20 interface allows us to prompt the user to deposit a specified weth token into the contract
    to get the ammount of DAI that can be borrowed, first we get the DAI_ETH price to know how much our eth was in DAI
    the using the leendingpool.getUserAccountData we are able to know how much we can borrow

    to repay, we approve a depayment prompt and then lendingpool.repay to make the payment
"""
AMOUNT = Web3.toWei(0.9, "ether")


def depositBorrowAndRepay():
    account = getAccount()
    ERC20_address = config["networks"][network.show_active()]["weth_token"]
    ERC20 = interface.IERC20(ERC20_address)
    if [network.show_active] in ["mainnet-fork"]:
        getWeth()
    lendingPool = getLendingPool()
    # approving transaction
    tx = ERC20.approve(lendingPool.address, AMOUNT, {"from": account})
    tx.wait(1)
    print("Transaction Approved")
    # depositing into the lending pool
    print("depositing into lending pool...")
    deposit = lendingPool.deposit(
        ERC20_address,
        AMOUNT,
        account.address,
        0,
        {"from": account, "gas": 1000000, "gasPrice": Web3.toWei(10, "gwei")},
    )
    deposit.wait(1)
    print("0.09 weth deposited into the account")

    lastestPrice = getAssetPrice(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    borrowableEth = getBorrowableData()[0]
    daiToken_address = config["networks"][network.show_active()]["dai_token"]
    amountToBorrow = (1 / lastestPrice) * (borrowableEth * 0.95)
    borrow = lendingPool.borrow(
        daiToken_address,
        Web3.toWei(amountToBorrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow.wait(1)
    print("aave borrow successful")
    getBorrowableData()
    totalDebt = getBorrowableData()[1]
    approveRepay_tx = ERC20.approve(
        lendingPool.address, Web3.toWei(totalDebt, "ether"), {"from": account}
    )
    approveRepay_tx.wait(1)
    print("Approve repay transaction")
    repay = lendingPool.repay(
        daiToken_address,
        Web3.toWei(amountToBorrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    repay.wait(1)
    print("aave repaid successful")
    print("you have successfully deposited, borrowed and repaid with AAVE")
    getBorrowableData()


def getBorrowableData(lendingPool, account):
    (
        totalCollateralETH,
        totalDebtETH,
        availableBorrowsETH,
        currentLiquidationThreshold,
        ltv,
        healthFactor,
    ) = lendingPool.getUserAccountData(account.address)
    available_eth = Web3.fromWei(availableBorrowsETH, "ether")
    print("available eth that can be borrowed is:", available_eth)
    totalDebt_ETH = Web3.fromWei(totalDebtETH, "ether")
    print("available eth that can be borrowed is:", totalDebt_ETH)
    return float(available_eth), float(totalDebt_ETH)


def getAssetPrice(priceFeedAddress):
    dai_eth_priceFeed = interface.AggregatorV3Interface(priceFeedAddress)
    lastestPrice = dai_eth_priceFeed.latestRoundData()[1]
    convertedLastestPrice = Web3.fromWei(lastestPrice, "ether")
    print("lastest price is", convertedLastestPrice)
    return float(convertedLastestPrice)


def getLendingPool():
    lendingPoolAddressProvider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lendingPoolAddress = lendingPoolAddressProvider.getLendingPool()
    lendingPool = interface.ILendingPool(lendingPoolAddress)
    return lendingPool


def main():
    depositBorrowAndRepay()
