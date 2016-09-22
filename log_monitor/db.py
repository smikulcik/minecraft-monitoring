import sqlite3
import datetime
import os

DATAFILE = os.getenv('DATAFILE', '/var/minecraft/mc.db')

class Db:
	conn = None
	c = None

	def __init__(self):
		self.conn = sqlite3.connect(DATAFILE)
		self.c = self.conn.cursor()

	def create_schema(self):
		self.c.execute("DROP TABLE IF EXISTS players")
		self.c.execute("DROP TABLE IF EXISTS session")
		self.c.execute(
			'''CREATE TABLE players(
				uuid CHAR(50) PRIMARY KEY	NOT NULL,
				username text NOT NULL
			)'''
		)
		self.c.execute(
			'''CREATE TABLE sessions(
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				uuid CHAR(50)	NOT NULL,
				start DATETIME,
				end DATETIME,
				FOREIGN KEY(uuid) REFERENCES players(uuid)
			)'''
		)
		self.conn.commit()

	def get_uuid(self, username):
		result =  self.c.execute(
			"SELECT uuid FROM players WHERE username = '" +
			 username + "'").fetchall()

		if len(result) == 0:
			return None
		else:
			return result[0][0]  # first col in first row

	def register(self, username, uuid):
		if len(self.c.execute(
		"SELECT uuid FROM players WHERE uuid = '" + uuid + "'"
		).fetchall()) == 0:
			self.c.execute(
				"INSERT INTO players VALUES('" +
				uuid + "', '" + username + "')")
		else:
			self.c.execute(
				"UPDATE players SET username = '" +
				username + "' WHERE uuid = '" + uuid + "'")
		self.conn.commit()

	def join(self, username, timestr):
		uuid = self.get_uuid(username)
		if uuid is None:
			print "WARNING: NEW USER WITHOUT UUID"
			return

		# Remove any existing sessions as they should not exist
		self.remove_dead_logins(uuid)
		
		# Now create new session
		self.c.execute(
			"INSERT INTO sessions (uuid,start) VALUES('" + uuid + 
			"', '" + str(datetime.date.today()) + " " + timestr +
			 "')"
		)
		self.conn.commit()

	def leave(self, username, timestr):
		uuid = self.get_uuid(username)
		if uuid is None:
			print "WARNING: NEW USER WITHOUT UUID"
			return
		id = self.c.execute(
			"SELECT id FROM sessions WHERE uuid = '" +
			uuid + "' AND start in (SELECT MAX(start) " +
			"from sessions WHERE uuid='" + uuid + "' AND end is null)"
		).fetchone()[0]
		self.c.execute("UPDATE sessions SET end='" + 
			str(datetime.date.today()) + " " + timestr +
			"' WHERE id = " + str(id))
		self.conn.commit()

	def remove_dead_logins(self, uuid=None):

		if uuid is None:
			print "removing all dead logins"
			# remove all dead logins
			self.c.execute("DELETE FROM sessions WHERE id in (SELECT id FROM sessions WHERE end is null)")
		else:
			# remove dead logins for uuid
			self.c.execute("DELETE FROM sessions WHERE id in (SELECT id FROM sessions WHERE end is null and uuid = ?)", (uuid,))
			
		self.conn.commit()

	def get_playtime(self, uuid, from_dt=None, to_dt=None):
		"""
		Get number of hours played for user with uuid between from_dt(optional)
		and to_dt(optional)

		NOTE: This adds up the second part of session 1, session 2 and the first 
		part of session 3 as seen below.

		  start                        end
		     |                          |
		     V                          V
		(session 1)    (session 2)   (session 3)
		"""
		playtime = 0

		# Get session 1 time if from_dt exists
		if from_dt is not None:
			result = self.c.execute(
				"SELECT SUM(( JulianDay(end) - JulianDay(?) ) * 24 ) " + 
				"from sessions where uuid = ?", (from_dt, uuid)).fetchall()
			if len(result) > 0:
				playtime += result[0][0]

		# Get session 2 time
		query = ("SELECT SUM(( JulianDay(end) - JulianDay(start) ) * 24 ) " + 
			"from sessions where uuid = ?")
		args = [uuid,]
		if from_dt is not None:
			query += " and start > ?"
			args.append(from_dt)
		if to_dt is not None:
			query += " and end < ?"
			args.append(to_dt)
		result = self.c.execute(query, args).fetchall()

		if len(result) > 0:
			playtime += result[0][0]

		# Get session 3 if to_dt exists
		if to_dt is not None:
			result = self.c.execute(
				"SELECT SUM(( JulianDay(?) - JulianDay(start) ) * 24 ) " + 
				"from sessions where uuid = ?", (to_dt, uuid)).fetchall()
			if len(result) > 0:
				playtime += result[0][0]
		return playtime

	def display_db(self):
		players = self.c.execute("SELECT * FROM players")
		for uuid, player in players.fetchall():
			print player, self.get_playtime(uuid)
#		sessions = self.c.execute("SELECT * FROM sessions")
#		for s in sessions.fetchall():
#			print s

	def close(self):
		self.conn.close()
db = Db()
if __name__ == '__main__':
	db.display_db()
