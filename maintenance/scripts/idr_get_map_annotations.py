# -----------------------------------------------------------------------------
#  Copyright (C) 2018 University of Dundee. All rights reserved.
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# ------------------------------------------------------------------------------

# This client-side script runs over IDR data in our local server (copy of IDR data
# imported locally) and annotates Images with map annotations loaded from IDR.
# Datasets, Images and Annotations are loaded from IDR via http using
# public URLS returning JSON data.
# Starting at a local Project ID and IDR Project ID, we use Dataset and Image
# names to match local objects with those in IDR.

import omero
from omero.gateway import BlitzGateway

USERNAME = "username"
PASSWORD = "password"
conn = BlitzGateway(USERNAME, PASSWORD, host="outreach.openmicroscopy.org", port=4064)
conn.connect()

import requests

session = requests.Session()
base_url = "http://idr.openmicroscopy.org/webclient/api/"
map_ann_url = base_url + "annotations/?type=map"

local_project_id = 4501
idr_project_id = 51


def get_idr_datasets_as_dict(project_id):
    """Get a dict of {name: {id: 1}} for Datasets in IDR Project."""
    url = base_url + "datasets/?id=%s" % project_id
    datasets = session.get(url).json()['datasets']
    by_name = {}
    for d in datasets:
        by_name[d['name']] = d
    return by_name


def get_idr_images_as_dict(dataset_id):
    """Get a dict of {name: {id: 1}} for Images in IDR Dataset."""
    url = base_url + "images/?id=%s" % dataset_id
    images = session.get(url).json()['images']
    by_name = {}
    for i in images:
        by_name[i['name']] = i
    return by_name


project = conn.getObject("Project", local_project_id)
idr_datasets = get_idr_datasets_as_dict(idr_project_id)

for dataset in project.listChildren():

    print "\n\nDataset", dataset.id, dataset.name
    # Get IDR Dataset with same name:
    idr_dataset = idr_datasets.get(dataset.name)
    if idr_dataset is None:
        print "    NO IDR Dataset found!"
        continue

    idr_images = get_idr_images_as_dict(idr_dataset['id'])
    for image in dataset.listChildren():

        print "Image", image.id, image.name
        idr_image = idr_images[image.name]
        if idr_image is None:
            print "    NO IDR Image found!"
            continue

        # Get map annotations for image...
        url = map_ann_url + "&image=%s" % idr_image['id']
        map_anns = session.get(url).json()['annotations']
        print "  adding ", len(map_anns), " map anns..."
        for ann in map_anns:
            key_value_data = ann['values']
            map_ann = omero.gateway.MapAnnotationWrapper(conn)
            map_ann.setValue(key_value_data)
            map_ann.setNs(ann['ns'])
            map_ann.save()
            image.linkAnnotation(map_ann)

