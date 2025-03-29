from collections import namedtuple


# ("files", (_file.filename, content, _file.content_type))

PartData = namedtuple("PartData", ['filename','content','contenttype'])

MultiPartData = namedtuple("MultiPartData", ['key','partdata'], defaults= ['files',None])


data = MultiPartData(partdata= tuple(PartData(filename="hellp.py", content="12,2", contenttype="json")))
print(tuple(data))
