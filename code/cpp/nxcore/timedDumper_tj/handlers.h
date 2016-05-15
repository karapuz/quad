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
    reversal_flag = 0;numReversals = 0;last_NZtrade = 0;pre_NZtrade = 0;numNZTrades = 0;
  }
  double bid;
  double ask;
  double last_trade;
  double last_NZtrade;
  double pre_NZtrade;
  unsigned int trade_exchange;
  unsigned int quote_exchange;
  unsigned long trade_time;
  unsigned long quote_time;
  int ask_size;
  int bid_size;
  int trade_size;
  int volume_shares;
  int volume_Ashares;
  int volume_Bshares;
  double volume_dollars;
  int numTrades;
  int numQuotes;
  int reversal_flag;
  int numReversals;
  int numNZTrades;
  int NZvolume_shares;
};

void printHeader();

extern boost::unordered_map<std::string, priceList> symbIndexMap;
extern std::list<unsigned long> reportTimeQueue;

extern cancelMap canceledTrades;
extern insertionList insertedTrades;

extern NxCoreClass * ptrNxCore;
