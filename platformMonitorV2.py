import sys
import os
import time
import autoLogin
import downLoadFile
import downLoadFileV2
import autologin
import downloadFile
from pexpect import *
import xlsxwriter
import pexpect
import paramiko
import commands
import smtplib
from smtplib import SMTPException
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders
from email.mime.text import MIMEText
import sendEmail
import sendEmailV2
import datetime
import glob
import re
import json

print("\n\n######\n")
rc,output=commands.getstatusoutput("date")
print("\nStart Time: "+str(output)+"\n")
getCurt="date +'%s'"
status,time2=commands.getstatusoutput(getCurt)
timestamp=int(time2)
timestamp2=int(time2)-24*60*60
value=datetime.datetime.fromtimestamp(timestamp)
value2=datetime.datetime.fromtimestamp(timestamp2)
curTT1=value.strftime('%m%d')
#curTT=value.strftime('%a %b %-d')
week1=value.strftime('%a')
mon1=value.strftime('%b')
date1=value.strftime('%-d')
if int(date1) < 10 :
  date1=" "+str(date1)
  #print(date1)
curTT=week1+" "+mon1+" "+date1
#curTT2=value2.strftime('%Y-%m-%d')
#curTT2=value2.strftime('%a %b %-d')
week2=value2.strftime('%a')
mon2=value2.strftime('%b')
date2=value2.strftime('%-d')
if int(date2) < 10 :
  date2=" "+str(date2)
  #print(date2)
curTT2=week2+" "+mon2+" "+date2


print(curTT)
print(curTT2)
#curTT2="Wed Dec 26"
#sys.exit(0)

def getCurrData(accTime):
  flag="False"
  open("/tmp/jobInfo.tmp","w").close()
  outFile=open("/tmp/jobInfo.tmp","wb+")
  with open("/tmp/awx-uwsgi.log","r") as inFile:
    for line in inFile:
      if accTime in line:
        flag="True"
      if flag=="True":
        outFile.write(line)
  outFile.close()

def getJobId():
  syscmd="cat  /tmp/jobInfo.tmp|awk '{print $12,$13,$14,$16,$18}' |grep jobs |grep 'format=json'|grep -v stdout|sort -rn |uniq > /tmp/jobInfoV2.tmp"
  os.system(syscmd)
  open("/tmp/ansibleJob.tmp","w").close()
  outFile=open("/tmp/ansibleJob.tmp","wb+")
  with open("/tmp/jobInfoV2.tmp","r") as inFile:
    for line in inFile:
      line=line.replace('/',',')
      sp=[]
      sp=line.split(',')
      jobtime=sp[0]
      jobid=sp[4]
      #print(jobid)
      outFile.write(jobtime+","+jobid+"\n")
  outFile.close()


def getMissingJob():
  open("/tmp/missingJob.tmp","w").close()
  outFile=open("/tmp/missingJob.tmp","wb+")
  with open("/tmp/ansibleJob.tmp","r") as inFile:
    for line in inFile:
      jobid=""
      jobtime=""
      sp=[]
      sp=line.split(',')
      jobtime=sp[0]
      jobid=sp[1].strip('\n')
      syscmd="cat /tmp/jobStatistics.tmp |grep "+jobid
      status,chkResult=commands.getstatusoutput(syscmd)
      #print(str(status)+' , '+str(chkResult))
      if int(status)!=0:
        outFile.write(jobtime+','+jobid+"\n")
        print(str(jobid))
      #sys.exit(0)
  outFile.close()

def compareJobId():
  flag="noIssueFound"
  with open("/tmp/missingJob.tmp","r") as inputFile:
    for line in inputFile:
      sp=[]
      sp=line.split(',')
      maxMissingJobId=sp[1].strip().rstrip("\n")
      break
  with open("/tmp/jobStatistics.tmp","r") as inFile:
    jobinfo=list(inFile)[-1]
    sp2=[]
    sp2=jobinfo.split(',')
    maxJobIdHiro=sp2[0].strip().rstrip('\n')
    print("\n max missing JobId: "+maxMissingJobId+"\n")
    print("\n max received JobId in Hiro: "+maxJobIdHiro+"\n")
  if int(maxMissingJobId) > int(maxJobIdHiro):
    flag="issueFound"
  else:
    flag="noIssueFound"
  print("\n"+flag+"\n")
  return(flag)

