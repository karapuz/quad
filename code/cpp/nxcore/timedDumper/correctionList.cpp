#include "correctionList.h"
#include <fstream>
#include <stdio.h>
#include <string.h>
#include <iostream> //temp

using namespace std;

bool buildCorrectListsFromFile(cancelMap & cancels, insertionList & inserts, string filename){
  ifstream fin;
  fin.open(filename.c_str());
  
  string line;
  while(fin.good()){
    getline( fin, line );

    char type;
    char symb[100];
    float price;
    unsigned int trade_size, time, seqNo,exchange;
    sscanf(line.c_str(),"(%c,%s )\n",&type, symb);
    if(sscanf(line.c_str(),"(%c,%s ,%f,%d,%d,%d,%d)",&type,symb,&price,&trade_size,&time,&seqNo,&exchange) < 7){
      if( line == "\n" || line.length() == 0 )
	continue;
      cerr << "Error on line: " << line << line.length() << endl;
      return false;
    }

    if( type == 'C' ){
      cancelation c;
      c.symb = string(symb);
      c.seqNo = (uint) seqNo;
      c.exchange = (unsigned short)exchange;
      cancels[seqNo] = c;
    }
    else if( type == 'I' ){
      insertion i;
      i.symb = string(symb);
      i.time = (unsigned long)time;
      i.exchange = (unsigned short)exchange;
      i.seqNo = (uint)seqNo;
      i.price = (double)price;
      i.trade_size = trade_size;
      inserts.push_back(i);
    }
    else{
      cerr << "Error on line: " << line << endl;
      return false;
    }
  }
  fin.close();
  inserts.sort();
  return true;
}

void printCancelList( cancelMap & cancels ){
  cancelMap::iterator it;
  for (it = cancels.begin(); it != cancels.end(); it++ ){
    cout << it->second.symb << ", "
	 << it->second.exchange << ", "
	 << it->second.seqNo << endl;
  }
}

void printInsertionList( insertionList & inserts ){
  insertionList::iterator it;
  for (it = inserts.begin(); it !=inserts.end(); it++ ){
    cout << it->symb << ", "
	 << it->time << ", "
      	 << it->exchange << ", "
	 << it->price << endl;
  }
}
