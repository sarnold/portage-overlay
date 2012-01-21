from distutils.core import setup, Extension

module1 = Extension('jarow',
                    sources = ['jarow.c'])

setup (name = 'JaroWinkler',
       version = '1.0',
       description = 'Jaro Winkler String Matcher',
       ext_modules = [module1])

