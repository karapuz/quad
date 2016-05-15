#include <iostream>
#include <boost/unordered_set.hpp>
#include <list>
#include "handlers.h"
#include "NxCoreAPI_Class.h"
#include "NxCoreAPI.h"
#include <string>

using namespace std;

NxCoreClass * ptrNxCore;  //Set in main
symbSet * inFileSymbs;

bool checkUniverseSymbol(char * str){
  //  return symbSet.count(str) >= 1;
  // return strcmp(str,"eGOOG") == 0;
  if(str[0] != 'e') return false;
  inFileSymbs->insert(string(str));
  return true;
}

void printCorrection(string symb, double price, int trade_size, unsigned long time,  unsigned int seqNo, unsigned int exchge, unsigned char flags){

  if ( flags & 0x20 ) //Cancel
    cout << "(C,";
  else if( flags & 0x10 ) //Insert
    cout << "(I," ;
  else
    cout << "(T," ;
  cout << symb << " ,"
       << price << "," << trade_size << ","
       << time << "," << seqNo << ","
       << exchge 
       << ")" << endl;
}

int OnPriceEvent(const NxCoreSystem*sys,const NxCoreMessage*msg, unsigned int messageType ){
  char * symbStr = (char*) msg->coreHeader.pnxStringSymbol->String;
  if( !checkUniverseSymbol(symbStr) )
    return NxCALLBACKRETURN_CONTINUE;

  unsigned long time = msg->coreHeader.nxExgTimestamp.MsOfDay;

  double bid, ask, price;
  int ask_size, bid_size, trade_size;
  //unsigned long time;
  unsigned int seqNo, exchange;
  switch(messageType){
  case NxMSG_EXGQUOTE:
    return NxCALLBACKRETURN_CONTINUE;
  case NxMSG_MMQUOTE:
    return NxCALLBACKRETURN_CONTINUE;
  case NxMSG_TRADE:
    if ( !((msg->coreData.Trade.PriceFlags) & ( 0x10 | 0x20 )) )
      return NxCALLBACKRETURN_CONTINUE;
    price = ptrNxCore->PriceToDouble(msg->coreData.Trade.Price,
				     msg->coreData.Trade.PriceType );
    seqNo = msg->coreData.Trade.ExgSequence;
    trade_size = msg->coreData.Trade.Size;
    exchange = msg->coreHeader.ReportingExg;
    printCorrection( symbStr, price, trade_size, time, seqNo, exchange ,msg->coreData.Trade.PriceFlags );
    break;
  }
  return NxCALLBACKRETURN_CONTINUE;
}

void dumpSymbs( symbSet & symbs ){
  cout << "-----BEGIN SYMBOL LIST-----" << endl;
  for ( symbSet::iterator it=symbs.begin(); it!=symbs.end(); ++it)
    cout << *it << endl;
  cout << "-----END SYMBOL LIST-----" << endl;
}
