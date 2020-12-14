import re

str = "  this is a title (but not a long one)   "

newstr = re.sub(r'\(.+?\)', '', str).strip()



print(newstr)





