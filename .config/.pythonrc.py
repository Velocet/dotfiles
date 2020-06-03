#!/usr/bin/env python3
#$XDG_CONFIG_HOME/.pythonrc.py
#FROM: https://gist.github.com/taavi223/1340876/7fcbec09a4f9dd4ee9bbafcfec5ce94c9decb8fb

#######################
# IMPORTS & CONSTANTS #
#######################

import imp
import os
import sys
import re
import threading
import time

VIRTUAL_ENV = os.environ.get('VIRTUAL_ENV', None)
HOME = VIRTUAL_ENV or os.environ.get('WORKON_HOME', None) or os.environ['HOME']

#################################
# SAVE & RESTORE HISTORY STATES #
#################################

try:
    import readline
except ImportError:
    pass
else:

    ##################
    # TAB COMPLETION #
    ##################

    try:
        import rlcompleter
    except ImportError:
        pass
    else:
        if(sys.platform == 'darwin'):
            # Work around a bug in Mac OS X's readline module.
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")

    ######################
    # PERSISTENT HISTORY #
    ######################

    # Use separate history files for each virtual environment.
    HISTFILE = os.path.join(HOME, '.pyhistory')

    # Read the existing history if there is one.
    if os.path.exists(HISTFILE):
        try:
            readline.read_history_file(HISTFILE)
        except:
            # If there was a problem reading the history file then it may have
            # become corrupted, so we just delete it.
            os.remove(HISTFILE)

    # Set maximum number of commands written to the history file.
    readline.set_history_length(256)

    def savehist():
        try:
            readline.write_history_file(HISTFILE)
        except NameError:
            pass
        except Exception as err:
            print("Unable to save history file due to the following error: %s"
                  % err)

    # Register the ``savehist`` function to run when the user exits the shell.
    import atexit
    atexit.register(savehist)

#################
# COLOR SUPPORT #
#################

class TermColors(dict):
    """Gives easy access to ANSI color codes. Attempts to fall back to no color
    for certain TERM values. (Mostly stolen from IPython.)"""

    COLOR_TEMPLATES = (
        ("Black"       , "0;30"),
        ("Red"         , "0;31"),
        ("Green"       , "0;32"),
        ("Brown"       , "0;33"),
        ("Blue"        , "0;34"),
        ("Purple"      , "0;35"),
        ("Cyan"        , "0;36"),
        ("LightGray"   , "0;37"),
        ("DarkGray"    , "1;30"),
        ("LightRed"    , "1;31"),
        ("LightGreen"  , "1;32"),
        ("Yellow"      , "1;33"),
        ("LightBlue"   , "1;34"),
        ("LightPurple" , "1;35"),
        ("LightCyan"   , "1;36"),
        ("White"       , "1;37"),
        ("Normal"      , "0"),
    )

    NoColor = ''
    _base  = '\001\033[%sm\002'

    def __init__(self):
        if os.environ.get('TERM') in ('xterm-color', 'xterm-256color', 'linux',
                                    'screen', 'screen-256color', 'screen-bce'):
            self.update(dict([(k, self._base % v) for k,v in self.COLOR_TEMPLATES]))
        else:
            self.update(dict([(k, self.NoColor) for k,v in self.COLOR_TEMPLATES]))
_c = TermColors()

################################
# PRETTY PRINT OUTPUT & ERRORS #
################################

# NOTE: there is a bug (at least on Mac OS X) that causes the following lines to
# garble the command history whenever there are long lines. Try enabling them
# and using the up/down arrows to cycle through your history.

# Make the prompts colorful.
# sys.ps1 = "%s>>>%s" % (_c['LightGreen'], _c['Normal'])
# sys.ps2 = "%s...%s" % (_c['LightPurple'], _c['Normal'])

# Enable pretty printing for STDOUT
def my_displayhook(value):
    if value is not None:
        # TODO: What's the point of this anyway?
        try:
            import __builtin__
            __builtin__._ = value
        except ImportError:
            __builtins__._ = value

        import pprint
        pprint.pprint(value)
        del pprint
sys.displayhook = my_displayhook

# Make errors and tracebacks stand out a bit more.
def my_excepthook(type, value, tb):
    sys.stderr.write(_c['Yellow'])
    import traceback
    output = traceback.print_exception(type, value, tb)
    del traceback
    sys.stderr.write(_c['Normal'])

    # NOTE: There is a bug (?) in Python 3, where a trailing color marker that's
    # written to STDERR or STDOUT by itself does not color the subsequent lines.
    # We work around this by manually calling ``flush`` afterwards.
    sys.stderr.flush()
sys.excepthook = my_excepthook

############################
# SETUP DJANGO ENVIRONMENT #
############################

