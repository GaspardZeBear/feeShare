import sys
import json
import argparse
import logging

#--------------------------------------------
def findMaxDueKey(account) :
  maxKey=""
  max=0
  for a in account.keys() :
    if account[a]["due"] > max : 
       max=account[a]["due"]
       maxKey=a
  return(maxKey)

#--------------------------------------------
def findMinDueKey(account) :
  minKey=""
  min=0
  for a in account.keys() :
    if account[a]["due"] < min : 
       min=account[a]["due"]
       minKey=a
  return(minKey)

#--------------------------------------------
def showAccount(tag,account) :
  print(f'--- begin {tag}')
  for a in sorted(account.keys()) :
    print((
          f'name={a}'
          f' account={account[a]["account"]:8.2f}' 
          f' spent={account[a]["spent"]:8.2f}'
          f' received={account[a]["received"]:8.2f}'
          f' gave={account[a]["given"]:8.2f}' 
          f' due={account[a]["due"]:8.2f}'
          f' debt={account[a]["debt"]:8.2f}'
          ))
  print(f'--- end {tag}')

#--------------------------------------------
def trans(num, minKey,maxKey,account) :
  #if account[maxKey]["due"] < 0 :
  #  print(f'account[maxKey]["due"] < 0 !!!!')
  
  give=account[maxKey]["due"]
  if account[maxKey]["due"] > abs(account[minKey]["due"])  :
    give = abs(account[minKey]["due"])
  
  print((f'Transaction {num:3d}'
         f' from {maxKey=} {account[maxKey]["due"]:8.2f}'
         f' to {minKey=} {account[minKey]["due"]:8.2f}'
         f' give={give:8.2f}'
         ))
  account[minKey]["received"] += give
  account[minKey]["account"] += give
  account[minKey]["due"] += give
  account[maxKey]["due"] -= give
  account[maxKey]["given"] += give
  account[maxKey]["account"] -= give

#--------------------------------------------
#-- names format :  <name1>[:<percent1>],<name2>[:<percent2>], ...
#-- ex :
# in : jim:0.8,bob,alice:0.15
# out : {"jimi":0.8,"bob":0.05,"alice":0.15}
#-------------------------------------------------------
def buildPercents(expense,key) :
    names=expense[key].split(",")
    namesSet=set()
    percents={}
    for n in names :
      namesSet.add(getNameFromFullname(n))
      percents[getNameFromFullname(n)]=-1
    
    sumPercent = 0
    countPercent = 0
    for n in names :
      percent=getPercentFromFullname(n)
      if percent > 0 :
        if percents[getNameFromFullname(n)] == -1 :
          percents[getNameFromFullname(n)]= 0
        percents[getNameFromFullname(n)]+=percent
        sumPercent += percent
        countPercent += 1
    if sumPercent > 1 :
      print(f'Error : sum percent in {expense} is {sumPercent} gt 1 !')
      sys.exit()

    #-- Nobody had a percentage, equi-share between all  
    if countPercent == 0 :
      part=1/len(namesSet)
      for n in namesSet :
        percents[n]=part
      return(percents)
    #-- all had a percentage nothing to change
    if countPercent == len(namesSet) :
      return(percents)
    #-- some had a percentage , others not : share the remaining percent between 
    part = (1-sumPercent)/(len(namesSet)-countPercent)
    for n in namesSet :
      if percents[n] == -1 :
        percents[n]=part
    return(percents)

