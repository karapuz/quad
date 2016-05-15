from distutils.core import setup, Extension

module1 = Extension( 'nxtimeddump',
                     sources = ['pymain.cpp',
                                'handlers.cpp',
                                'correctionList.cpp'],
                     include_dirs = ['/opt/vendorLibs/NxCore'],
                     libraries = ['nx'],
                     library_dirs = ['/opt/vendorLibs/NxCore']
                     )

setup ( name = 'NxTimedDump',
        version = '0.1',
        description = 'Interface to NxCore parser.',
        ext_modules = [module1] )

