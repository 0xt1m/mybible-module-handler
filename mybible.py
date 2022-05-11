import sqlite3
import re
import string

class Book:
	def __init__(self, book_number, short_name, long_name, book_color):
		self.book_number = book_number
		self.short_name = short_name
		self.long_name = long_name
		self.book_color = book_color

	def __str__(self):
		return self.long_name


class Verse:
	def __init__(self, book_number, chapter, verse, text):
		self.book_number = book_number
		self.chapter = chapter
		self.verse = verse
		self.text = self.strip_tags(text)

	def __str__(self):
		return self.text

	def strip_tags(self, text = None):
		if text is None:
			text = self.text

		text = re.sub("<[Smf]>([^<]+)</[Smf]>", "", text)
		text = re.sub("<[iJet]>([^<]+)</[iJet]>", "\\1", text)
		text = re.sub("<n>([^<]+)</n>", "[\\1]", text)

		text = text.replace("<br/>", "").replace("<pb/>", "")

		text = re.sub("<h>([^<]+)</h>", "", text)

		return text.strip()


class Mybible:
	def __init__(self, filename):
		self.bible_file = filename

		self.connection = sqlite3.connect(filename, check_same_thread=False)
		self.cursor = self.connection.cursor()

		self.all_books = self.__get_all_books()
		self.all_verses = self.__get_all_verses()

		self.__create_search_table()

		self.all_search_verses = self.__get_all_search_verses()


	def __create_search_table(self):
		if self.all_verses == None:
			self.all_verses = self.__get_all_verses()

		try:
			self.cursor.execute("""CREATE TABLE verses_search (
				"book_number"	NUMERIC NOT NULL,
				"chapter"	NUMERIC NOT NULL,
				"verse"	NUMERIC NOT NULL,
				"text"	TEXT NOT NULL DEFAULT ''
			);""")
		except:
			pass
		check = self.cursor.execute(f"SELECT * FROM verses_search WHERE book_number=10 AND chapter=1 AND verse=1").fetchall()
		if not check:
			for v in self.all_verses:
				text = v.text.translate(str.maketrans('', '', string.punctuation)).lower().replace("„", "")
				text = text.replace("а́", "а").replace("є́", "є")
				text = text.replace("е́", "е").replace("и́", "и")
				text = text.replace("і́", "і").replace("ї́", "ї")
				text = text.replace("о́", "о").replace("у́", "у")
				text = text.replace("ю́", "ю").replace("я́", "я")		
				self.cursor.execute(f"INSERT INTO verses_search VALUES (?, ?, ?, ?)", (v.book_number, v.chapter, v.verse, text))

			self.connection.commit()
		

	def __get_all_books(self):
		all_books = self.cursor.execute("SELECT * FROM books").fetchall()
		res = [Book(b[0], b[1], b[2], b[3]) for b in all_books]
		return res


	def __get_all_verses(self):
		all_verses = self.cursor.execute("SELECT * FROM verses").fetchall()
		res = [Verse(v[0], v[1], v[2], v[3]) for v in all_verses]
		return res

	def __get_all_search_verses(self):
		all_search_verses = self.cursor.execute("SELECT * FROM verses_search").fetchall()
		res = [Verse(v[0], v[1], v[2], v[3]) for v in all_search_verses]
		return res
	
	def book_to_number(self, book):
		book = book.lower().replace("i", "і")
		for b in self.all_books:
			b_l = b.long_name.lower().replace("i", "і")
			b_s = b.short_name.lower().replace("i", "і")
			# print(book + " <><> " + b_l)
			if book in b_l or book in b_s:
				return b.book_number
			if len(b.short_name.split()) == 2:
				try_line = b.short_name.split()
				try_line = "".join((try_line[0], try_line[1])).lower()
				if book.lower() in try_line:
					return b.book_number
		return 0

	
	def get_book_index_by_number(self, book_number):
		for i in range(len(self.all_books)):
			if self.all_books[i].book_number == book_number:
				return i


	def get_book_title_by_number(self, book_number):
		for i in range(len(self.all_books)):
			if self.all_books[i].book_number == book_number:
				return self.all_books[i].long_name

	
	def get_book_by_number(self, book_number):
		b = self.cursor.execute(f"SELECT * FROM books WHERE book_number={book_number}").fetchall()
		book = Book(b[0][0], b[0][1], b[0][2], b[0][3])
		return book

	
	def get_verse(self, book_number, chapter, verse):
		verse_db = self.cursor.execute(f"""SELECT * FROM verses WHERE book_number={book_number}
			AND chapter={chapter} AND verse={verse}""").fetchall()
		verse = Verse(verse_db[0][0], verse_db[0][1], verse_db[0][2], verse_db[0][3])
		return verse

	
	def get_verses(self, book_number, chapter):
		res = []
		verses = self.cursor.execute(f"SELECT * FROM verses WHERE book_number={book_number} AND chapter={chapter}").fetchall()
		res = [Verse(v[0], v[1], v[2], v[3]) for v in verses]
		return res

	
	def count_of_chapters(self, book_number):
		chapters = self.cursor.execute(f"SELECT chapter FROM verses WHERE book_number={book_number}").fetchall()
		chapters = list(set(chapters))
		return len(chapters)

	
	def find(self, query):
		query_s = query.split()
		if len(query_s) < 3:
			raise ValueError("Something wrong")
		elif len(query_s) == 3:
			book = query_s[0]
			chapter = query_s[1]
			verse = query_s[2]
		elif len(query_s) == 4:
			book = " ".join((query_s[0], query_s[1])).strip()
			chapter = query_s[2]
			verse = query_s[3]
		elif len(query_s) > 4:
			raise ValueError("Something wrong")

		book_number = self.book_to_number(book)

		verse_db = None
		try:
			verse_db = self.cursor.execute(f"""SELECT * FROM verses WHERE book_number={book_number}
				AND chapter={chapter} AND verse={verse}""").fetchall()
		except:
			raise ValueError("Something wrong")

		verse = None
		try:
			verse = Verse(verse_db[0][0], verse_db[0][1], verse_db[0][2], verse_db[0][3])
		except:
			raise ValueError("Nothing found")
		return verse

	
	def find_by_text(self, query_text):
		if self.all_verses == None:
			self.all_verses = self.__get_all_verses()
		for v in self.all_verses:
			text = v.text.lower()
			if query_text.lower() in text:
				return v
		raise ValueError("Nothing found")

	
	def find_all_by_text(self, query_text):
		if self.all_verses == None:
			self.all_verses = self.__get_all_verses()

		res = []
		for v in self.all_verses:
			text = v.text.translate(str.maketrans('', '', string.punctuation)).lower().replace("„", "")
			text = text.replace("а́", "а").replace("є́", "є")
			text = text.replace("е́", "е").replace("и́", "и")
			text = text.replace("і́", "і").replace("ї́", "ї")
			text = text.replace("о́", "о").replace("у́", "у")
			text = text.replace("ю́", "ю").replace("я́", "я")
			if query_text.lower() in text:
				res.append(v)
		if res == []:
			raise ValueError("Nothing found")
		return res


# import time
# start_time = time.time()

# bible = Mybible("bible_translations/UBIO'88.SQLite3")

# print(time.time() - start_time)