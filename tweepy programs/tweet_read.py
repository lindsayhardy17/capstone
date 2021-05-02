"""
import json
with open('tweets2.json') as f:
    z = f.readlines()
    #print(json.loads(z[0]))
    #print(z)
    #data = json.loads(z)
    print(len(z))

# get this to work
"""
f1 = open("following.txt", "r")
scraped = f1.readlines()
print("done: ", len(scraped))
f1.close()



"""
    data = json.loads(f.read())
   
# try this a diff way
"""
"""
import csv

with open('tweets.csv') as f:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            print(row)
      
        line_count += 1
print(line_count)
"""
