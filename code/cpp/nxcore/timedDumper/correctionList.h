#ifndef __CORRECTIONLIST_H__
#define __CORRECTIONLIST_H__

#include <string>
#include <map>
#include <list>

typedef unsigned int uint;

using namespace std;

class cancelation{
 public:
  string symb;
  uint seqNo;
  unsigned short exchange;
};

class insertion{
 public:
  string symb;
  unsigned long time;
  unsigned short exchange;
  uint seqNo; //To check if this inserted trade was later cancelled
  double price;
  int trade_size;
 public:
  const bool operator<(const insertion & rhs){ return time < rhs.time; }; // For sorting.
};

typedef map<uint, cancelation> cancelMap;
typedef list<insertion> insertionList;

bool buildCorrectListsFromFile(cancelMap & cancels, insertionList & inserts, string filename);
void printCancelList( cancelMap & cancels );
void printInsertionList( insertionList & inserts );

#endif
