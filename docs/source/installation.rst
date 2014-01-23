Installation
============


It is recommended that you use `VirtualEnv <https://pypi.python.org/pypi/virtualenv>`_ in order to install the dependencies.  You will also need the python development libraries / headers in order to install the dependencies.  As well as libxml and libxslt.


First, create the virtual environment for installation::

   $ virtualenv reporting
   $ . reporting/bin/activate

Next, you need to install the dependencies::

   $ pip install premailer cheetah
   
Check out the report from github::

   $ git clone https://github.com/djw8605/hcc-usage-email.git
   

Testing
-------

You can run an example report quickly by manually running the update.py file::

   $ python update.py -e <email address>
   
You should receive an email shortly.



