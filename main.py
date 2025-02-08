from tkinter import *
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox
from functools import partial
import json
import os
import socket
import subprocess
import win32gui, win32con
import threading
import asyncio
import websockets
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

port = 9242
new_process = r"C:\Program Files\Google\Chrome\Application\chrome.exe --remote-debugging-port=%s"%(port)


#Check If Chrome Is Running And Port Is Used
def running(process_name):
    tasks = subprocess.check_output (['tasklist'], shell=True, encoding='latin1')
    return process_name in tasks
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    if(s.connect_ex(('localhost', port)) != 0):
        print("You have to use a specific modification of chrome..")
        if(running("chrome.exe")):
            print("Close All Chrome Windows First! Then Run Again")
            time.sleep(3);exit()
        else:
            print("Launching New Chrome Window...Run Again")
            subprocess.run(new_process, shell=False, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


program = win32gui.GetForegroundWindow()
# win32gui.ShowWindow(program, win32con.SW_HIDE)


#VARIABLES

refreshing=0
toggleCMD = False
data = json.loads(requests.get(f"http://127.0.0.1:{port}/json",verify=False).text)
saveFilePath = os.path.abspath(os.path.join(__file__, os.pardir))+"/data.json"
run = False
tabsIDHistory=[]
scripts = []

if(os.path.exists(saveFilePath)):
    with open(saveFilePath, 'r') as f:
        scripts=json.load(f)
        if(scripts=={}):print("No Extensions Installed!")
else:open(saveFilePath,"w").write("[]")            

print(scripts)


#INITILIZE TKINTER
root = Tk()
root.title("JSEXTENSION")
root.geometry(f"300x{50+(25*(len(scripts)+1))}")
frm = ttk.Frame(root, padding=10)
frm.grid()



#FUNCTIONS

def findTabs(pageURL):
    global tabsIDHistory
    tabsId = []
    for i in range(len(data)):
        tabData = data[i]
        if(tabData["url"].__contains__(pageURL)):
            tabsId.append(tabData["id"])
    return tabsId

async def inject(id,code,repeating):
   try:
    async with websockets.connect(f"ws://localhost:{port}/devtools/page/{id}") as websocket:
            message = {"id":1,"method":"Runtime.evaluate","params":{"expression":code}}
            await websocket.send(json.dumps(message))
            if(repeating==0):tabsIDHistory.append(id)
   except Exception as e:print("Tab Closed:",e)

def refresh():
    global refreshing;refreshing=1
    root.destroy()

def syncText(text_widget, text_var):
    text_var.set(text_widget.get("1.0", END))
    text_widget.after(100, syncText, text_widget, text_var)

def editOpenGUI(popup,run,label,index):

    popup.title(label)
    popup.geometry("300x350")
    
    Label(popup, text=label).pack()
    
    scriptName=StringVar()
    urlStr=StringVar()
    codeStr=StringVar()
    repeat=IntVar()

    def retur():
        finalJSON = {
            "name":scriptName.get(),
            "url":urlStr.get(),
            "code":codeStr.get().replace(";","").replace('\n',";").replace('"','`')+"document",
            "repeat":repeat.get()
        }
        run(finalJSON,[scriptName.get(),urlStr.get(),codeStr.get(),repeat.get()])
        print(finalJSON)
    
    Label(popup,text='Script Name').pack()
    e1 = Entry(popup,textvariable=scriptName);e1.pack()
    Label(popup,text='URL (Contain)').pack()
    e2 = Entry(popup,textvariable=urlStr);e2.pack()
    e3 = Checkbutton(popup, text='Repeat Code',variable=repeat, onvalue=1,offvalue=0);e3.pack()
    Button(popup,text = '---Save---', command=retur).pack()

    Label(popup,text='Script:').pack()
    code = scrolledtext.ScrolledText(popup, width=100,height=10, wrap=NONE)
    scrollH = Scrollbar(popup, orient=HORIZONTAL, command=code.xview)
    scrollV = Scrollbar(popup, orient=VERTICAL, command=code.yview) 
    
    code.config(xscrollcommand=scrollH.set, yscrollcommand=scrollV.set)
    code.pack(expand=True, fill='both') 
    scrollH.pack(side=BOTTOM, fill=X)
    scrollV.pack(side=RIGHT, fill=Y)   
    syncText(code, codeStr)

    if(index!=None):
        e1.insert(END,scripts[index]["name"])
        e2.insert(END,scripts[index]["url"])
        code.insert(END,scripts[index]["code"].replace(";document","").replace(';',"\n").replace('`','"'))
        if(scripts[index]["repeat"]):e3.toggle()

def newScriptWindow():
    popup = Toplevel(root)
    
    def run(finalJSON,values):submit(finalJSON,values)
    editOpenGUI(popup,run,"Create New Userscript",None)

    def submit(finalJSON,values):  
        global scripts
        checkName=0

        for i in range(len(scripts)):
            if(scripts[i]["name"]==values[0]):checkName=1
        if(checkName==0):
            print(finalJSON)
            if isinstance(scripts, list):scripts.append(finalJSON)
            else:scripts = [scripts, finalJSON]
            json.dump(scripts, open(saveFilePath, 'w'), indent=4)
            refresh()
        else:messagebox.showwarning(title="Error",message="Name Allready In Use ")


def editScriptWindow(index):
    global scripts
    popup = Toplevel(root)

    def run(finalJSON,values):submit(finalJSON,values)
    editOpenGUI(popup,run,f"Edit Existing Userscript: {scripts[index]["name"]}",index)

    def submit(finalJSON,values):  
        global scripts
        checkName=0

        for i in range(len(scripts)):
            if(i!=index):
                if(scripts[i]["name"]==values[0]):checkName=1
        if(checkName==0):
            json.dump(finalJSON,open(saveFilePath,"w"),indent=4)
            refresh()
        else:messagebox.showwarning(title="Error",message="Name Allready In Use ")

def deleteScript(index):
    del scripts[index]
    json.dump(scripts,open(saveFilePath,"w"),indent=4)
    refresh()

def showCMD():
    global toggleCMD
    if(toggleCMD):win32gui.ShowWindow(program, win32con.SW_HIDE)
    else:win32gui.ShowWindow(program, win32con.SW_SHOW)
    toggleCMD^=True

    


#Main Window


ttk.Label(frm,text="Userscripts:").grid(sticky=W,column=0, row=0,pady=(0,25))
ttk.Button(frm, text="NEW SCRIPT", command=newScriptWindow).grid(column=1,row=0,pady=(0,25))
ttk.Button(frm, text="CMD", command=showCMD).grid(column=2,row=0,pady=(0,25))



alphabet = ["a","b","c"]


for i in range(len(scripts)):
    ttk.Label(frm, anchor="w", text=scripts[i]["name"]).grid(sticky=W,column=0,row=1+i,padx=(0,30))
    ttk.Button(frm, text="Edit", command=partial(editScriptWindow,i)).grid(column=1,row=1+i)
    ttk.Button(frm, text="Delete", command=partial(deleteScript,i)).grid(column=2,row=1+i)


async def main(tabs_id, tab_script,repeating):
    tasks = [inject(tab_id, tab_script,repeating) for tab_id in tabs_id]
    await asyncio.gather(*tasks)

def Scan():
    global run;run=True
    while run:
        global data
        global scripts
        global tabsIDHistory

        #Update Data
        data = json.loads(requests.get(f"http://127.0.0.1:{port}/json",verify=False).text)
        if(os.path.exists(saveFilePath)):
            scripts=json.load(open(saveFilePath, 'r'))

        #Injector
        for i in range(len(scripts)):
            if(run==True):
                tabsID = findTabs(scripts[i]["url"])
                for j in range(len(tabsIDHistory)):
                    if(tabsID!=[]):tabsID.remove(tabsIDHistory[j])
                tabScript = scripts[i]["code"]
                asyncio.run(main(tabsID,tabScript,scripts[i]["repeat"]))


function = threading.Thread(target=Scan)
function.start()


root.mainloop()
run=False   

if(refreshing):
    subprocess.Popen(['start', 'cmd', '/k', 'python', __file__], shell=True)
