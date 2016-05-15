#include <vector>
#include "NxCoreAPI_Class.h"
#include <boost/unordered_map.hpp>
#include <list>
#include "correctionList.h"

int OnPriceEvent(const NxCoreSystem*,const NxCoreMessage*, unsigned int messageType);

class priceList {
 public:
  priceList(){bid = 0; ask = 0; last_trade = 0;
    trade_exchange = 0; quote_exchange = 0;
    trade_time = 0; quote_time = 0;
    ask_size = 0; bid_size = 0; trade_size = 0;
    volume_shares = 0; volume_dollars = 0;
    numTrades = 0; numQuotes = 0;
    
    high = 0; low = 0;
    high_time = 0; low_time = 0;    
  }
  double bid;
  double ask;
  double last_trade;
  unsigned int trade_exchange;
  unsigned int quote_exchange;
  unsigned long trade_time;
  unsigned long quote_time;
  int ask_size;
  int bid_size;
  int trade_size;
  int volume_shares;
  double volume_dollars;
  int numTrades;
  int numQuotes;

  // high/low members
  double high;
  double low;
  unsigned long high_time;
  unsigned long low_time;
};

void printHeader();
void setOutputFunction( bool (*fcn) (boost::unordered_map<string,priceList> &) );
bool printGroup( boost::unordered_map<string,priceList> & );

extern boost::unordered_map<std::string, priceList> symbIndexMap;
extern std::list<unsigned long> reportTimeQueue;

extern cancelMap canceledTrades;
extern insertionList insertedTrades;

extern NxCoreClass * ptrNxCore;
