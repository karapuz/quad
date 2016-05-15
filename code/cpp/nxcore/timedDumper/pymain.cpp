#include <Python.h>
#include "NxCoreAPI_Class.h"
#include <map>
#include "handlers.h"
#include "correctionList.h"

NxCoreClass NxCore;

static PyObject * NxError;
static PyObject * pyCallback = NULL;

int tickCallback(const NxCoreSystem* system, const NxCoreMessage* msg);

int null(const NxCoreSystem *, const NxCoreMessage*){
  return  NxCALLBACKRETURN_CONTINUE;  
}

PyObject * buildReturnedData( boost::unordered_map<string,priceList> & symbIndexMap ){
  PyObject * dataList;
  PyObject * singleSymbolData;
  unsigned int n = symbIndexMap.size();
  dataList = PyList_New( n );
  boost::unordered_map<string, priceList>::iterator it;
  Py_ssize_t i = 0;
  for(it = symbIndexMap.begin(); it != symbIndexMap.end(); it++, i++){
    singleSymbolData = Py_BuildValue("s(dikI)(dikI)(dikI)(idii)",
				     //Symbol
				     it->first.c_str(),
				     //LastTrade
				     it->second.last_trade,
				     it->second.trade_size,
				     it->second.trade_time,
				     it->second.trade_exchange,
				     //Last ask
				     it->second.ask,
				     it->second.ask_size,
				     it->second.quote_time,
				     it->second.quote_exchange,
				     //Last bid
				     it->second.bid,
				     it->second.bid_size,
				     it->second.quote_time,
				     it->second.quote_exchange,
				     //Aggregates
				     it->second.volume_shares,
				     it->second.volume_dollars,
				     it->second.numTrades,
				     it->second.numQuotes
				     );
    it->second.volume_shares = 0;
    it->second.volume_dollars = 0;
    it->second.numTrades = 0;
    it->second.numQuotes = 0;

    PyList_SET_ITEM( dataList , i, singleSymbolData );
  }
  return dataList;  
}

bool pyCallbackWrapper( boost::unordered_map<string,priceList> & symbIndexMap ){
  PyObject * result;
  PyObject * data;
  long c_result;
  data = buildReturnedData(symbIndexMap);
  if ( data == NULL ){
    return false;
  }
  result = PyObject_CallFunctionObjArgs( pyCallback, data, NULL );
  Py_DECREF( data );
  if (result == NULL){
    return false;
  }
  c_result = PyInt_AsLong( result );
  Py_DECREF( result );
  if( ! c_result )
    return false;
  return true;
}

int init(NxCoreClass * curNxCore){
  reportTimeQueue.sort();

  ptrNxCore = curNxCore;
  setOutputFunction( pyCallbackWrapper );
  return 0;
}

static PyObject * processTape(PyObject * self, PyObject * args){
  const char * fname;
  const char * correctionFile;
  PyObject * reportTimePyList;
  PyObject * temp;
  int returnVal;

  if( !PyArg_ParseTuple( args, "ssOO", &fname, &correctionFile , &temp, &reportTimePyList) )
    return NULL;
  if (!PyCallable_Check(temp)){
    PyErr_SetString(PyExc_TypeError, "Callback function parameter must be callable");
    return NULL;
  }
  Py_XINCREF(temp);
  if ( !PyList_Check(reportTimePyList) ){
    PyErr_SetString(PyExc_TypeError, "report time list parameter must be a list");
    return NULL;
  }
  
  //Parse the Python Data and put the times into the reportTimeQueue.
  Py_ssize_t listLen;
  PyObject * listItem;
  listLen = PyList_Size(reportTimePyList);
  for( Py_ssize_t i = 0; i < listLen; i++){
    listItem = PyList_GetItem( reportTimePyList, i );
    reportTimeQueue.push_back( PyInt_AsLong( listItem ) );
  }

  if( PyErr_Occurred() ){
    return NULL;
  }

  init(&NxCore);
  //Set up the python end of the call back.

  Py_XDECREF(pyCallback);
  pyCallback = temp;

  if( ! NxCore.LoadNxCore("libnx.so") ){
    PyErr_SetString( NxError, "Error loading NxCore library." );
    return NULL;
  }

  returnVal = NxCore.ProcessTape( fname, 0, 0, 0, (NxCoreCallback)&tickCallback );
  if( PyErr_Occurred() )
    return NULL;
  return Py_BuildValue("i", returnVal);
}

static PyMethodDef nxlibMethods[] = {
  {"processTape", processTape, METH_VARARGS, "Process a tape."},
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initnxtimeddump(void){
  PyObject * m;
  m =  Py_InitModule( "nxtimeddump", nxlibMethods );
  if ( m == NULL )
    return;
  //  NxError = PyErr_NewException( (char*)"nxtimmeddump.error", NULL, NULL );
  //  Py_INCREF( NxError );
  //  PyModule_AddObject( m, "error", NxError );
}

int tickCallback(const NxCoreSystem* system, const NxCoreMessage* msg){
  int ret =  NxCALLBACKRETURN_CONTINUE;
  switch (msg->MessageType)
    {
    case NxMSG_STATUS:
      ret	= null(system,msg); //OnStatus(system,msg);
      break;
    case NxMSG_EXGQUOTE:
      ret	= OnPriceEvent(system,msg,NxMSG_EXGQUOTE);
      break;
    case NxMSG_MMQUOTE:
      ret	= OnPriceEvent(system,msg,NxMSG_MMQUOTE); //OnMMQuote(system,msg);
      break;
    case NxMSG_TRADE:
      ret	= OnPriceEvent(system,msg,NxMSG_TRADE); //OnTrade(system,msg);
      break;
    case NxMSG_CATEGORY:
      ret	= null(system,msg); //OnCategory(system,msg);		
      break;
    case NxMSG_SYMBOLCHANGE:
      ret	= null(system,msg); //OnSymbolChange(system,msg);	
      break;
    case NxMSG_SYMBOLSPIN:
      ret	= null(system,msg); //OnSymbolSpin(system,msg);	
      break;
    }
  return ret;
}
