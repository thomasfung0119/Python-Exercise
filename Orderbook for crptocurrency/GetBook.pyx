#-*- coding : utf-8-*-
import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import threading
import logging

screenlock = threading.Semaphore(value=1)
cur_pos = os.path.abspath(os.path.dirname('symbol_config.csv'))

#Main function that do http request, Please add request here for more platforms
cpdef GetResponse(platform,symbol):
    try:
        if platform == "BINANCE":
                r = requests.get("https://api.binance.com/api/v3/depth",params={"symbol":symbol})
        elif platform == "BNFUTURES":
                r = requests.get("https://binance.com/fapi/v1/depth",params={"symbol":symbol, "limit":100})
        elif platform == "AAX":
                r = requests.get("https://api.aax.com/v2/market/orderbook",params={"symbol":symbol})
        elif platform == "DERIBIT":
                r = requests.get("https://www.deribit.com/api/v2/public/get_order_book",params={"instrument_name" : symbol})
        elif platform == "FTX":
                r = requests.get("https://ftx.com/api/markets/" +symbol + "/orderbook")
        elif platform == "GATEIO":
                r = requests.get("https://api.gateio.ws/api/v4/spot/order_book",params={"currency_pair" : symbol})
        elif platform == "HUOBI":
                r = requests.get("https://api.huobi.pro/market/depth",params={"symbol" : symbol, "type" : "step0"})
        elif platform == "KUCOIN":
                r = requests.get("https://api.kucoin.com/api/v1/market/orderbook/level2_100",params={"symbol" : symbol})
        else:
            screenlock.acquire()
            logging.warning("Corresponding API for " + platform + " are not implemented yet.")
            screenlock.release()
            return None 
    except:
        return None
    
    #Guard Network Error
    if not(r.status_code == 200):
        screenlock.acquire()
        logging.warning("Request Error for " + symbol + " of " + platform)
	print('Request Error')
        screenlock.release()
        return None
    return r
        
cdef NormalFrame(j):
        #Guard Empty OrderBook
        if not("asks" in j or "bids" in j):
            return None

        #Ask only OrderBook
        if not("bids" in j):
            frames = {side: pd.DataFrame(data=j[side], columns=["price", "quantity"], dtype=float)
                        for side in ["asks"]}
            return frames

        #Bid only OrderBook
        if not("asks" in j):
            frames = {side: pd.DataFrame(data=j[side], columns=["price", "quantity"], dtype=float)
                        for side in ["bids"]}
            return frames
        
        #Normal OrderBook
        frames = {side: pd.DataFrame(data=j[side], columns=["price", "quantity"], dtype=float)
                        for side in ["bids", "asks"]}
        return frames

#Frame the Response to a certain framework to save
cdef Frame(j , platform):
    try: 
        if (platform == "DERIBIT" or platform =="FTX"):
            frames = NormalFrame(j["result"])
        elif platform == "HUOBI":
            frames = NormalFrame(j["tick"])
        elif platform == "KUCOIN":
            frames = NormalFrame(j["data"])
        else:
            frames = NormalFrame(j)
    except:
        frames = None
    return frames

#Return all symbol of a platform that is in the symbol_config 
cpdef ReturnSymbol(platform):
    path = cur_pos +"\\symbol_config.csv"

    #Guard if cannot find csv file
    if not(os.path.isfile(path)):
        return None 

    #Read csv and get corresponding coin
    SymbolConfig = pd.read_csv(path)
    SymbolConfig = SymbolConfig.loc[SymbolConfig['exchange'] == platform]   
    cdef list Symbol = SymbolConfig['symbol_orderbook'].tolist()

    #Guard if no symbol is found
    if Symbol == []:
        return None
    
    return Symbol

#Return all exchange platform as a list
cpdef ReturnExchange(path):
    #Initializing
    cdef list Result = []
    if path == "":
        path = cur_pos +"\\symbol_config.csv"
    
    #Guard if cannot find csv file
    if not(os.path.isfile(path)):
        return None

    #Read csv and get a list of exchange platform 
    SymbolConfig = pd.read_csv(path)
    cdef list ExchangeList = SymbolConfig['exchange'].tolist()
    for temp in ExchangeList:
        if not(temp in Result):
            Result.append(temp)
    
    return Result

#Create an Inventory if it is not there already
cdef CreateInventory(path):
    if not(os.path.isdir(path)):
        os.mkdir(path)

#Saving the orderbook of a symbol
cpdef SaveBook(path, date, platform, coin):
    #Getting Response
    r = GetResponse(platform, coin)
    if r == None:
        return None

    #Framing data
    frames = Frame(r.json(), platform)
    if frames==None:
        screenlock.acquire()
	logging.warning("Error from Framing " + coin + " from " + platform)
        print("Error from Framing " + coin + " from " + platform)
        screenlock.release()
        return None
    
    #edit, add date, add platform, save csv
    frames_list = [frames[side].assign(side=side) for side in frames]
    data = pd.concat(frames_list, axis="index", 
                        ignore_index=True, sort=True)
    data.insert(loc=1, column='date', value=date, allow_duplicates=True)
    data.insert(loc=1, column='exchange', value=platform, allow_duplicates=True)
    data.to_csv(path)      
    

cpdef LoadCoins(ExchangeList):
    #Initialize variable
    s = time.time()
    now = datetime.now()-timedelta(hours=8)
    current_dir = cur_pos + "\\Record\\"+ now.strftime("%d-%m-%Y") 
    absolute_path = current_dir + "\\" + now.strftime("%H-%M-%S")

    #Create Directory if not exist
    CreateInventory(current_dir)
    CreateInventory(absolute_path)


    for exchange in ExchangeList:

        symbols = ReturnSymbol(exchange)

        #Guard if no symbol retrieved
        if symbols == None:
	    logging.warning("Cannot retrieve symbols from " + exchange)
            print("Cannot retrieve symbols from " + exchange)
            continue
        
        #Save Data by using Thread
        try:
            threadList = []
            for i in range(len(symbols)):
                path = absolute_path + "\\" + exchange + "_" + str(symbols[i]).replace("/","-") + ".csv"
                tempThread = threading.Thread(target = SaveBook, args = (path, now, exchange, symbols[i]))
                threadList.append(tempThread)
                
            for t in threadList:
                t.start()
                
            for t in threadList:
                t.join()
        except:
	    logging.warning("Thread Error")
            print("Thread Error")

    #Check Loading time
    logging.info("Total Loading time: {}".format(time.time()-s))
    print("Total Loading time: {}".format(time.time()-s))