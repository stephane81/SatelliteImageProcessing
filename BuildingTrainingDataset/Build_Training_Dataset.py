import numpy as np
import pandas as pd
import datetime
import os
import sys

import urllib2
import json
import webbrowser
import xmltodict

# shapefile
import matplotlib.pyplot as plt
import matplotlib.path as mplp
import shapefile

# import private keys
from my_keys import stephane_gooogle_api_key, stephane_zillow_api_key


class LocalDatabase(object):

    def __init__(self,  in_local_database_filepath='', in_local_database_filename='database.csv'):
        self.column_names = ['row1','row2']
        self.filepath = in_local_database_filepath
        self.filename = in_local_database_filename
        self.df_local = pd.DataFrame()

    def load_local_database(self):

        if os.path.isfile(self.filepath + self.filename):
            print self.filepath + self.filename, " loaded from disk"
            self.df_local = pd.read_csv(self.filepath + self.filename)
        else:
            print "Creating new file for local database..."
            self.df_local = pd.DataFrame(columns=self.column_names)

    def save_local_database(self):

        if os.path.isfile(self.filepath + self.filename):
            old = pd.read_csv(self.filepath + self.filename)
            if not os.path.exists(self.filepath  + "backup/"):
                os.makedirs(self.filepath + "backup/")
            print
            old.to_csv(
                path_or_buf=self.filepath + "backup/" + self.filename + datetime.datetime.now().__str__().replace(":", ";") + ".csv")
            # print self.filename + " already exists ... Backup created before overwriting"

        self.df_local.to_csv(path_or_buf=self.filepath + self.filename, index=False)
        print self.filepath + self.filename + " saved on disk "


class GoogleMapsApiWrapper(object):

    def __init__(self,in_google_api_key):

        self.google_api_key = in_google_api_key

    @staticmethod
    def get_google_formatted_address_from_gps_coordinates(in_latitude, in_longitude):

        # url = 'https://maps.googleapis.com/maps/api/geocode/xml?&latlng=37.7557210617,-122.124042102'
        url = 'https://maps.googleapis.com/maps/api/geocode/xml?&latlng=' + str(in_latitude) + ',' + str(in_longitude)
        xml_address = urllib2.urlopen(url).read()
        dict_address = xmltodict.parse(xml_address)
        if dict_address[u'GeocodeResponse'][u'status'] == 'OK':
            return dict_address[u'GeocodeResponse'][u'result'][0][u'formatted_address']
        else:
            print "Error getting address from gps coordinates. Google maps API Error code:", \
                dict_address[u'GeocodeResponse'][u'status']

    def get_google_gps_coordinates_from_address(self, in_address='Hamilton ave, Campbell, CA'):

        address = in_address.replace(", ", ",").replace(" ,", ",").replace("  ", "+").replace(" ", "+")
        json_geocode = urllib2.urlopen(
            'https://maps.googleapis.com/maps/api/geocode/json?address=' + address + '&key=' + self.google_api_key).read()
        if json.loads(json_geocode)['status'] == 'OK':
            print "Formated Address: \n", json.loads(json_geocode)['results'][0]['formatted_address'], '\n'
            print "GPS Coordinates: \n", json.loads(json_geocode)['results'][0]['geometry']['location']
            latitude = json.loads(json_geocode)['results'][0]['geometry']['location']['lat']
            longitude = json.loads(json_geocode)['results'][0]['geometry']['location']['lng']
            return latitude, longitude
        else:
            print "Error Code:", json.loads(json_geocode)['status']

    def list_of_gps_coordinates_to_google_url_using_paths(self, in_list_shape_points):

        url_path = "&path=color:0x0000ff|weight:5"
        for index in range(len(in_list_shape_points)):
            point = in_list_shape_points[index]
            # print point
            url_path = url_path + "|" + str(point[1]) + "," + str(point[0])
        url = 'https://maps.googleapis.com/maps/api/staticmap?maptype=satellite&size=640x640&key=' \
              + self.google_api_key + url_path
        return url

    @staticmethod
    def plot_png_file_object(in_png_file_object):

        filename = "my_image.png"
        file_out = open(filename, "wb")
        file_out.write(in_png_file_object)
        file_out.close()
        webbrowser.open(filename)

    def plot_shape_on_googlemap_using_path_center_and_zoom(self, in_list_shape_points, in_center, in_zoom=19):

        center_lat, center_lon = in_center
        url = self.list_of_gps_coordinates_to_google_url_using_paths(in_list_shape_points=in_list_shape_points) \
              + '&center=' + str(center_lat) + ',' + str(center_lon) + '&zoom=' + str(in_zoom)
        print url
        print "length of url(max 2048):", len(url)
        staticmap = urllib2.urlopen(url).read()
        self.plot_png_file_object(staticmap)

    def plot_shape_on_googlemap_using_path(self, in_list_shape_points):
        url = self.list_of_gps_coordinates_to_google_url_using_paths(in_list_shape_points=in_list_shape_points)
        print url
        print "length of url(max 2048):", len(url)
        staticmap = urllib2.urlopen(url).read()
        self.plot_png_file_object(staticmap)


