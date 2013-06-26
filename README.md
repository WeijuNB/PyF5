PyF5(Alpha)
==========

A Satic Files Server & Web Page Auto Reloader, And Also a Markdown Editor.


Install
-------
PyF5 has already submitted to PyPi. Run this command to install ( make sure you have 'easy_install' ):
```bash
sudo easy_install pyf5
```

Getting Start (Static Web Sites)
-------------------------------
1. run **f5.py** in any folder

  this will open a browser tab for you to manange your web sites.
  if not, please manually open the url displayed in the terminal
  
2. input your path, and press "添加"(the green button)

  Your project will be added to the project list on the left hand side;
  
3. select your project from the list

  Your Project is now served by PyF5, 
  click any html file in the files list (on the right hand side of the page) to open it in the browser.
  
  F5 will inject scripts into the html page, and watch related files modifications.
  Once changed are saved to files, the html page will reload automatically.
  

Dynamic Sites
-------------
If php/python/ruby/asp/... are used in your project, 
and is served by another server, you can still use PyF5 to auto reload.

Once your project are added and selected in PyF5,
a help message will show above the file list.
Just paste the script tag into your web page's source code (before &lt;/body&gt;)
And open the page with its original url. Done!


Markdown Editor
---------------
PyF5 is also a Markdown Editor.

If you click a **.md** file in the file list, PyF5 will open it with a markdown editor in the new tab.

You can see a live preview on the right side of the editor, and press ctrl+s to save.


Dependencies
------------
python
* tornado
* watchdog

html/css/js
* bootstrap
* jquery
* knockout.js
* less.js
* CodeMirror
* marked.js
* highlight.js


Platforms
---------
Any platform what supports python
* windows (tested on windows 7)
* Mac OSX (tested on Mountain Lion)
* Linux (not tested)