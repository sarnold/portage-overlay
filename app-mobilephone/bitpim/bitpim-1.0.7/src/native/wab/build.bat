genprops.py
"c:\program files\swig-1.3.19\swig.exe" -python -c++  -noexcept -o _pywabimpl.cpp pywab.swg
sed -f unapply.sed < pywabimpl.py >xx.py
del pywabimpl.py
ren xx.py pywabimpl.py
@rem remove our constants hackery
sed s/constants:://g < _pywabimpl.cpp > pywabimpl.cpp
@del _pywabimpl.cpp
g++ -g -Wall -shared -L c:\python23\libs -I c:\python23\include -I c:\projects\fixedwab -o _pywabimpl.dll pywabimpl.cpp wab.cpp -lpython23