class ShapefileWrapper(object):

    @staticmethod
    def open_shapefile(in_shapefile_filepath, in_shapefile_filename):
        shapefile_object = shapefile.Reader(in_shapefile_filepath + in_shapefile_filename)
        return shapefile_object.shapes()

    @staticmethod
    def center_of_shape(in_shape):
        # to do compute centroid
        bbox = in_shape.bbox
        center_lat = (bbox[1] + bbox[3]) / 2
        center_lon = (bbox[0] + bbox[2]) / 2
        return center_lat, center_lon


    def describe_shapefile(self, in_shapefile_filepath, in_shapefile_filename, in_index_shape=0):
        shapes = self.open_shapefile(in_shapefile_filepath=in_shapefile_filepath, in_shapefile_filename=in_shapefile_filename)
        print "properties of shapefile:"
        print "number of shapes:", len(list(shapes))
        print "list of the different types of shape:", set([x.shapeType for x in shapes]), " 5 means polygon"
        print "\nProperties of shape number:", in_index_shape
        print "coordinates of the box that includes the shape:", shapes[in_index_shape].bbox  #
        center_lat , center_lon = self.center_of_shape(in_shape = shapes[in_index_shape])
        print "coordinates of the center of the box :", center_lat, center_lon
        #print "address:", self.get_google_address_from_gps_coordinates(in_latitude=center_lat, in_longitude=center_lon)
        print "number of parts in shape  :", shapes[in_index_shape].parts
        print "number of points in shape  :", len(shapes[in_index_shape].points)
        print "points describing shape  :", shapes[in_index_shape].points
        self.plot_shape(in_shape=shapes[in_index_shape])

    @staticmethod
    def plot_shape(in_shape):
        # from Ed Smith
        # http://stackoverflow.com/questions/32991649/matplotlib-imshow-how-to-apply-a-mask-on-the-matrix
        lon_min, lat_min, lon_max, lat_max = in_shape.bbox
        m_path = mplp.Path(in_shape.points)
        x, y = np.arange(lon_min, lon_max, (lon_max - lon_min) / 100), np.arange(lat_min, lat_max, (
        lat_max - lat_min) / 100)  # create a grid inside bbox
        X, Y = np.meshgrid(x, y)
        points = np.array((X.flatten(), Y.flatten())).T  # flatten to 1D list of points to apply function
        mask = m_path.contains_points(points).reshape(X.shape)  # reshape as 2D matrix to plot
        plt.imshow(mask, origin='lower')


