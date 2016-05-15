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

bool (*outputGroup)( boost::unordered_map<string,priceList> & ) = NULL;

bool checkUniverseSymbol(char * str){
  return  (symbIndexMap.find(str + 1) != symbIndexMap.end());
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

    it->second.high = 0;
    it->second.low = 0;
    it->second.high_time = 0;
    it->second.low_time = 0;
  }
  cout << ")" << endl;
}

void updateHighLow( priceList& curPrices ) {
    if ( curPrices.high == 0 || curPrices.high < curPrices.last_trade ) {
        curPrices.high = curPrices.last_trade;
        curPrices.high_time = curPrices.trade_time;
    }

    if ( curPrices.low == 0 || curPrices.low > curPrices.last_trade ) {
        curPrices.low = curPrices.last_trade;
        curPrices.low_time = curPrices.trade_time;
    }
}

void printHighLow(){
  cout << "(\'H\'";
  boost::unordered_map<string, priceList>::iterator it;
  for(it = symbIndexMap.begin(); it != symbIndexMap.end(); it++){
    cout << ",("
     << it->second.high << ","
     << it->second.low << ","
     << it->second.high_time << ","
     << it->second.low_time << ")";
  }
  cout << ")" << endl;
}

bool tradeFilter( const NxCoreMessage * msg ){
    // Skip cancel and insert events... these should be in our lists
    if( (msg->coreData.Trade.PriceFlags) & (0x10 | 0x20) )
      return false;
    // Skip if this trade has been cancelled
    if( canceledTrades.count( msg->coreData.Trade.ExgSequence ) )
      return false;
    if( msg->coreData.Trade.ConditionFlags )
      return false;
    if( msg->coreData.Trade.VolumeType != 0 )
      return false;
    if( msg->coreData.Trade.TradeCondition == 5  ||
	msg->coreData.Trade.TradeCondition == 6  ||
	msg->coreData.Trade.TradeCondition == 7  ||
	msg->coreData.Trade.TradeCondition == 26 ||
	msg->coreData.Trade.TradeCondition == 62 ||
	msg->coreData.Trade.TradeCondition == 63 ||
	msg->coreData.Trade.TradeCondition == 66 ||
	msg->coreData.Trade.TradeCondition == 68 )
      return false;

    //Normal as best Lorne can tell.
    return true;
}

bool printGroup( boost::unordered_map<string,priceList> & data ){
  printHeader();
  printLastTrade();
  printBid();
  printAsk();
  printHighLow();
  printAndClearAggregates();
  return true;
}

void setOutputFunction( bool (*fcn) ( boost::unordered_map<string,priceList> & ) ){
  outputGroup = fcn;
}

int OnPriceEvent(const NxCoreSystem*sys,const NxCoreMessage*msg, unsigned int messageType ){
  
  if ( reportTimeQueue.empty() ){
    return NxCALLBACKRETURN_STOP;
  }
  
  char * symbStr = (char*) msg->coreHeader.pnxStringSymbol->String;

  // Check time
  unsigned long time = msg->coreHeader.nxExgTimestamp.MsOfDay;

  if( time > reportTimeQueue.front() ){
    if ( ! outputGroup( symbIndexMap ) )
      return NxCALLBACKRETURN_STOP;

    reportTimeQueue.pop_front();
  }
  // Only go on here if we are at an equity event
  if (symbStr[0] != 'e')
    return NxCALLBACKRETURN_CONTINUE;

  // Check if we need to insert some trades from the correction list.
  while( !insertedTrades.empty() && time > insertedTrades.front().time ){
    insertion i = insertedTrades.front();
    insertedTrades.pop_front();
    // Check if this inserted trade was later cancelled
    if(canceledTrades.count( i.seqNo ) >= 1)
      continue;

    priceList & curPrices = symbIndexMap[i.symb];

    curPrices.last_trade = i.price;
    curPrices.trade_exchange = i.exchange;
    curPrices.trade_time = i.time;
    curPrices.trade_size = i.trade_size;
    curPrices.volume_shares += curPrices.trade_size;
    curPrices.volume_dollars += curPrices.trade_size * curPrices.last_trade;
    curPrices.numTrades++;
    updateHighLow( curPrices );
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
    curPrices.numQuotes++;
    break;
  case NxMSG_TRADE:
    if( ! tradeFilter( msg ) )
      break;
    curPrices.last_trade = ptrNxCore->PriceToDouble(msg->coreData.Trade.Price,
					     msg->coreData.Trade.PriceType);
    curPrices.trade_exchange = msg->coreHeader.ReportingExg;
    curPrices.trade_time = time;
    curPrices.trade_size = msg->coreData.Trade.Size;
    curPrices.volume_shares += curPrices.trade_size;
    curPrices.volume_dollars += curPrices.trade_size * curPrices.last_trade;
    curPrices.numTrades++;
    updateHighLow( curPrices );
    break;
  }
  //symbIndexMap[symbStr] = curPrices; // Not needed if curPrices is a reference

  return NxCALLBACKRETURN_CONTINUE;
}
