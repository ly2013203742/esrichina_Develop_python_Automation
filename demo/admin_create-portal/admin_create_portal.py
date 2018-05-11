from arcgis.gis import *
import csv
import json

def main(argv=None):
    try:
        url = 'https://liy.esrichina.com/portal'
        username = 'arcgis'
        password = 'Super123'

        print("\n")
        print("=====================================================================\n")
        print("CREATING GROUPS")

        # connect to gis
        gis = GIS(url, username, password, verify_cert=False)
        creat_group(gis)
        creat_user(gis)
        publish_content(gis)
    except:
        print("错误！！");
# Script to read list of groups from a csv and create them on the portal.
def creat_group(gis):
    with open("groups.csv", 'r') as groups_csv:
        groups = csv.DictReader(groups_csv)
        for group in groups:
            try:
                print("\nCreating group: "+ group['title'] + "  ##  ")
                result = gis.groups.create_from_dict(group)
                if result:
                    print("success")

            except Exception as create_ex:
                print("Error... ", str(create_ex))
# Script to read account list from a csv file and create appropriate users in the portal.
def creat_user(gis):
    # loop through and create users
    with open("users.csv", 'r') as users_csv:
        users = csv.DictReader(users_csv)
        for user in users:
            try:
                print("\nCreating user: " + user['Username'], end= " ## ")
                result = gis.users.create(username=user['Username'],
                                          password=user['Password'],
                                          firstname=user['First Name'],
                                          lastname=user['Last Name'],
                                          email=user['Email'],
                                          role =user['Role'])
                if result:
                    print("success  ##\n")

                    print("\t Adding to groups: ", end=" # ")
                    groups = user['groups']
                    group_list = groups.split(",")

                    # Search for the group
                    for g in group_list:
                        group_search = gis.groups.search(g)
                        if len(group_search) > 0:
                            try:
                                group = group_search[0]
                                groups_result = group.add_users([user['Username']])
                                if len(groups_result['notAdded']) == 0:
                                    print(g + " # ")

                            except Exception as groups_ex:
                                print("\n \t Cannot add user to group ", g, str(groups_ex))
            except Exception as add_ex:
                print("\nCannot create user: " + user['Username'])
                print("\n")
                print(str(add_ex))
# Publisher persona
# Script to publish content for each user.
def publish_content(gis):
    # Read the csv containing user accounts and their territory info
    csv_path = "users.csv"

    # Read template web map
    template_webmap_dict = dict()
    with open('user_content/web_map.json', 'r') as webmap_file:
                template_webmap_dict = json.load(webmap_file)

    # Loop through each user and publish the content
    with open(csv_path, 'r') as csv_handle:
        reader = csv.DictReader(csv_handle)
        for row in reader:
            try:
                data_to_publish = 'user_content/' + row['assigned_zone'] + ".csv"

                print("\nPublishing " + data_to_publish, end= " # ")
                added_item = gis.content.add({}, data = data_to_publish)
                published_item = added_item.publish()

                if published_item is not None:
                    # publish web map
                    print('webmaps', end= " ## ")
                    user_webmap_dict = template_webmap_dict
                    user_webmap_dict['operationalLayers'][0].update({'itemId': published_item.itemid,
                                                                     'layerType': "ArcGISFeatureLayer",
                                                                     'title': published_item.title,
                                                                     'url': published_item.url + r"/0"})

                    web_map_properties = {'title': '{0} {1} response locations'.format(row['First Name'], row['Last Name']),
                                          'type': 'Web Map',
                                          'snippet': 'Regions under the supervision of' +\
                                                     '{0} {1}'.format(row['First Name'], row['Last Name']),
                                          'tags': 'ArcGIS API for Python',
                                          'typeKeywords': "Collector, Explorer Web Map, Web Map, Map, Online Map",
                                          'text': json.dumps(user_webmap_dict)}

                    web_map_item = gis.content.add(web_map_properties)

                    #Reassign ownership of items to current user. Transfer webmaps in a new
                    # folder with user's last name
                    print("success. Assigning to: ", end= "  #  ")
                    result1 = published_item.reassign_to(row['Username'])
                    new_folder_name = row['Last Name'] + "_webmaps"
                    result2 = web_map_item.reassign_to(row['Username'], target_folder=new_folder_name)

                    #share webmap to user's groups
                    groups_list1 = row['groups'].split(',')
                    groups_list = [gname.lstrip() for gname in groups_list1] #remove white spaces in name
                    result3 = web_map_item.share(groups=groups_list)
                    if (result1 and result2 and result3) is not None:
                        print(row['Username'])
                    else:
                        print("error")
                else:
                    print(" error publishing csv")

            except Exception as pub_ex:
                print("Error : " + str(pub_ex))
    print("0")
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))