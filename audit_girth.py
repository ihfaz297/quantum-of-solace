from collections import deque
import math
def girth(n,edges):
    adj={i:[] for i in range(n)}
    for a,b in edges: adj[a].append(b); adj[b].append(a)
    best=math.inf
    for s in range(n):
        dist={s:0}; par={s:None}; q=deque([s])
        while q:
            u=q.popleft()
            for w in adj[u]:
                if w not in dist:
                    dist[w]=dist[u]+1; par[w]=u; q.append(w)
                elif w!=par[u]: best=min(best,dist[u]+dist[w]+1)
    return best
# C_6 + 3 legs to an OUTSIDE hub  (winding.py's construction)
m=6; e=[(i,(i+1)%m) for i in range(m)]
k=m; hub=k; k+=1
for i in range(0,m,2):
    e.append((i,k)); e.append((k,hub)); k+=1
print("C_6 + legs->outside hub: n=",k," girth =",girth(k,e), " (thread says g_z=6; is plain girth different?)")
# C_4 version
m=4; e=[(i,(i+1)%m) for i in range(m)]
k=m; hub=k; k+=1
for i in range(0,m,2):
    e.append((i,k)); e.append((k,hub)); k+=1
print("C_4 + legs->outside hub: n=",k," girth =",girth(k,e))
# heavy-hex bounded faces: cyclomatic number and face lengths
import sys; sys.path.insert(0,r"c:/Users/ADIB/OneDrive/Desktop/quantum-of-solace")
from pts.heavyhex import HeavyHex
for (W,Ht) in ((3,2),(5,2),(5,3),(7,3)):
    X=HeavyHex(W,Ht)
    n=len(X.vertices); mm=sum(len(a) for a in X.adj.values())//2
    print(f"HeavyHex(W={W},Ht={Ht}): n={n} m={mm} cyclomatic={mm-n+1} girth={girth(n,[(X.index[u],X.index[v]) for u in X.vertices for v in X.adj[u] if X.index[u]<X.index[v]])}")
