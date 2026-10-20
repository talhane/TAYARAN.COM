import numpy as np, math, struct

def naca_z(x, code):
    m=int(code[0])/100; p=int(code[1])/10; t=int(code[2:])/100
    yt=5*t*(0.2969*np.sqrt(np.maximum(x,0))-0.1260*x-0.3516*x**2+0.2843*x**3-0.1015*x**4)
    yc=np.zeros_like(x); dy=np.zeros_like(x)
    if m and p:
        a=x<p; yc[a]=m/p**2*(2*p*x[a]-x[a]**2); dy[a]=2*m/p**2*(p-x[a]); b=~a; yc[b]=m/(1-p)**2*((1-2*p)+2*p*x[b]-x[b]**2); dy[b]=2*m/(1-p)**2*(p-x[b])
    th=np.arctan(dy); xu=x-yt*np.sin(th); zu=yc+yt*np.cos(th); xl=x+yt*np.sin(th); zl=yc-yt*np.cos(th)
    return xu,zu,xl,zl

def build_wing(code='0012',span=4.,chord=1.,nx=50,ny=32):
    x=np.linspace(0,1,nx); y=np.linspace(-span/2,span/2,ny); X=np.zeros((ny,nx*2)); Y=np.zeros_like(X); Z=np.zeros_like(X)
    xu,zu,xl,zl=naca_z(x,code)
    for j,yy in enumerate(y):
        taper=1-0.15*abs(yy)/(span/2); c=chord*taper
        X[j,:nx]=xu*c; X[j,nx:]=xl[::-1]*c
        Y[j,:nx]=yy; Y[j,nx:]=yy
        Z[j,:nx]=zu*c; Z[j,nx:]=zl[::-1]*c
    return X,Y,Z

def wing_estimates(span,chord,speed,alpha,rho,code):
    S=span*chord*0.925; AR=span**2/S; q=0.5*rho*speed**2
    cl=max(-0.8,min(1.35,0.1*alpha+int(code[0])*0.03))
    cd=0.012+cl**2/(math.pi*AR*0.85); lift=q*S*cl; drag=q*S*cd
    return {'Area ref. (m²)':f'{S:.3f}','Aspect ratio':f'{AR:.2f}','q (Pa)':f'{q:.1f}','CL (stima)':f'{cl:.3f}','CD (stima)':f'{cd:.4f}','Lift (N)':f'{lift:.1f}','Drag (N)':f'{drag:.1f}','L/D':f'{lift/drag:.2f}' if drag else '—'}

def stl_bytes(X,Y,Z):
    ny,nx=X.shape; tris=[]
    for j in range(ny-1):
        for i in range(nx-1):
            p=[(X[j,i],Y[j,i],Z[j,i]),(X[j,i+1],Y[j,i+1],Z[j,i+1]),(X[j+1,i],Y[j+1,i],Z[j+1,i]),(X[j+1,i+1],Y[j+1,i+1],Z[j+1,i+1])]
            tris.extend([(p[0],p[1],p[2]),(p[1],p[3],p[2])])
    out=bytearray(b'Engineering Academy educational wing STL'.ljust(80,b' ')); out.extend(struct.pack('<I',len(tris)))
    for tri in tris:
        a,b,c=[np.array(q,dtype=float) for q in tri]; n=np.cross(b-a,c-a); norm=np.linalg.norm(n); n=n/norm if norm else n
        out.extend(struct.pack('<12fH',*(list(n)+list(a)+list(b)+list(c)),0))
    return bytes(out)