def queryJob(maxJobId):
  open("/tmp/jobChkResult.txt","w").close()
  timeoutJob=0
  ##create excel file
  syscmd="rm -f /tmp/timeout"+curTT1+".xlsx"
  os.system(syscmd)
  workbook = xlsxwriter.Workbook('/tmp/timeout'+curTT1+'.xlsx')
  worksheet = workbook.add_worksheet("timeout info")
  # Start from the first cell. Rows and columns are zero indexed.
  bold = workbook.add_format({'bold': True})

  worksheet.write(0,0, "JobTime",bold)
  worksheet.write(0,1, "JobId",bold)
  worksheet.write(0,2, "IPAddress",bold)
  worksheet.write(0,3, "eTime(seconds)",bold)
  worksheet.write(0,4, "TemplateName",bold)
  worksheet.write(0,5, "PlayBook",bold)
  worksheet.write(0,6, "JobStatus",bold)
  worksheet.write(0,7, "MuleOrAnsibeIssue?",bold)

  worksheet.set_column('A:G',20)
  worksheet.set_column('H:H',30)
  row=1
  col=0
  queryErrCount=0
  jobChkResult="jobtime , jobid ,  hostname , elapseTime , templatename , playbook , jobstatus , muleissue?\n"

  ##end creating excel file
  with open("/tmp/missingJob.tmp","r") as inFile:
    for line in inFile:
      sp=[]
      sp=line.split(',')
      jobtime=sp[0]
      jobid=sp[1].strip().rstrip('\n')
      filename="/tmp/jobInfo/jobinfo-"+str(jobid)
      syscmd='curl -H "Content-Type: application/json" -X GET -u xxx:xxx  -k -s -o '+filename+' https://main.twrgoo.compucom.com/api/v2/jobs/'+str(jobid)+'/job_events/?order_by=start_line'
      os.system(syscmd)
      resFile=open("/tmp/jobChkResult.txt","a")
      with open(filename,'r') as inputFile:
        out_json=json.load(inputFile)
        count=0
        count=len(out_json['results'])
        fflag="True"
        if count==0 and int(jobid)>int(maxJobId):
          queryErrCount += 1
          fflag="False"
          #row -= 1
          print("\nThis job: "+jobid+" failed ansible query!\n")
          continue
        elif count==0 and int(jobid)<=int(maxJobId):
          #row -= 1
          print("\nThis job: "+jobid+" failed ansible query!\n")
          continue
        count=count-1
        print("\n count: "+str(count)+' , '+str(jobid)+"\n")
        k=out_json['results'][count]
        templatename=k['summary_fields']['job']['name']
        for h in out_json['results']:
            hostname="unknow"
            hostname=h['host_name']
            if (hostname and "localhost" not in hostname) or (hostname=="localhost" and "Local" in templatename):
              print("\n"+hostname+"\n")
              break
        jobstatus=k['summary_fields']['job']['status']
        etime=k['summary_fields']['job']['elapsed']
        print("\n"+jobid+' , '+templatename+' , '+jobstatus+' , '+str(etime)+"\n")
        if "running" in jobstatus:
            playbook="unknown"
            muleissue="False"
            resFile.write(jobtime+" , "+jobid+" , "+ hostname+" , "+str(etime)+" , "+templatename+" , "+playbook+" , "+jobstatus+" , "+muleissue+"\n")
            jobChkResult += jobtime+" , "+jobid+" , "+ hostname+" , "+str(etime)+" , "+templatename+" , "+playbook+" , "+jobstatus+" , "+muleissue+"\n"
            worksheet.write(row, col, jobtime)
            worksheet.write(row, col+1, jobid)
            worksheet.write(row, col+2, hostname)
            worksheet.write(row, col+3, str(etime))
            worksheet.write(row, col+4, templatename)
            worksheet.write(row, col+5, playbook)
            worksheet.write(row, col+6, jobstatus)
            worksheet.write(row, col+7, muleissue)
        #elif (k['host_name'] and "localhost" not in k['host_name']) or "Local" in templatename:
        else:
            #templatename=k['summary_fields']['job']['name']
            #jobstatus=k['summary_fields']['job']['status']
            #etime=k['summary_fields']['job']['elapsed']
            playbook=k['playbook']
            muleissue="True"
            if int(etime) > 300:
              muleissue="False"
            resFile.write(jobtime+" , "+jobid+" , "+ hostname+" , "+str(etime)+" , "+templatename+" , "+playbook+" , "+jobstatus+" , "+muleissue+"\n")
            jobChkResult += jobtime+" , "+jobid+" , "+ hostname+" , "+str(etime)+" , "+templatename+" , "+playbook+" , "+jobstatus+" , "+muleissue+"\n"
            if muleissue=="True" and int(jobid)>int(maxJobId):
              timeoutJob += 1
              print("\n jobid : "+jobid+" , max job id in Hiro: "+maxJobId+"\n")
              
            worksheet.write(row, col, jobtime)
            worksheet.write(row, col+1, jobid)
            worksheet.write(row, col+2, hostname)
            worksheet.write(row, col+3, str(etime))
            worksheet.write(row, col+4, templatename)
            worksheet.write(row, col+5, playbook)
            worksheet.write(row, col+6, jobstatus)
            worksheet.write(row, col+7, muleissue)
      resFile.close() 
      row += 1
  worksheet.autofilter('A1:H20')
  workbook.close()
  return(str(timeoutJob),str(queryErrCount),jobChkResult)

