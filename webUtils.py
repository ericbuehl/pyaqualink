
##################################################################
# http routines
##################################################################
def parseRequest(request):
    params = {}
    reqLines = request.split("\n")
    reqItems = reqLines[0].split(" ")
    verb = reqItems[0]
    pathItems = reqItems[1].split("?")
    path = pathItems[0]
    if len(pathItems) > 1:
        query = pathItems[1]
        queryItems = query.split("&")
        for item in queryItems:
            part = item.split("=")
            params[part[0]] = part[1]
    return (verb, path, params)

def httpHeader(server, contentLength=0, responseCode="200 OK"):
    response  = "HTTP/1.0 "+responseCode+"\n"
    response += "Server: "+server+"\n"
    response += "Connection: close\n"
    if contentLength != 0:
        response += "Content-length: "+str(contentLength)+"\n"
        response += "Content-Type: text/html; charset=UTF-8\n"
    response += "\r\n"
    return response

def url(scheme="http", host="", port="", path="", query=[]):
    response = ""
    if scheme != "":
        response += scheme+"://"
    if host != "":
        response += host
        if port != "":
            response += ":"+port
        response += "/"
    if path != "":
        response += path
    if query != []:
        delimiter = "?"
        for item in query:
            response += delimiter+item[0]+"="+item[1]
            delimiter = "&"
    return response

def selfUrl(query):
    return url("", "", "", "index.php", query)
    
######################################################################################
# javascript
######################################################################################

def refreshScript(interval):
    script  = "<script type='text/javascript'>\n"
    script += "<!-- Begin\n"
    script += "function refresh() {\n"
    script += "	location.reload(true)\n"
    script += "}\n"
    script += "window.setInterval('refresh()',"+str(interval*1000)+");\n"
    script += "// End -->\n"
    script += "</script>\n"
    return script

def redirectScript(location, interval):
    script  = "<script type='text/javascript'>\n"
    script += "<!--\n"
    script += "function redirect() {\n"
    script += "	location='"+location+"';\n"
    script += "}\n"
    script += "window.setInterval('redirect()',"+str(interval*1000)+");\n"
    script += "//-->\n"
    script += "</script>\n"
    return script
      
######################################################################################
# Basic HTML definitions
######################################################################################

def htmlDocument(document, title=[""], script="", trailer=""):
    response  = htmlHeader(title, script)
    response += htmlBody(document, title)
    response += htmlTrailer(trailer)
    return response

def htmlHeader(title, script="", css=""):
    response  = "<!DOCTYPE html PUBLIC>\n"
    response += "<html xmlns='http://www.w3.org/1999/xhtml' xml:lang='en'>\n"
    response += "<head>\n"
    response += "<title>"+displayLine(title)+"</title>\n"
    response += script
    if css != "":
        response += "<link rel='stylesheet' type='text/css' href='"+css+"'>\n"
    response += "</head>\n"
    return response

def htmlTrailer(text=""):
    response  = text
    response += "</html>\n"
    return response

def htmlBody(body, heading=[""]):
    response  = "<body>\n"
    if heading != "":
        response += htmlHeading(heading)
    response += body
    response += "</body>\n"
    return response

def htmlHeading(heading, level=1):
    response  = "<h"+str(level)+">"+displayLine(heading)+"</h"+str(level)+">\n"
    return response

def htmlTable(rows, headings=[], widths=[], border=1):
    tableWidth = 0
    col = ""
    for width in widths:
        tableWidth += width
        col += "    <col width="+str(width)+">\n"
    response  = "<table border="+str(border)+" width="+str(tableWidth)+" style='table-layout:fixed'>\n"
    if col != "":
        response += col
    if headings != []:
        response += "    <tr>\n"
        for heading in headings:
            response += "        <th>"+heading+"</th>\n"
        response += "    </tr>\n"
    for row in rows:
        response += "    <tr>\n"
        for item in row:
            response += "        <td>"+item+"</td>\n"
        response += "    </tr>\n"
    response += "</table>\n"
    return response

def htmlForm(form, name, action, method="post"):
    response  = "<form name='"+name+"' action='"+action+"' method='"+method+"'>\n"
    response += form
    response += "</form>\n"
    return response

def htmlInput(label, inputType, name, value, size="", maxlength=""):
    response  = label
    response += "<input type='"+inputType+"' name='"+name+"' value='"+value+"'"
    if size != "":
        response += " size='"+size+"'"
    if maxlength != "":
        response += " maxlength='"+maxlength+"'"
    response += " />"
    return response

def htmlFieldset(text, legend=""):
    response  = "<fieldset>\n"
    if legend != "":
        response += "<legend>"+legend+"</legend>\n"
    response += text
    response += "</fieldset>\n"
    return response
        
def htmlImage(src, width="", height=""):
    response  = "<img src='"+src+"'"
    if width != "":
        response += " width='"+str(width)+"'"
    if height != "":
        response += " height='"+str(height)+"'"
    response += ">"
    return response

def htmlAnchor(href, text, br=False):
    response  = "<a href='"+href+"'>"+text+"</a>"
    if br: response += htmlBreak()
    return response

def htmlFont(text, size="", color="", face=""):
    response  = "<font"
    if size != "":
        response += " size="+size
    if color != "":
        response += " color="+color
    if face != "":
        response += " face="+face
    response += ">"+text+"</font>\n"
    return response
    
def htmlBreak():
    return "<br>\n"

######################################################################################
# Complex HTML
######################################################################################

# concatenate a list of lines separated by a break into a page of text
def displayPage(lineList):
    response = ""
    for line in lineList:
        response += displayLine(line)+htmlBreak()
    return response

# concatenate a list of chunks of text separated by a space into a line of text
def displayLine(chunkList):
    response = ""
    for chunk in chunkList:
        response += chunk+" "
    return response.strip(" ")

# create a list of form inputs from a list of attributes
# [0] = label
# [1] = type
# [2] = name
# [3] = value
# [4] = size
# [5] - maxlength
def updatePage(attrList, br=True):
    response = ""
    for attr in attrList:   # this needs improving
        if len(attr) == 4:
            response += htmlInput(attr[0], attr[1], attr[2], attr[3])
        elif len(attr) == 5:
            response += htmlInput(attr[0], attr[1], attr[2], attr[3], attr[4])
        elif len(attr) == 6:
            response += htmlInput(attr[0], attr[1], attr[2], attr[3], attr[4], attr[5])
        if br: response += htmlBreak()
    return response

######################################################################################
# display
######################################################################################

def secs2hms(seconds):
    hours = seconds / 3600
    seconds -= 3600*hours
    minutes = seconds / 60
    seconds -= 60*minutes
    if hours == 0:
        return "%2d:%02d" % (minutes, seconds)
    return "%2d:%02d:%02d" % (hours, minutes, seconds)

def displayPhone(phone):
    if phone != "":
        return "+"+phone[0:2]+" "+phone[2:5]+" "+phone[5:8]+"-"+phone[8:12]
    else:
        return ""

