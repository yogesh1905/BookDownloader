import json, os, io, requests, logging, subprocess
from bs4 import BeautifulSoup as BS
from urllib import parse

logging.basicConfig(level=logging.INFO)

class bcolors:
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'

def convert_to_djvu(book_name):
	logging.info('Converting...')
	subprocess.run(['djvups', './books/' + book_name + '.djvu', './books/out.ps'])
	subprocess.run(['ps2pdf', './books/out.ps', './books/' + book_name + '.pdf'])
	logging.info("Converted !")
	subprocess.run(['rm', './books/' + book_name + '.djvu'])
	subprocess.run(['rm', './books/out.ps'])	


def get_and_save_book(Soup, name="book.pdf"):
	links = Soup.find_all('a')
	book_link = ''
	for link in links:
		GET_link = link.get('href')
		if GET_link.endswith('.pdf') or GET_link.endswith('.djvu'):
			book_link = GET_link
			break
	
	if not book_link:
		raise ValueError('The page does not contain link to download')
	book_name = name.replace(' ', '_')
	logging.info("Downloading book from " + book_link)
	res = requests.get(book_link)
	extension = '.pdf'
	if(book_link.endswith('.djvu')):
		extension = '.djvu'
	file = open('./books/'+ book_name + extension, 'wb')
	file.write(res.content)
	file.close()
	logging.info("Book saved !")
	if extension == '.djvu':
		logging.info("Book Dowloaded in .djvu format. Want to convert to .pdf ? [Y/y]")
		user_input = input().lower()
		if user_input == 'y' or user_input == 'yes':
			try:
				convert_to_djvu(book_name)
			except Exception as e:
				logging.error("Couldn't convert to pdf :(")
				print(repr(e))
		elif user_input == 'n' or user_input == 'no':
			logging.info("Ok..")
		else:
			logging.error('Invalid input !')


 
def get_link_fiction(Soup, book_name):
	table = Soup.find('table', {'class':'catalog'})
	try:
		trows = table.find_all('tr')
	except Exception as e:
		raise ValueError("Sorry book not found :( Make sure you enter the correct book name and category")
	link = ''
	for trow in trows[1:]:
		tcol = trow.find_all('td')
		is_english = False
		is_pdf_or_djvu = False
		link_book_name = tcol[2].find('a').text
		if 'english' in tcol[3].text.lower():
			is_english = True
		if 'pdf' in tcol[4].text.lower() or 'djvu' in tcol[4].text.lower():
			is_pdf_or_djvu = True
		if is_english and is_pdf_or_djvu:
			link_col = tcol[5].find('ul', {'class': 'record_mirrors_compact'})
			link = link_col.find_all('li')[0].find('a').get('href')
			book_name = tcol[2].find('a').text
			break

	if link:
		return {'link': link, 'book_name': book_name}

	raise ValueError("No files found in English and pdf or djvu format!!!") 


def get_link_scientific(Soup, book_name):
	table = Soup.find('table', {'class': 'c'})
	try:
		trows = table.find_all('tr')
	except Exception as e:
		raise ValueError("Sorry book not found :( Make sure you enter the correct book name and category")
	link = ''
	for trow in trows[1:]:
		tcol = trow.find_all('td')
		is_english = False
		is_pdf_or_djvu = False
		link_book_name = tcol[2].find('a').text
		if 'english' in tcol[6].text.lower():
			is_english = True
		if 'pdf' in tcol[8].text.lower() or 'djvu' in tcol[8].text.lower():
			is_pdf_or_djvu = True
		if is_english and is_pdf_or_djvu:
			link_col = tcol[9].find('a')
			link = link_col.get('href')
			book_name = tcol[2].find('a').text
			unwanted_words = tcol[2].find('a').find_all('font')
			for unwanted_word in unwanted_words:
				book_name = book_name.replace(unwanted_word.text, '')
			break

	if link:
		return {'link': link, 'book_name': book_name}

	raise ValueError("No files found in English and pdf or djvu format!!!") 
	
	

def get_site_data(url):
	site = requests.get(url)
	data = site.content.decode('utf-8')
	Soup = BS(data, 'lxml')
	return Soup


def get_scientific_book(name):
	name_link = parse.quote_plus(name)
	url = 'https://libgen.is/search.php?req=' + name_link
	logging.info("Getting site data for the url " + url + "...")
	Soup = get_site_data(url)
	logging.info("Received site data...")
	returned_info = get_link_scientific(Soup, name)
	link = returned_info['link']
	name = returned_info['book_name']
	logging.info("Getting site data for the download url " + link + "...")
	Soup = get_site_data(link)
	logging.info("Received site data...")
	get_and_save_book(Soup, name)


	
def get_fiction_book(name):
	name_link = parse.quote_plus(name)
	url = 'https://libgen.is/fiction/?q=' + name_link + '&criteria=&language=&format='
	try:
		logging.info("Getting site data for the url " + url + "...")
		Soup = get_site_data(url)
		logging.info("Received site data...")
		returned_info = get_link_fiction(Soup, name)
		link = returned_info['link']
		name = returned_info['book_name']
		logging.info("Getting site data for the download url " + link + "...")
		Soup = get_site_data(link)
		logging.info("Received site data...")
		get_and_save_book(Soup, name)

	except ValueError as e:
		logging.warning(bcolors.WARNING + "Book not found in the first link searching in the next..." + bcolors.ENDC)
		get_scientific_book(name)


def get_book(**kwargs):
	os.makedirs("books", exist_ok=True)
	try:
		to_unicode = unicode
	except NameError:
		to_unicode = str

	book_type = kwargs['book_type']
	book_name = kwargs['book_name']
	try:
		if book_type == 'fiction':
			get_fiction_book(book_name)
		else:
			get_scientific_book(book_name)
		
		logging.info(bcolors.OKGREEN + "Successful" + bcolors.ENDC)
	
	except ConnectionError as e:
		logging.error(bcolors.FAIL + "Check for internet connectivity" + bcolors.ENDC)

	except ValueError as e:
		logging.error(bcolors.FAIL + str(e) + bcolors.ENDC)
	
	except Exception as e:
		logging.error(bcolors.FAIL + 'Something went wrong!!!' + bcolors.ENDC)	
		print(repr(e))

	