fileN="issue"+curTT1

autoLogin.main("nohup /usr/bin/python /export/home/RIMusers/bgao/kibackup/healthChk.py > /tmp/test.out 2>&1 &","161.108.208.209")
autoLogin.main("nohup /usr/bin/python /export/home/RIMusers/bgao/kibackup/healthChk.py > /tmp/test.out 2>&1 &","161.108.208.143")
autoLogin.main("nohup /usr/bin/python /export/home/RIMusers/bgao/getErrInfo.py > /tmp/test.out 2>&1 &","161.108.208.185")
autoLogin.main("nohup /usr/bin/python /export/home/RIMusers/bgao/getErrInfo.py > /tmp/test.out 2>&1 &","161.108.208.240")
autologin.main("nohup /usr/bin/python /export/home/RIMusers/bgao/monitorIssueCreation.py 1 date >/tmp/test0201.out  2>&1 &")
time.sleep(120)
autologin.main("nohup /usr/bin/python /export/home/RIMusers/bgao/extrIssueInfo.py 4 date > /tmp/test0203.out 2>&1 &")
time.sleep(120)
try:
  downLoadFile.dFile("engine2Chk.txt,jobStatistics2.tmp","161.108.208.209")
except:
  pass
downLoadFile.dFile("errInfoGxy.out,ticketDeleteAlert.out","161.108.208.185")
downLoadFile.dFile("errInfoGxy1.out,ticketDeleteAlert2.out","161.108.208.240")
try:
  downLoadFile.dFile("engine1Chk.txt,jobStatistics1.tmp","161.108.208.143")
except:
  pass
downloadFile.dFile("chkIssueCreationResult")
downLoadFileV2.dFile(fileN,"161.108.208.250")


getToken='curl -k -X POST -s -o /tmp/token.out -H "Content-Type: application/x-www-form-urlencoded;charset=UTF-8" -d "grant_type=client_credentials&client_id=G30gIWsLEeHJZ_fwXLBiYIu6q4Ya&client_secret=BLFns3lggeisiLXEoD0g9ZxfhZ8a"'+' https://161.108.208.181:9443/oauth2/token'

print("\n"+getToken+"\n")
os.system(getToken)

#time.sleep(20)
#sys.exit(1)
with open("/tmp/token.out", "rb") as filet:
  tokenf=filet.readline()
print(tokenf)
tokenf=json.loads(tokenf)
token=tokenf["access_token"]


def chkFsMissingIssue(filename):
  getCurt="date +'%s'"
  status,times=commands.getstatusoutput(getCurt)
  timestamp=int(times)
  value=datetime.datetime.fromtimestamp(timestamp)
  curTT=value.strftime('%m%d')
  open("/tmp/missfsissue.out","w").close
  outFile=open("/tmp/missfsissue.out","w") 
  with open("/tmp/"+filename,"r") as inFile:
    for line in inFile:
      sp=[]
      sp=line.split(',')
      tm=sp[0].split()[0]
      tm=tm.strip()
      ciname=sp[1].strip()
      testcmd="cat /tmp/ticketinfo/issue"+curTT+"|awk -F ',' '{print $1,$2,$3,$5,$6,$16}'|grep "+tm+"|grep -i "+ciname+"|grep -v INACTIVE|grep NOTIFICATION-FileSystem_FS"
      print(testcmd)
      rc,result=commands.getstatusoutput(testcmd)
      print("\n result , rc:  "+rc+' , '+result+"\n")
      if rc==0:
        continue
      else:
        print(line)
        outFile.write(line)
  outFile.close()    


