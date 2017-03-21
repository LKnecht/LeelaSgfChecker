from subprocess import PIPE, Popen
import os, sys

import sgf

leela_path = "./Leela090/leela_090_linux_x64"
skip_opening_moves = 0	#number of the first moves to skip checking


#~ LIST OF GTP COMMANDS: list_commands

GTP_POS = ' abcdefghjklmnopqrstuvwxyzABCDEFGHJKLMNOPQRSTUVWXYZ'

def sgf2gpt_move(sgf_move):
	'''convert the move coordinate from sgf to gtp.
	Note that gtp skips the 'i'.'''
	if len(sgf_move) < 2:
		print("whywhywhywhywhyw?!")
		return ""
	x = GTP_POS[sgf.SGF_POS.find(sgf_move[0])]
	y = sgf.SGF_POS.find(sgf_move[1])
	return "{}{}".format(x, y)


def analyze(sgf_string, player_name):
	'''Analyzes the sgf_string on how many moves of player_name are matching leelas moves.
	Returns a tuple containing the moves matching to leelas moves and the total number of moves.'''
	#initialize
	coll = sgf.parse(sgf_string)
	if len(coll) == 0:
		print("No game in sgf found")
		return
	if len(coll) > 1:
		print("Multiple games in sgf found, using the first!")
	game_iterator = coll[0].__iter__()
	meta = game_iterator.__next__().properties
	player_white = meta['PW'][0]
	player_black = meta['PB'][0]
	
	player_color = None
	if player_white == player_name:
		player_color = 'W'
	elif player_black == player_name:
		player_color = 'B'
	else:
		print("{} doesn't match with either black or white player".format(player_name))
		return None
	print("\nStart Analysis for {} (b) vs {} (w)\ncomparing {} with Leela's moves\n".format(
		player_black, player_white, player_name))
	
	movelist = []
	leelas_move = None
	move_counter = 0
	leela_moves_played = 0
	for i, node in enumerate(game_iterator):
		prop = node.properties
		for c in ['B', 'W']:
			if c in prop:
				movelist.append( (c, sgf2gpt_move(prop[c][0])) )
				break
		if i + 1 < skip_opening_moves:
			continue
		
		if not leelas_move is None and not leelas_move == "":
			move = movelist[-1][1]
			print("#{} {}: {} leela: {}".format(i+1, player_name, move, leelas_move), end='')
			move_counter += 1
			if move == leelas_move:
				leela_moves_played += 1
				print("\t<-- {} match".format(leela_moves_played), end='')
			print()
		else:
			print("#{} {}: {}".format(i+1, movelist[-1][0], movelist[-1][1]))
			
		
		# probably bad solution?
		# start leela, manually play all moves in movelist
		# and then get the result of genmove:
		
		next_color = movelist[-1][0]
		if next_color == 'W': next_color = 'B'
		else: next_color = 'W'
		
		if next_color == player_color:
		
			leela_input = ''
			for move in movelist:
				leela_input += 'play {} {}\n'.format(move[0], move[1])
			leela_input += 'genmove {}'.format(next_color)
			
			leela = Popen([leela_path, "--gtp", "--quiet"], stdin=PIPE, stdout=PIPE, bufsize=1)
			res = leela.communicate(input=leela_input.encode())[0]
			leela.stdin.close()
			
			if len(res) > 12:
				res = res[-7:]
			leelas_move = res[res.find(b'\n= ')+3:res.find(b'\n\n', res.find(b'\n= '))].decode().lower()
			leelas_move = leelas_move.replace('\n', '')
		else:
			leelas_move = None
	
	if move_counter == 0: move_counter = 1
	print("\n\nResult of analysis: {} / {} ({}%) leela moves played".format(leela_moves_played, move_counter, leela_moves_played * 100. / move_counter))
	return leela_moves_played, move_counter

def analyze_collection(sgf_subfolder, player_name):
	'''Analyze the sgf collection in the folder sgf_subfolder.
	Returns a tuple containing the number of games, 
	the number of moves leela would have played too
	and the total number of moves.'''
	games, leela_moves_played, move_counter = (0,0,0)
	history = []
	for filename in os.listdir(sgf_subfolder):
		if not filename.endswith(".sgf"):
			continue
		filename = os.path.join(sgf_subfolder, filename)
		sgf = open(filename, 'r').read()
		
		res = analyze(sgf, player_name)
		if res is None:
			continue
		leelas_moves, moves = res
		games += 1
		leela_moves_played += leelas_moves
		move_counter += moves
		history.append( (filename, leelas_moves, moves ) )
	print("\n\nRESULT:")
	for h in history:
		print("{}\t{} / {} ({}%)".format(h[0], h[1], h[2], h[1] * 100. / h[2]))
	print("\nGames: \t{}\nleela moves:\t{}\nmoves total\t{}\n%\t\t{}%".format(
		games, leela_moves_played, move_counter, leela_moves_played * 100. / move_counter))
	return games, leela_moves_played, move_counter

if __name__ == '__main__':
	argv = sys.argv[1:]
	if len(argv) != 2:
		print("Usage: python leelasgfchecker.py PLAYER_NAME SGF-FOLDER[/FILENAME]")
		exit()
	player_name, path = argv
	if path.endswith('.sgf'):
		try:
			sgf_string = open(path, 'r').read()
			analyze(sgf_string, player_name)
		except KeyboardInterrupt:
			print("Aborted.")
			exit()
	else:
		try:
			analyze_collection(path, player_name)
		except KeyboardInterrupt:
			print("aborted.")
			exit()
		