#--------------------------------------------
def exploseExpenses(expenses,account,people) :

  #-- explose the money spent between those who paid
  total=0
  for e in expenses :
    logging.debug(f'{e}')
    percents=buildPercents(e,"name")
    logging.debug(f'{percents}')
    #print(f'==========')
    #print(f'{e=}')
    #print(f'{percents=}')
    names=e["name"].split(",")
    for n in names :
      #account[getNameFromFullname(n)]["spent"] -= e["amount"]/len(names)
      #account[getNameFromFullname(n)]["account"] -= e["amount"]/len(names)
      account[getNameFromFullname(n)]["spent"] -= e["amount"]*percents[getNameFromFullname(n)]
      account[getNameFromFullname(n)]["account"] -= e["amount"]*percents[getNameFromFullname(n)]
    total += e["amount"]
    logging.debug(f'{account}')

  #-- explose the money spent between those who where destination 
  for e in expenses :
    dest=people 
    if "exc" in e and len(e["exc"]) > 0 :
      part=e["amount"]/(len(e["exc"])+1)
      for p in e["exc"] :
        dest.remove(getNameFromFullname(p))
    elif "inc" in e and len(e["inc"]) > 0 :
      dest.clear()
      part=e["amount"]/(len(e["inc"]))
      for p in e["inc"] :
        dest.add(getNameFromFullname(p))
    else :
      part=e["amount"]/len(people)
    #print(f'--- {e=} {dest=} {part=}')
    for d in dest :
      account[d]["debt"] -= part
    logging.debug(f'{account}')
    #  print(f'{d=} {account[d]}')

#--------------------------------------------
def getNameFromFullname(fullname) :
  return(fullname.split(":")[0]) 

#--------------------------------------------
def getPercentFromFullname(fullname) :
  if ":" not in fullname :
    return(-1)
  else :
    return(float(fullname.split(":")[1])) 


#--------------------------------------------
def getPeopleFromExpenses(expenses,key,people) :
  for e in expenses :
    if key in e and len(e[key]) > 0 :
      names=e[key].split(",")
      for n in names :
        people.add(getNameFromFullname(n))

#-----------------------------------------------------
def fSpread(args) :
  with open(args.file) as fIn :
    expenses=json.load(fIn)
  if len(args.key) > 0 :
    expenses=expenses[args.key]
  
  people=set()
  getPeopleFromExpenses(expenses,"name",people)
  getPeopleFromExpenses(expenses,"exc",people)
  getPeopleFromExpenses(expenses,"inc",people)
  if len(people) <= 0 :
    print("No people found")
    sys.exit()
#-------------------------------------------------------------
# account hashmap : key=people :
# - account : money on the account
# - debt : how many must he give 
# - spent : how many did he spend
# - due : how many does he really give (spent - debt)
# - received : after repartition
# - given : after repartition
  account={}
  for p in people :
    account[p]={"account":0,"debt":0,"spent":0,"due":0,"received":0,"given":0}
  
  exploseExpenses(expenses,account,people)
  
  for a in account.keys() :
    account[a]["due"]= account[a]["spent"]-account[a]["debt"]
    #print(f'{a=} {account[a]}')
  
  print(f'{expenses=}')
  showAccount('Init',account)
  i=1
  while True :
    maxKey=findMaxDueKey(account)
    minKey=findMinDueKey(account)
    if len(maxKey) == 0  or len(minKey) == 0 :
      break
    trans(i,minKey,maxKey,account)
    i += 1
  showAccount('Final',account)

#----------------------------------------------------------------
parser = argparse.ArgumentParser()

subparsers = parser.add_subparsers(help='sub-command help')
parser.add_argument('-v', '--verbose',
                    action='count',
                    dest='verbose',
                    default=0,
                    help="verbose output (repeat for increased verbosity)")

parserSpread = subparsers.add_parser('spread', help='a help')
parserSpread.set_defaults(func=fSpread)
#parserSpread.add_argument('--alert','-a',default=False,action='store_true',help="Send alert")
parserSpread.add_argument('--file','-f',default="",help="file")
parserSpread.add_argument('--key','-k',default="",help="key in file")

args=parser.parse_args()
loglevels=[logging.ERROR,logging.WARNING,logging.INFO,logging.DEBUG,1]
loglevel=loglevels[args.verbose] if args.verbose < len(loglevels) else loglevels[len(loglevels) - 1]
logging.basicConfig(stream=sys.stdout,format="%(asctime)s %(module)s %(name)s  %(funcName)s %(lineno)s %(levelname)s %(message)s", level=loglevel)
logging.log(1,'Deep debug')
args.func(args)
