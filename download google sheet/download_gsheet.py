import pygsheets
import logging

logging.basicConfig(level=logging.DEBUG)

Var = { "OAUTH2": "client_secret.json",
        "SERVICEACCOUNT":"cred.json",
        "EXCELNAME": "excel_name", 
        "SHEETNAME": "tab_name", 
        "SAVEPATH": "saveing_path_include_csv_name.csv"}

OAUTH2_OR_SERVICEACCOUNT = "SERVICEACCOUNT"

Include_index_in_excel = False


def getsheet(Choice, Index):
    try:
        if Choice == 1:
            gc = pygsheets.authorize(client_secret=Var["OAUTH2"], local=True)
        if Choice == 2:
            gc = pygsheets.authorize(service_file=Var["SERVICEACCOUNT"])
    except:
        print("Fail to authenticate, Please check.")
        exit

    try:
        sh = gc.open(Var["EXCELNAME"])
        for i in range(len(sh.worksheets())):
            wks = sh[i]
            if (wks.title==Var["SHEETNAME"]):
                read = wks.get_as_df()
    except:
        print("Can't find excel")
        exit
    
    try:
        read.to_csv(Var["SAVEPATH"], index = Index)
    except:
        print("Can't find sheet")
        exit

def getsheetmain():
    Num = {"OAUTH2": 1, "SERVICEACCOUNT":2}
    getsheet(Num[OAUTH2_OR_SERVICEACCOUNT], Include_index_in_excel)

def main():
    getsheetmain()

if __name__ == "__main__":
    main()

