#include <iostream>
#include <boost/unordered_map.hpp>
#include <list>
#include "handlers.h"
#include "NxCoreAPI_Class.h"
#include "NxCoreAPI.h"

using namespace std;

boost::unordered_map<string, priceList> symbIndexMap;
list<unsigned long> reportTimeQueue;
NxCoreClass * ptrNxCore;  //Set in main

cancelMap canceledTrades;
insertionList insertedTrades;

bool checkUniverseSymbol(char * str){
  return  (symbIndexMap.find(str + 1) != symbIndexMap.end());
}

int sign( float n ){
  if(n>0) return  1;
  if(n<0) return -1;
}
void printHeader(){
  cout << "(\'X\'";
  boost::unordered_map<string, priceList>::iterator it;
  for(it = symbIndexMap.begin(); it != symbIndexMap.end(); it++)
    cout << "," << "\'" << it->first << "\'" ;
  cout << ")" << endl;
}

void printLastTrade(){
  cout << "(\'T\'";
  boost::unordered_map<string, priceList>::iterator it;
  for(it = symbIndexMap.begin(); it != symbIndexMap.end(); it++){
    cout << ",(" 
	 << it->second.last_trade << ","
	 << it->second.trade_size << ","
	 << it->second.trade_time << ","
	 << it->second.trade_exchange << ")";
  }
  cout << ")" << endl;

}
void printAsk(){
  cout << "(\'A\'";
  boost::unordered_map<string, priceList>::iterator it;
  for(it = symbIndexMap.begin(); it != symbIndexMap.end(); it++){
    cout << ",(" 
	 << it->second.ask << ","
	 << it->second.ask_size << ","
	 << it->second.quote_time << ","
	 << it->second.quote_exchange << ")";
  }
  cout << ")" << endl;

}

void printBid(){
  cout << "(\'B\'";
  boost::unordered_map<string, priceList>::iterator it;
  for(it = symbIndexMap.begin(); it != symbIndexMap.end(); it++){
    cout << ",(" 
	 << it->second.bid << ","
	 << it->second.bid_size << ","
	 << it->second.quote_time << ","
	 << it->second.quote_exchange << ")";
  }
  cout << ")" << endl;

}

void printAndClearAggregates(){
  cout << "(\'G\'";
  boost::unordered_map<string, priceList>::iterator it;
  for(it = symbIndexMap.begin(); it != symbIndexMap.end(); it++){
    cout << ",(" 
	 << it->second.volume_shares << ","
	 << it->second.volume_dollars << ","
	 << it->second.numTrades << ","
	 << it->second.numQuotes << ")";

    it->second.volume_shares = 0;
    it->second.volume_dollars = 0;
    it->second.numTrades = 0;
    it->second.numQuotes = 0;
  }
  cout << ")" << endl;

}

void printAndClearAggregates_TJ(){

  boost::unordered_map<string, priceList>::iterator it;
  for(it = symbIndexMap.begin(); it != symbIndexMap.end(); it++){
    cout << it->second.volume_shares << ","
	 << it->second.NZvolume_shares << ","
	 << it->second.numTrades << ","
	 << it->second.numNZTrades << ",";

    it->second.volume_shares = 0;
    it->second.NZvolume_shares = 0;
    it->second.numTrades = 0;
    it->second.numNZTrades = 0;
  }
  cout << endl;

}

void printAndClearAggregates_BA(){

  boost::unordered_map<string, priceList>::iterator it;
  for(it = symbIndexMap.begin(); it != symbIndexMap.end(); it++){
    cout << it->second.volume_Ashares << ","
	 << it->second.volume_Bshares << ","
	 << it->second.numQuotes << "," ;

    it->second.volume_Ashares = 0;
    it->second.volume_Bshares = 0;
    it->second.numQuotes = 0;
  }
  cout << endl;

}

