from csv import reader
import os
with open('county_list.csv', 'r') as read_obj:
    csv_reader = reader(read_obj)
    for row in csv_reader:
        print(row)
        if not os.path.exists(row[1]):
            os.makedirs(row[1])
            with open(os.path.join(row[1], "README.md"), 'w') as temp_file:
                temp_file.write("# "+row[1]+"\nBe sure to check your specific county above to see if you have additional tips for your location")
            with open(os.path.join(row[1], "index.html"), 'w') as temp_file:
                temp_file.write("# "+row[1]+"<body><h1>Be sure to check your specific county above to see if you have additional tips for your location</h1>") 
        filename = row[0] + '.md'
        with open(os.path.join(row[1], filename), 'w') as temp_file:
            temp_file.write("No tips submitted for this location yet.")
            with open(os.path.join(row[1], "README.md"), 'a') as temp2_file:
                temp2_file.write("\\\n["+row[0]+"]("+row[0]+".md)")
            with open(os.path.join(row[1], "index.html"), 'a') as temp2_file:
                temp2_file.write("\n<br/><a href=\""+row[0]+".md\">"+row[0]+"</a>")
        with open(os.path.join(row[1], "index.html"), 'a') as temp_file:
            temp_file.write("</body>")
