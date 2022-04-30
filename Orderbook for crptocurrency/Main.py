import GetBook
import time
from pickle import TRUE
import logging

path = os.path.abspath(os.path.dirname('symbol_config.csv'))+"\\symbol_config.csv"
ExchangeList = GrabCoin.ReturnExchange(path)

GetBook.LoadCoins(ExchangeList)

#Main Code
period = __period__
endtime=time.time()

while TRUE:
    if (time.time()>=endtime): 
            try:
                GetBook.LoadCoins(ExchangeList)
                endtime = endtime + period
            except:
                logging.warning('Connection issue!')