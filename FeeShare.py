import sys
import json

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
def show(tag,account) :
  print(f'--- {tag}')
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
def explode(expenses,account,people) :

  #-- explode the money spent between those who paid
  total=0
  for e in expenses :
    names=e["name"].split(",")
    for n in names :
      account[n]["spent"] -= e["amount"]/len(names)
      account[n]["account"] -= e["amount"]/len(names)
    total += e["amount"]

  #-- explode the money spent between those who where destination 
  for e in expenses :
    dest=people 
    if "exc" in e and len(e["exc"]) > 0 :
      part=e["amount"]/(len(e["exc"])+1)
      for p in e["exc"] :
        dest.remove(p)
    elif "inc" in e and len(e["inc"]) > 0 :
      dest.clear()
      part=e["amount"]/(len(e["inc"]))
      for p in e["inc"] :
        dest.add(p)
    else :
      part=e["amount"]/len(people)
    print(f'--- {e=} {dest=} {part=}')
    for d in dest :
      account[d]["debt"] -= part
      print(f'{d=} {account[d]}')
  return(total)

#--------------------------------------------
with open(sys.argv[1]) as fIn :
  expenses=json.load(fIn)

people=set()
for e in expenses :
  names=e["name"].split(",")
  for n in names :
    people.add(n)

if len(people) <= 0 :
  print("No people found")
  sys.exit()

account={}

#-------------------------------------------------------------
# people :
# - account : money on the account
# - debt : how many does he give 
# - spent : how many did he spend
# - due : how many does he really give (spent - debt)
# - received : after repartition
# - given : after repartition

for p in people :
  account[p]={"account":0,"debt":0,"spent":0,"due":0,"received":0,"given":0}

total=explode(expenses,account,people)

each=total/len(people)
print(f'{total=} expenses lines {len(expenses)} people={len(people)} {each=:.2f}')
for a in account.keys() :
  #account[a]["due"]=each + account[a]["spent"]
  account[a]["due"]= account[a]["spent"]-account[a]["debt"]
  print(f'{a=} {account[a]}')

show('Init',account)
i=1
while True :
  maxKey=findMaxDueKey(account)
  minKey=findMinDueKey(account)
  if len(maxKey) == 0  or len(minKey) == 0 :
    break
  trans(i,minKey,maxKey,account)
  i += 1
show('Final',account)