void printAndClearReversals(){
  cout << "(\'R\'";
  boost::unordered_map<string, priceList>::iterator it;
  for(it = symbIndexMap.begin(); it != symbIndexMap.end(); it++){
    cout << ",("
         << it->second.numNZTrades << ","
         << it->second.numReversals << ")";

    it->second.numNZTrades = 0;
    it->second.numReversals = 0;
  }
  cout << ")" << endl;
}

void printAndClearReversals_TJ(){
  
  boost::unordered_map<string, priceList>::iterator it;
  for(it = symbIndexMap.begin(); it != symbIndexMap.end(); it++){
    cout << it->second.numNZTrades << ","
         << it->second.numReversals<< "," ;

    it->second.numNZTrades = 0;
    it->second.numReversals = 0;
  }
  cout << endl;
}

int OnPriceEvent(const NxCoreSystem*sys,const NxCoreMessage*msg, unsigned int messageType ){
  
  if ( reportTimeQueue.empty() ){
    return NxCALLBACKRETURN_STOP;
  }
  
  char * symbStr = (char*) msg->coreHeader.pnxStringSymbol->String;
  if (symbIndexMap.count(symbStr) <= 0)
    return NxCALLBACKRETURN_CONTINUE;
  //if (strcmp(symbStr,"eAAPL")!=0)
  //  return NxCALLBACKRETURN_CONTINUE;
  
// Check time
  unsigned long time = msg->coreHeader.nxExgTimestamp.MsOfDay;

  if( time > reportTimeQueue.front() ){
    //printHeader();
    //printLastTrade();
    //printBid();
    //printAsk();
    //printAndClearAggregates();
    printAndClearAggregates_TJ();
    //printAndClearAggregates_BA();
    //printAndClearReversals();
    //printAndClearReversals_TJ();

    reportTimeQueue.pop_front();
  }
  // Only go on here if we are at an equity event
  if (symbStr[0] != 'e')
    return NxCALLBACKRETURN_CONTINUE;
  //if (strcmp(symbStr,"eAAPL")!=0)
  //  return NxCALLBACKRETURN_CONTINUE;

  // Check if we need to insert some trades from the correction list.
  while( !insertedTrades.empty() && time > insertedTrades.front().time ){
    insertion i = insertedTrades.front();
    insertedTrades.pop_front();
    // Check if this inserted trade was later cancelled
    if(canceledTrades.count( i.seqNo ) >= 1)
      continue;
    if (symbIndexMap.count(i.symb) <= 0)
      continue;
    //if (strcmp(i.symb,"eAAPL")!=0)
    //  continue;
    priceList & curPrices = symbIndexMap[i.symb];
    
    curPrices.last_trade = i.price;
    curPrices.trade_exchange = i.exchange;
    curPrices.trade_time = i.time;
    curPrices.trade_size = i.trade_size;
    curPrices.volume_shares += curPrices.trade_size;
    curPrices.volume_dollars += curPrices.trade_size * curPrices.last_trade;
    curPrices.numTrades++;

    if (curPrices.numTrades == 1){
      curPrices.numNZTrades++;
      curPrices.last_NZtrade=curPrices.last_trade;
      curPrices.NZvolume_shares += curPrices.trade_size;
    }
    if (curPrices.numTrades >  1){
      if (curPrices.last_trade - curPrices.last_NZtrade !=0 ){
        curPrices.numNZTrades++;
        curPrices.pre_NZtrade  = curPrices.last_NZtrade;
        curPrices.last_NZtrade = curPrices.last_trade;
        curPrices.NZvolume_shares += curPrices.trade_size;
      }
    }
    if (curPrices.numNZTrades == 2){
      curPrices.reversal_flag = sign(curPrices.last_NZtrade - curPrices.pre_NZtrade); 
    }
    if (curPrices.numNZTrades >  2 ){
      if (curPrices.reversal_flag != sign(curPrices.last_NZtrade - curPrices.pre_NZtrade)){
        curPrices.reversal_flag = sign(curPrices.last_NZtrade - curPrices.pre_NZtrade);
        curPrices.numReversals++;
      }
    }
  }

  // Update price in row
  priceList & curPrices = symbIndexMap[symbStr];

  switch(messageType){
  case NxMSG_EXGQUOTE:
    curPrices.ask = ptrNxCore->PriceToDouble(msg->coreData.ExgQuote.coreQuote.AskPrice,
    					     msg->coreData.ExgQuote.coreQuote.PriceType);
    curPrices.bid = ptrNxCore->PriceToDouble(msg->coreData.ExgQuote.coreQuote.BidPrice,
    					     msg->coreData.ExgQuote.coreQuote.PriceType);
    curPrices.quote_exchange = msg->coreHeader.ReportingExg;
    curPrices.quote_time = time;
    curPrices.ask_size = msg->coreData.ExgQuote.coreQuote.AskSize;
    curPrices.bid_size = msg->coreData.ExgQuote.coreQuote.BidSize;
    curPrices.volume_Ashares += curPrices.ask_size;
    curPrices.volume_Bshares += curPrices.bid_size;
    curPrices.numQuotes++;
    break;
  case NxMSG_MMQUOTE:
    curPrices.ask = ptrNxCore->PriceToDouble(msg->coreData.MMQuote.coreQuote.AskPrice,
    					     msg->coreData.MMQuote.coreQuote.PriceType);
    curPrices.bid = ptrNxCore->PriceToDouble(msg->coreData.MMQuote.coreQuote.BidPrice,
    					     msg->coreData.MMQuote.coreQuote.PriceType);
    curPrices.quote_exchange = msg->coreHeader.ReportingExg;
    curPrices.quote_time = time;
    curPrices.ask_size = msg->coreData.MMQuote.coreQuote.AskSize;
    curPrices.bid_size = msg->coreData.MMQuote.coreQuote.BidSize;
    curPrices.volume_Ashares += curPrices.ask_size;
    curPrices.volume_Bshares += curPrices.bid_size;
    curPrices.numQuotes++;
    break;
  case NxMSG_TRADE:
    // Skip cancel and insert events... these should be in our lists
    if( (msg->coreData.Trade.PriceFlags) & (0x10 | 0x20) )
      break;
    // Skip if this trade has been cancelled
    if( canceledTrades.count( msg->coreData.Trade.ExgSequence ) )
      break;
    // New valid trade.
    curPrices.last_trade  = ptrNxCore->PriceToDouble(msg->coreData.Trade.Price,
					     msg->coreData.Trade.PriceType);
    curPrices.trade_exchange = msg->coreHeader.ReportingExg;
    curPrices.trade_time = time;
    curPrices.trade_size = msg->coreData.Trade.Size;
    curPrices.volume_shares += curPrices.trade_size;
    curPrices.volume_dollars += curPrices.trade_size * curPrices.last_trade;
    curPrices.numTrades++;

    if (curPrices.numTrades == 1){
      curPrices.numNZTrades++;
      curPrices.last_NZtrade=curPrices.last_trade;
      curPrices.NZvolume_shares += curPrices.trade_size;
    }
    if (curPrices.numTrades >  1){
      if (curPrices.last_trade - curPrices.last_NZtrade !=0 ){
        curPrices.numNZTrades++;
        curPrices.pre_NZtrade  = curPrices.last_NZtrade;
        curPrices.last_NZtrade = curPrices.last_trade;
        curPrices.NZvolume_shares += curPrices.trade_size;
      }
    }
    if (curPrices.numNZTrades == 2){
      curPrices.reversal_flag = sign(curPrices.last_NZtrade - curPrices.pre_NZtrade); 
    }
    if (curPrices.numNZTrades >  2 ){
      if (curPrices.reversal_flag != sign(curPrices.last_NZtrade - curPrices.pre_NZtrade)){
        curPrices.reversal_flag = sign(curPrices.last_NZtrade - curPrices.pre_NZtrade);
        curPrices.numReversals++;
      }
    }

    break;
  }
  //symbIndexMap[symbStr] = curPrices; // Not needed if curPrices is a reference

  return NxCALLBACKRETURN_CONTINUE;
}
