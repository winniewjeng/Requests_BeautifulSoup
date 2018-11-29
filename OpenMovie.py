"""
This is a wrapper around the Open Movie Database python API module.
"""

import json
import logging
import os
import traceback
import urllib.request
import sqlalchemy
import ORM
import bs4
import requests
import omdb


class OpenMovie:
    """
    """

    def __init__(self, title=None, posterURL=None):
        """
        Constructor
        """

        # Save class data members
        self.title = title
        self.posterURL = posterURL
        self.posterFileName = None

        # os.mkdir will throw an exception if the directory already
        # exists, so catch it and move on
        try:
            os.mkdir("Posters")
        except:
            pass

        client = omdb.OMDBClient(apikey=os.environ['OMDB_API_KEY'])
        try:
            self.movie = client.get(title=title)
        except:
            logging.error("Could not get {} from omdb".format(title))

        return

    def __del__(self):
        """
        Destructor
        """
        print("Destructor Called")
        return

    def getPoster(self):
        """
        Download the poster for this title and save with the same name
        """

        try:
            # Set the posterURL to the ’poster’ element of the movie member
            self.posterURL = self.movie['poster']
        except:
            # If ’poster’ is not in our movie member, log and return False
            logging.warning("{} does not have a poster url".format(self.title))
            return False

        # Clear up the title of the movie poster name.  these symbols in a filename can create
        # problems for the OS and writing the file
        title = self.title
        title = title.replace("/", " ")
        title = title.replace("?", " ")
        title = title.replace(":", " ")
        title = title.replace(" ", "_")
        self.posterFileName = "Posters/"+title+".jpg"

        # retrieve the poster via the URL and save it off.  if something goes wrong look at the
        # traceback
        try:
            local_file, r = urllib.request.urlretrieve(self.posterURL, self.posterFileName)
        except Exception:
            logging.error("FAILED to download poster for {}".format(title))
            print(traceback.format_exc())
            logging.error(traceback.format_exc())
            return False

        return True

    def getAwards(self):
        """
        Download the awards section for a movie from IMDB
        Use requests to download and beau-soup to scrape the info
        """
        # check if movie has IMDB ID
        try:
            # extract the IMDB ID from OMDB
            # self.imbdID = self.movie['imbd_id']
            self.imbdID = "tt0499549"  # Avatar for testing purpose
        except:
            logging.warning("{} is not in imdb".format(self.title))
            return

        #  feed IMDB ID to the url string
        self.url = "https://www.imdb.com/title/{}/awards?ref =tt awd".format(self.imbdID)

        # request get the url and turn it into soup
        r = requests.get(self.url)

        # soup = bs4.BeautifulSoup(r.text)  # this is the canonical UCLA class example way
        soup = bs4.BeautifulSoup(r.text, "lxml")  # this is the only way to stop my program from throwing error

        # in the soup, find table with attributes 'class': 'awards'
        table = soup.find('table', attrs={'class': 'awards'})

        # if table comes back as None, set class member awardsDict to an empty dict and return
        self.awardDict = {}
        if table is None:
            # self.awardDict = {}
            logging.info("{} has won no award".format(self.title))
            return  # ??? do I return the empty dict or do i simply return?

        # find all rows in the table
        rows = table.find_all('tr')

        data = []
        for row in rows:
            cols = row.find_all('td')  # for each row, find all column and strip the text
            cols = [ele.text.strip() for ele in cols]  # Get rid of empty value from column
            data.append([ele for ele in cols if ele])  # append this to a list to keep track of it

        # plough through the list and find the winning categories
        index = True  # flag the first winning category
        for x in data:
            # don't print out the nominees
            if "Nominee" in x[0]:
                break  # break out of the function

            elif index is True:  # first winning category requires special parsing
                # print(x)
                # print("\n")
                for item in x:
                    if "Winner\nOscar" not in item: # this is what i want
                        sublist = item.split('\n')
                        print("|{}|".format(sublist))
                        award_flag = True  # the award category is always the first element of the sublist
                        award_key = ""
                        award_val = ""
                        for y in sublist:
                            if award_flag == True:
                                award_key = y  # this is the award category
                                award_flag = False  # after getting the key, flag to get the winners' names
                            else:
                                award_val += y
                                award_val += " "
                        self.awardDict[award_key] = award_val  # update dictionary
                        print(self.awardDict)
                index = False  # flag marks the end of first winning category

            else:  # the rest of the winning categories have same method for parsing
                list = x[0].split('\n')
                filteredList = filter(None, list)
                award_flag = True
                award_key = ""
                award_val = ""
                for element in filteredList:
                    if award_flag == True:
                        award_key = element  # first element of the filteredList is winning award category
                        award_flag = False
                    else:
                        award_val += element
                        award_val += " "
                        self.awardDict[award_key] = award_val  # update dictionary

        # print(self.awardDict)  # testing purpose. comment out
        return self.awardDict

    def getMovieTitleData(self):
        """
        Get the database information for this title
        """
        # Query the database for all movies with this title
        try:
            movieTitleQuery = ORM.session.query(
                ORM.Movies).filter(ORM.Movies.title == self.title).one()
        except sqlalchemy.orm.exc.NoResultFound:
            logging.error("Movie Not in Database {}".format(self.title))
            print("getMovieTitle Movie Not in Database {}".format(self.title))
            return False

        return movieTitleQuery

    def getCast(self):
        """
        Get the cast list for the movie
        """

        try:
            movieCreditsQuery = ORM.session.query(
                ORM.Credits).filter(ORM.Credits.title == self.title)
        except:
            logging.error("getCast failed on ORM query")
            print("getCast failed on ORM query")
            return False

        # Try to get the cast and crew informatioon
        try:
            cast = json.loads(movieCreditsQuery[0].cast)
        except:
            logging.error(
                "getCast: Failed to retrieve movie or credits"
            )
            print(traceback.format_exc())
            logging.error(traceback.format_exc())

            return False

        return cast

    def getCrew(self):
        """
        Get the director and the crew for the movie
        """
        director = "NONE"
        print(self.title)
        try:
            movieCreditsQuery = ORM.session.query(
                ORM.Credits).filter(ORM.Credits.title == self.title)
        except:
            logging.error("getCast failed on ORM query")
            print("getCrew failed on ORM query")
            return False, False

        # Try to get the cast and crew informatioon
        try:
            crew = json.loads(movieCreditsQuery[0].crew)
        except:
            logging.error(
                "getCrew: Failed to retrieve credits"
            )
            print(traceback.format_exc())
            logging.error(traceback.format_exc())

            return False, False

        try:
            for x in crew:
                if x['job'] == 'Director':
                    director = x['name']
        except:
            logging.error("No crew or director")
            print("No crew or director")
            return False

        return director, crew


#  testing purpose. Comment out later
if __name__ == "__main__":
    print("Hello World")
    op = OpenMovie()
    op.getAwards()