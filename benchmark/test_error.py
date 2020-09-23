
f = open('spacetruth.txt')
L = ['1','2','5','10','20','50']

def compute(L1,L2):
    total = []
    for x,y in zip(L1,L2):
        total.append( abs((y-x)/x))
    print('average error',sum(total)/len(L1))
    print('max error',max(total))

truth_values  = [int(x.split()[1].strip()) for x in f.readlines()]
for l in L:
    f2 = open('space'+l+'.txt')
    values  = [float(x.split()[1].strip()) for x in f2.readlines()]
    print(values)
    compute(truth_values,values)