try:
  os.system("cat /tmp/errInfoGxy1.out >> /tmp/errInfoGxy.out")
  chkFsMissingIssue("errInfoGxy.out")
except:
  pass


def removeDuplicateRecord():
  outFile=open("/tmp/ticketdeletealert.out","w")
  os.system("cat /tmp/ticketDeleteAlert.out|sort -n > /tmp/ticketDeleteAlert4.out")
  with open("/tmp/ticketDeleteAlert4.out","r") as inFile:
    ticketinfo=[]
    for line in inFile:
      ticketnumber=line.split(',')[0].strip()
      if ticketnumber in ticketinfo:
        continue
      else:
        ticketinfo.append(ticketnumber)
        print("\n ticket deleted upon request"+str(line)+"\n")
        outFile.write(line)
  return "true" 
 
   
  
def chkSNOWstatus(inc,iid,token):
  getT="date +'%s'"
  status,times=commands.getstatusoutput(getT)
  timestamp=int(times)
  value=datetime.datetime.fromtimestamp(timestamp)
  curT=value.strftime('%y-%m-%dT%H:%M:%SZ')
  #print(curT)
  tranId=iid+curT+inc
  qcmd="curl -s -o /tmp/snowv4.out " + "\'https://xxx:xxx@mule-internal.muleca.compucom.com/api/incident/incidentnumber?sender=HIRO&client=HIRO&transactionId="+tranId+"\&caseNumber="+inc+"\'"
  print(qcmd)
  try:
    os.system(qcmd)
    output_json = json.load(open('/tmp/snowv4.out'))
    assignedgroup=str(output_json['incident']['supportGroup']).strip()
    ticketstatus=str(output_json['incident']['status']).strip()
    if "HIRO" in assignedgroup and "Resolved" not in ticketstatus and "Closed" not in ticketstatus:
      return("true")
    else:
      return("false")
  except:
    #if str(output_json['statusCode']) == "404":
    print("\n something wrong when trying to get the SNOW information! \n")
    return("true")
  

def chkModifyTime(filename):
  time1=os.path.getmtime(filename)

  getCurt="date +'%s'"
  status,time2=commands.getstatusoutput(getCurt)
  timeThreshold=10*60
  timeDifference=int(time2)-int(time1)

  if timeDifference > timeThreshold:
    return("OLd file")
  else:
    return("New File")

def chkEngineStatus(filename):
  flag="Active"
  with open(filename,"r") as inputFile:
    for line in inputFile:
      if "notActive" in line:
        flag="notActive"
        break
  return(flag)
  


eng1Chk=chkEngineStatus("/tmp/engine1Chk.txt")
eng2Chk=chkEngineStatus("/tmp/engine2Chk.txt")
print("eng1Chk : "+eng1Chk+"\n")
print("eng2Chk : "+eng2Chk+"\n")


open("/tmp/chkResult.txt","w").close()
outputFile=open("/tmp/chkResult.txt","wb+")
outputFile.write("Team:\n\n")
outputFile.write("Below is the check result, please take a look:\n\n")
issueFound="False"
#att=["/tmp/engine2Chk.txt"]
#att=["/tmp/timeout"+str(curTT1)+".xlsx"]
att=[]
if eng1Chk=="notActive":
  att.append("/tmp/engine2Chk.txt")
  os.system("cp -p /tmp/jobStatistics2.tmp  /tmp/jobStatistics.tmp")
  with open("/tmp/engine2Chk.txt","rb+") as inputFile:
    for line in inputFile:
      if "no issue found" not in line:
        outputFile.write(line)
        issueFound="True"
else:
  att.append("/tmp/engine1Chk.txt")
  os.system("cp -p /tmp/jobStatistics1.tmp /tmp/jobStatistics.tmp")
  with open("/tmp/engine1Chk.txt","rb+") as inputFile:
    for line in inputFile:
      if "no issue found" not in line:
        outputFile.write(line)
        issueFound="True"
