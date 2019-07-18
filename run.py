import requests
import argparse
from BookDownloader import get_book 

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--fiction', help="Book belonging to fiction category")
parser.add_argument('-s', '--scientific', help="Book belonging to scientific category")
args = parser.parse_args()
if args.fiction:
	get_book(book_type="fiction", book_name=args.fiction)

elif args.scientific:
	get_book(book_type="scientific", book_name=args.scientific)

else:
	print("Enter a valid type :)")

