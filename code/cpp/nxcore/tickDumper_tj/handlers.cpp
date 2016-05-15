#include <iostream>
#include <set>
#include <list>
#include "handlers.h"
#include "NxCoreAPI_Class.h"
#include "NxCoreAPI.h"

using namespace std;

std::set<string> symbSet;
list<unsigned long> reportTimeQueue;
NxCoreClass * ptrNxCore;  //Set in main


bool checkUniverseSymbol(char * str){
  return symbSet.count(str) >= 1;
}

void printQuote(string symb, double ask, double bid, int ask_size,
		int bid_size, unsigned long quote_time, unsigned int quote_exchange ){
  cout << "(\'Q\',"
       << "\'" << symb << "\',"
       << bid << "," << bid_size << ","
       << ask << "," << ask_size << ","
       << quote_time << "," << quote_exchange
       << ")" << endl;
}

void printTrade(string symb, double price, int trade_size, unsigned long time,  unsigned int trade_exchange){
  cout << "(\'T\',"
       << "\'" << symb << "\',"
       << price << "," << trade_size << ","
       << time << "," << trade_exchange
       << ")" << endl;
}

int OnPriceEvent(const NxCoreSystem*sys,const NxCoreMessage*msg, unsigned int messageType ){
  
  if ( reportTimeQueue.empty() ){
    return NxCALLBACKRETURN_STOP;
  }

  // Check time
  unsigned long time = msg->coreHeader.nxExgTimestamp.MsOfDay;
  if( time < reportTimeQueue.front() )
    return NxCALLBACKRETURN_CONTINUE;
  if( time > reportTimeQueue.back() )
    return NxCALLBACKRETURN_STOP;

  char * symbStr = (char*) msg->coreHeader.pnxStringSymbol->String;
  if( !checkUniverseSymbol(symbStr) )
    return NxCALLBACKRETURN_CONTINUE;

  double bid, ask, price;
  int ask_size, bid_size, trade_size;
  //unsigned long time;
  unsigned int exchange;
  switch(messageType){
  case NxMSG_EXGQUOTE:
    ask = ptrNxCore->PriceToDouble(msg->coreData.ExgQuote.coreQuote.AskPrice,
    					     msg->coreData.ExgQuote.coreQuote.PriceType);
    bid = ptrNxCore->PriceToDouble(msg->coreData.ExgQuote.coreQuote.BidPrice,
    					     msg->coreData.ExgQuote.coreQuote.PriceType);
    exchange = msg->coreHeader.ReportingExg;
    ask_size = msg->coreData.ExgQuote.coreQuote.AskSize;
    bid_size = msg->coreData.ExgQuote.coreQuote.BidSize;
    //printQuote(symbStr, ask, bid, ask_size, bid_size, time, exchange);
    break;
  case NxMSG_MMQUOTE:
    ask = ptrNxCore->PriceToDouble(msg->coreData.MMQuote.coreQuote.AskPrice,
				   msg->coreData.MMQuote.coreQuote.PriceType);
    bid = ptrNxCore->PriceToDouble(msg->coreData.MMQuote.coreQuote.BidPrice,
				   msg->coreData.MMQuote.coreQuote.PriceType);
    exchange = msg->coreHeader.ReportingExg;
    ask_size = msg->coreData.MMQuote.coreQuote.AskSize;
    bid_size = msg->coreData.MMQuote.coreQuote.BidSize;
    //printQuote(symbStr, ask, bid, ask_size, bid_size, time, exchange);
    break;
  case NxMSG_TRADE:
    price = ptrNxCore->PriceToDouble(msg->coreData.Trade.Price,
					     msg->coreData.Trade.PriceType);
    exchange = msg->coreHeader.ReportingExg;
    trade_size = msg->coreData.Trade.Size;
    printTrade( symbStr, price, trade_size, time, exchange );
    break;
  }

  return NxCALLBACKRETURN_CONTINUE;
}