##check the time out error
getCurrData(curTT)
getJobId()
getMissingJob()
timeoutJob=0
queryErrCount=0
maxJobIdHiro="nodata"
jobChkResult=""
with open("/tmp/jobStatistics.tmp","r") as inFile:
  try:
    jobinfo=list(inFile)[-1]
    sp2=[]
    sp2=jobinfo.split(',')
    maxJobIdHiro=sp2[0].strip().rstrip('\n')
    print("\n max received JobId in Hiro: "+maxJobIdHiro+"\n")
  except:
    print("\n no Ansible JobId found, please check!!\n")

try:
  timeoutJob,queryErrCount,jobChkResult=queryJob(maxJobIdHiro)
except:
  timeoutJob=0
#flag="noIssueFound"
#flag=compareJobId()
#sys.exit(0)
if int(timeoutJob) > 3:
  outputFile.write("\n\nTimeout found in Hiro, please investigate - - - - \n\n")
  outputFile.write(jobChkResult)
  att.append("/tmp/timeout"+str(curTT1)+".xlsx")
  issueFound="True"

if int(queryErrCount) > 3:
  outputFile.write("\n\nThere are "+str(queryErrCount)+" times Ansible query error, please check Ansible Tower!!\n\n")
  issueFound="True"

status=0
issueAmount=0
status,issueAmount=commands.getstatusoutput("cat /export/home/RIMusers/bgao/chkIssueCreationResult|wc -l")
if int(issueAmount) < 1 :
  outputFile.write("\n\nThere are no issue created for more than 1 hour, there may be something wrong with the Ascend platform!!\n")
  issueFound="True"


status=0
issueAmount=0
status,issueAmount=commands.getstatusoutput("cat /tmp/ticketMonitor.out|wc -l")
if int(issueAmount) > 0 :
  issueFound="True"
  outputFile.write("\n\n")
  with open("/tmp/ticketMonitor.out","rb+") as inputFile:
    for line in inputFile:
      print(line)
      outputFile.write(line)

status=0
hiroqueue=0
status,hiroqueue=commands.getstatusoutput("cat /tmp/snticketmonitor.out|wc -l")
if int(hiroqueue) > 0 :
  issueFound="True"
  outputFile.write("\n\nBelow is the ticket in Hiro queue, please assign them to SME to handle:\n")
  with open("/tmp/snticketmonitor.out","rb+") as inputFile:
    for line in inputFile:
      print(line)
      outputFile.write(line)



status=0
missingfsissue=0
status,missingfsissue=commands.getstatusoutput("cat /tmp/missfsissue.out|wc -l")
if int(missingfsissue) > 0 :
  issueFound="True"
  outputFile.write("\n\nBelow alert may get ignored by the Ascend platform:\n")
  with open("/tmp/missfsissue.out","rb+") as inputFile:
    for line in inputFile:
      print(line)
      outputFile.write(line)


status=0
delteticketalert=0
os.system("cat /tmp/ticketDeleteAlert2.out >> /tmp/ticketDeleteAlert.out")
result2=removeDuplicateRecord()
status,deleteticketalert=commands.getstatusoutput("cat /tmp/ticketdeletealert.out|wc -l")
if int(deleteticketalert) > 0 :
  outputFile.write("\n\n\nThe following ticket# was deleted in Hiro upon request within the last 4 hours, ServiceNow may not be updated from the point of the time unless the ticket# is added back: \n")
  os.system("cat /tmp/ticketdeletealert.out |grep INC0 > /tmp/ticketdeletealert2.out")
  os.system("mv /tmp/ticketdeletealert2.out /tmp/ticketdeletealert.out")
  with open("/tmp/ticketdeletealert.out","rb+") as inputFile:
    for line in inputFile:
      print("\nline: "+line+"\n")
      sp8=[]
      sp8=line.split(',')
      iid=sp8[2]
      incidentId=sp8[0]
      flag="true"
      flag=chkSNOWstatus(incidentId,iid,token)
      if flag=="true":
        outputFile.write(line)
        issueFound="True"
      else:
        print("\n"+incidentId+" has been resolved or not in HIRO queue! \n")

##
outputFile.write("\n\nRegards,\n")
outputFile.close()

subj="Platform monitoring report"
file1="/tmp/chkResult.txt"
print("\n  issueFound: "+issueFound+"\n")
#issueFound="True"
if issueFound=="True":
  sendEmailV2.sendEmail(subj,file1,att,"gqrlt1207@gmail.com","ansiblereport@gmail.com")
  print("there may be some issue, please check!!\n")
else:
  print("no issue found!!")
print("\nFinish checking Ascend Platform!\n")
