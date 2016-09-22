import pyinotify
import mcparser

LOGFILE = '/var/log/minecraft/minecraft.log'
with open(LOGFILE) as fd:
	lines = fd.readlines()
	log_num_lines = len(lines)

def get_change(log_file):
	with open(log_file) as fd:
		lines = fd.readlines()
		new_num_lines = len(lines)
		global log_num_lines
		if(log_num_lines is not None and new_num_lines > log_num_lines):
			new_lines = lines[-1 * (new_num_lines - log_num_lines):]
		else:
			new_lines = []
		log_num_lines = new_num_lines
		return new_lines

class MyEventHandler(pyinotify.ProcessEvent):
	def process_IN_MODIFY(self, event):
		for ch in get_change(LOGFILE):
			mcparser.parse(ch)

def main():
    # watch manager
    wm = pyinotify.WatchManager()
    wm.add_watch(LOGFILE, pyinotify.ALL_EVENTS, rec=True)

    # event handler
    eh = MyEventHandler()

    # notifier
    notifier = pyinotify.Notifier(wm, eh)
    notifier.loop()

if __name__ == '__main__':
    main()
