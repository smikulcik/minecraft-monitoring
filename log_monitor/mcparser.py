import re
import db

def parse(line):

	match =  re.match(
                '^\[(\d\d\:\d\d\:\d\d)\] \[(.+)\]: (.*)',
                line
        )

	if match is not None:
		timestr, category, message = match.groups()
	else:
		message = line

	if 'User Authenticator' in category:
		match = re.match('UUID of player (.+) is (.+)', message)

		if match is not None:
			username, uuid = match.groups()
			db.db.register(username, uuid)
			print "REGISTER " + username + " with " + uuid

	if 'Server thread/INFO' in category:
		match = re.match('(.+) joined the game', message)
		if match is not None:
			username = match.groups()[0]
			db.db.join(username, timestr)
			print username + " joined"

		match = re.match('(.+) left the game', message)
		if match is not None:
			username = match.groups()[0]
			db.db.leave(username, timestr)
			print username + " left"

		#[14:13:24] [Server thread/INFO]: com.mojang.authlib.GameProfile@
		#4ddf41c8[id=<null>,name=hhjabris,properties={},legacy=false] 
		#(/192.227.225.218:40543) lost connection: 
		#D[14:13:24] [Server thread/INFO]:
		# com.mojang.authlib.GameProfile@4ddf41c8[id=<null>,name=hhjabris,properties={},legacy=false] (/192.227.225.218:40543) lost connection: D
		match = re.match('(.+) lost connection: (.+)', message)
		if match is not None:
			username, reason = match.groups()
			print username + " lost connection"

		match = re.match('Starting minecraft server version (.+)', message)
		if match is not None:
			server_version = match.groups()[0]

			# As per policy, we do not count dangling logins from server crashes as logins
			db.db.remove_dead_logins()
			print "Started Server"