class ZillowApiWrapper(object):

    def __init__(self, in_zillow_api_key):
        self.zillow_api_key = in_zillow_api_key

    def list_of_comparable_houses_from_zpid(self, in_zpid, in_number_of_houses=25):
        # xml_list_houses = urllib2.urlopen('http://www.zillow.com/webservice/GetDeepComps.htm?zws-id=X1-ZWz1fcbgun7uh7_9od0r&zpid=48749425&count=5').read()
        xml_list_houses = urllib2.urlopen(
            'http://www.zillow.com/webservice/GetDeepComps.htm?zws-id=' + self.zillow_api_key + '&zpid=' + in_zpid + '&count=' + str(
                in_number_of_houses)).read()
        # save file
        file_object = open('list_zillow_houses.xml', mode="w")
        file_object.write(xml_list_houses)
        file_object.close()
        # extract seulement les zpid
        dict_list_houses = xmltodict.parse(xml_list_houses)
        if dict_list_houses['Comps:comps']['message']['code'] != '0':
            print "Probleme de request... code:", dict_list_houses['Comps:comps']['message']['code']


        else:
            list_zpids = []
            for index in range(min(in_number_of_houses, len(
                    dict_list_houses['Comps:comps']['response']['properties']['comparables']['comp']))):
                list_zpids.append(
                    dict_list_houses['Comps:comps']['response']['properties']['comparables']['comp'][index]['zpid'])
            return list_zpids

    def extract_property_feature_from_zpid(self, in_zpid):
        # in_zpid = "25058473"
        # http://www.zillow.com/webservice/GetUpdatedPropertyDetails.htm?zws-id=X1-ZWz1fcbgun7uh7_9od0r&zpid=25058473
        xml_property_details = urllib2.urlopen(
            'http://www.zillow.com/webservice/GetUpdatedPropertyDetails.htm?zws-id=' + self.zillow_api_key + '&zpid=' + in_zpid).read()
        # extract seulement les zpid
        dict_property_details = xmltodict.parse(xml_property_details)
        status_code = dict_property_details['UpdatedPropertyDetails:updatedPropertyDetails']['message']['code']
        if status_code != '0':
            raise Exception("Problem when extracting property features", status_code)
        else:
            df_address = pd.DataFrame(
                dict_property_details['UpdatedPropertyDetails:updatedPropertyDetails']['response']['address'],
                index=[0])
            df_links = pd.DataFrame(
                dict_property_details['UpdatedPropertyDetails:updatedPropertyDetails']['response']['links'], index=[0])
            df_edited_facts = pd.DataFrame(
                dict_property_details['UpdatedPropertyDetails:updatedPropertyDetails']['response']['editedFacts'],
                index=[0])
            df_all = pd.DataFrame(
                {key: dict_property_details['UpdatedPropertyDetails:updatedPropertyDetails']['response'][key] for key in
                 ['zpid']}  # 'homeDescription','neighborhood','schoolDistrict',
                , index=[0])
            df_new_property = pd.concat([df_address, df_links, df_edited_facts, df_all], axis=1)

        return df_new_property

    def zpid_from_address(self, in_address):
        #in_address = "34298 Kenwood Dr, Fremont, CA 94555, USA" # exist in zillow
        #in_address = "4650 Cushing Pkwy, Fremont, CA 94538, USA"
        address = in_address.split(',')[0].replace(" ", "+")
        citystatezip = (in_address.split(',')[1]+in_address.split(',')[2]).lstrip().replace(" ", "+")
        #  "http://www.zillow.com/webservice/GetSearchResults.htm?zws-id=<ZWSID>&address=2114+Bigelow+Ave&citystatezip=Seattle%2C+WA"
        xml_property_details = urllib2.urlopen(
            'http://www.zillow.com/webservice/GetSearchResults.htm?zws-id=' + self.zillow_api_key + '&address='
            + address + '&citystatezip=' + citystatezip).read()
        dict_property_details = xmltodict.parse(xml_property_details)
        status_code = dict_property_details[u'SearchResults:searchresults'][u'message'][u'code']
        if status_code != '0':
            raise Exception("Problem when getting zpid_from_address", status_code)
        else:
            try:
                zpid = dict_property_details[u'SearchResults:searchresults'][ u'response'][u'results'][u'result'][u'zpid']
            except:
                print "returned several zpid, keeping first"
                zpid = dict_property_details[u'SearchResults:searchresults'][ u'response'][u'results'][u'result'][0][u'zpid']

            return zpid

        #xml_property_details = urllib2.urlopen('http://www.zillow.com/webservice/GetSearchResults.htm?zws-id=' + 'X1-ZWz1fcbgun7uh7_9od0r'+ '&address=' + address + '&citystatezip=' + citystatezip).read()


