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
            movie = client.get(title=title)
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

        logging.debug("getPoster TITLE: {} URL:{}".format(self.title, self.posterURL))
        print("getPoster TITLE: {} URL:{}".format(self.title, self.posterURL))

        # Only work with valid URLS
        if self.posterURL is None:
            return

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