# TODO: Search for a settings.py file, then add that directory?
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    try:
        from django.core.management import setup_environ

        # Add the 'www' subfolder in the virtualenv to the path.
        # If you're not in a virtualenv, we assume your django project folder is
        # already on your python path.
        if VIRTUAL_ENV:
            sys.path.append(os.path.join(VIRTUAL_ENV, 'www'))

        # Try to import and setup a django settings module.
        import settings
        setup_environ(settings)

        # Cleanup the namespace a bit.
        del setup_environ
        del settings
    except ImportError:
        pass

# Load Common Django Utilities
if 'DJANGO_SETTINGS_MODULE' in os.environ:
    from django.test.client import Client
    from django.conf import settings as S

    from django.db.models.query import Q
    from django.db.models.expressions import F
    from django.db.models.aggregates import *

    class DjangoModels(object):
        """Loop through all the models in INSTALLED_APPS and import them."""
        def __init__(self):
            from django.db.models.loading import get_models
            for m in get_models():
                setattr(self, m.__name__, m)

    M = DjangoModels()
    C = Client()

######################################
# AUTOMATICALLY RELOAD CHANGED FILES #
######################################

class WatchdogThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__ (self, directory):
        super(WatchdogThread, self).__init__()

        # Set it so that the thread automatically exits when its parent exits.
        self.daemon = True

        self._stopped = threading.Event()
        self._initialized = threading.Event()

        # The regular expression for matching valid files in the directory.
        self.regex = re.compile('^[a-zA-Z_][a-zA-Z_0-9]*\.py$')

        # Add the directory to the system's path, so that we can import from it.
        self.directory = os.path.abspath(directory)
        sys.path.append(self.directory)

        self.mtimes = {}

    def stop(self):
        """Stops the thread and waits for it to finish execution."""
        self._stopped.set()
        self.join()

    def is_stopped(self):
        """Returns whether or not the thread has been stopped."""
        return self._stopped.is_set()

    def is_initialized(self):
        """Returns whether the thread has finished its first pass of the
        given directory."""

        return self._initialized.is_set()

    def add(self, path):
        """Allows a user to add additional directories or modules which
        should be watched for changes."""
        raise NotImplementedError

    def run(self):
        while not self.is_stopped():
            try:
                # Loop over all the files in the specified directory that match
                # the regular expression.
                for filename in os.listdir(self.directory):
                    if self.regex.match(filename) is None:
                        continue

                    # Extract the module name.
                    modulename = filename.rsplit('.', 1)[0]

                    # Check to see if the file has been modified since we last
                    # scanned it.
                    filepath = os.path.abspath(os.path.join(
                        self.directory,
                        filename,
                    ))
                    new_mtime = os.path.getmtime(filepath)
                    old_mtime = self.mtimes.get(modulename, None)

                    # If the file hasn't been modified, we move on.
                    if new_mtime == old_mtime:
                        continue

                    try:
                        try:
                            imported = False
                            module = imp.reload(sys.modules[modulename])
                        except KeyError:
                            imported = True
                            module = __import__(modulename)

                        # Work out the paths to the module and file, sans
                        # extensions, so that we can figure out if we imported
                        # the right thing.
                        modulepath = os.path.abspath(module.__file__)
                        base_modulepath = os.path.splitext(modulepath)[0]
                        base_filepath = os.path.splitext(filepath)[0]

                        # Make sure we imported or reloaded the correct module.
                        if base_modulepath != base_filepath:
                            sys.stderr.write("%sThe scratchpad file '%s' "
                                             "conflicts with a built-in "
                                             "module.%s\n" % (_c['LightRed'],
                                             filename, _c['Normal']))
                        else:
                            globals()[modulename] = module
                            verb = imported and 'Imported' or 'Reloaded'
                            sys.stdout.write("%s%s the scratchpad file "
                                             "'%s'.%s\n" % (_c['LightGreen'],
                                             verb, filename, _c['Normal']))

                    # Let the user know if we couldn't import or reload one of
                    # the modules, so that they can correct the errors.
                    except Exception as err:
                        verb = imported and 'import' or 'reload'
                        sys.stderr.write("%sUnable to %s the scratchpad file "
                                         "'%s'.%s" % (_c['LightRed'], verb,
                                         filename, _c['Normal']))

                        # Print the traceback.
                        sys.stderr.write(_c['Yellow'])
                        import traceback
                        traceback.print_exc()
                        del traceback
                        sys.stderr.write(_c['Normal'])

                    # Update the last known mtime for the module.
                    self.mtimes[modulename] = new_mtime
            except OSError:
                # If the watched directory doesn't exist, we fail gracefully.
                pass
            finally:
                # Mark that the threads first pass has been completed.
                if not self.is_initialized():
                    self._initialized.set()
                time.sleep(1)

# Start the watchdog thread, localizing it to the current virtualenv.
watchdog = WatchdogThread(os.path.join(HOME, 'scratchpad'))
watchdog.start()

# Wait until the watchdog thread has finished its first scan of the scratchpad
# directory, so that prompt shows up after the import messages, like it should.
while not watchdog.is_initialized():
    time.sleep(.01)