class HomePropertiesDataset(LocalDatabase, GoogleMapsApiWrapper, ShapefileWrapper, ZillowApiWrapper):

    def __init__(self, in_local_database_filepath, in_local_database_filename , in_google_api_key, in_zillow_api_key):
        GoogleMapsApiWrapper.__init__(self, in_google_api_key=in_google_api_key)
        ZillowApiWrapper.__init__(self, in_zillow_api_key=in_zillow_api_key)
        LocalDatabase.__init__(self, in_local_database_filepath, in_local_database_filename)
        self.column_names = ['id', 'google_address', 'zpid', 'zillow_data', 'google_image_filename', 'shapefile_filename', 'shapefile_index', 'parcel_boundary_points'
                             u'street', u'zipcode', u'city', u'state', u'latitude', u'longitude',
                             u'homeDetails', u'photoGallery', u'homeInfo', u'useCode', u'bedrooms', u'bathrooms',
                             u'finishedSqFt', u'lotSizeSqFt', u'yearBuilt', u'numFloors', u'basement', u'roof',
                             u'exteriorMaterial', u'view', u'parkingType', u'coveredParkingSpaces', u'heatingSources',
                             u'heatingSystem', u'coolingSystem', u'appliances', u'floorCovering', u'rooms',
                             u'architecture', u'homeDescription', u'neighborhood', u'schoolDistrict']
        self.load_local_database()

    def already_scraped(self, in_shapefile_filename, in_index):
        return  len(self.df_local[ (self.df_local['shapefile_filename'] == in_shapefile_filename) & (self.df_local['shapefile_index'] == in_index)].index) == 1

    def explore_shapefile_and_scrape_zillow(self, in_shapefile_filepath, in_shapefile_filename):
        shapes = self.open_shapefile(in_shapefile_filepath=in_shapefile_filepath, in_shapefile_filename=in_shapefile_filename)
        for shape_index in range(396750-1,0,-1): #len(list(shapes))
            print "######", in_shapefile_filename,  "   shape number ", shape_index
            if self.already_scraped(in_shapefile_filename=in_shapefile_filename, in_index=shape_index):
                print "Already scraped"
            else:
                shape = shapes[shape_index]
                df_index = len(self.df_local.id)+1
                df_new = pd.DataFrame(columns=self.column_names, index=[df_index])
                df_new.ix[df_index, 'shapefile_filename'] = in_shapefile_filename
                df_new.ix[df_index, 'shapefile_index'] = shape_index
                df_new.id[df_index] = df_index
                center_lat, center_lon = self.center_of_shape(in_shape=shape)
                df_new.google_address[df_index] = self.get_google_formatted_address_from_gps_coordinates(in_latitude=center_lat, in_longitude=center_lon)
                #remove non unicode character
                df_new.google_address[df_index] = ''.join( [i if ord(i) < 128 else '' for i in df_new.google_address[df_index]])
                print df_new.google_address[df_index]
                # zillow
                try:
                    # get zpid
                    df_new.zpid[df_index] = self.zpid_from_address(df_new.google_address[df_index])
                    # extract property_features
                    df_prop_feat = self.extract_property_feature_from_zpid(in_zpid= df_new.zpid[df_index] )
                    df_new.zillow_data = "Yes"
                    for column in df_prop_feat.columns:
                        df_new.ix[df_index, column] = df_prop_feat.ix[0, column]
                except Exception as error:
                    df_new.zillow_data = "No"
                    print error.args[0], " | Zillow API returned Error:", error.args[1], ":"
                    if error.args[1] == '502':
                        print "No results found"
                    if error.args[1] == '7':
                        print "Maximum number of requests reached"
                        sys.exit()

                    # zpid : http://www.zillow.com/howto/api/GetSearchResults.htm
                    # property details: http://www.zillow.com/howto/api/GetUpdatedPropertyDetails.htm
                self.df_local = pd.concat([self.df_local, df_new], axis=0)
                if shape_index%10 == 0:  # save localy every 20 requests
                    self.save_local_database()
                # print "*********df_local:", self.df_local
        self.save_local_database()
        # print "*********final df_local:", self.df_local


alameda_dataset = HomePropertiesDataset(in_local_database_filepath="../data/",
                                        in_local_database_filename="Alameda_Properties_from_end.csv",
                                        in_google_api_key=stephane_gooogle_api_key,
                                        in_zillow_api_key=stephane_zillow_api_key)

alameda_dataset.explore_shapefile_and_scrape_zillow(in_shapefile_filepath='../shapefiles/alameda/',
                                                    in_shapefile_filename='alameda.shp')



#test.describe_shapefile(in_shapefile_filepath='shapefiles/ZillowNeighborhoods-CA/', in_shapefile_filename='ZillowNeighborhoods-CA.shp')

#test.explore_shapefile_and_scrape_zillow( in_shapefile_filepath='shapefiles/ZillowNeighborhoods-CA/', in_shapefile_filename='ZillowNeighborhoods-CA.shp')
