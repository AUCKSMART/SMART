import math
millnames = ['',' K',' M',' B',' T']

def millify(n):
    n = float(n)
    millidx = max(0,min(len(millnames)-1, int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))
    return '{:0.2F}{}'.format(n / 10**(3 * millidx), millnames[millidx])

def stripper(data):
    data = data.replace('-','')
    data = data.replace(':','')
    data = data.replace(' ','')
    data = data.replace('.','')
    data = int(data)
    return data