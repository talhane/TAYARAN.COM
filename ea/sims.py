import numpy as np, math
import plotly.graph_objects as go

def projectile_plot(v,ang,h):
    g=9.81; a=math.radians(ang); vx=v*math.cos(a); vy=v*math.sin(a); tf=(vy+math.sqrt(vy**2+2*g*h))/g; t=np.linspace(0,tf,180); x=vx*t; y=h+vy*t-.5*g*t**2
    fig=go.Figure(go.Scatter(x=x,y=np.maximum(y,0),mode='lines',name='Trajectory')); fig.update_layout(xaxis_title='x (m)',yaxis_title='y (m)',height=440)
    return fig, {'Tempo di volo (s)':round(tf,2),'Gittata (m)':round(x[-1],2),'Altezza massima (m)':round(h+vy**2/(2*g),2)}
def spring_plot(m,k,x0):
    w=math.sqrt(k/m); t=np.linspace(0,10,600); x=x0*np.cos(w*t); fig=go.Figure(go.Scatter(x=t,y=x,mode='lines')); fig.update_layout(xaxis_title='t (s)',yaxis_title='x (m)',height=440); return fig
def venturi_plot(d1,d2,q,rho):
    a1=math.pi*d1**2/4; a2=math.pi*d2**2/4; v1=q/a1; v2=q/a2; dp=.5*rho*(v2*v2-v1*v1)
    fig=go.Figure(go.Scatter(x=[0,1,2,3,4],y=[d1,d1,d2,d1,d1],mode='lines+markers',name='Diametro')); fig.update_layout(xaxis_title='Posizione (arbitraria)',yaxis_title='Diametro (m)',height=380)
    return fig, {'v₁ (m/s)':round(v1,3),'v₂ (m/s)':round(v2,3),'p₁−p₂ ideale (Pa)':round(dp,2)}
def moody_plot(re,rough):
    Re=np.logspace(3,8,200); fig=go.Figure()
    for eps in [0,.0001,.001,.01,.05]:
        f=np.array([64/r if r<2300 else 0.25/(math.log10(eps/3.7+5.74/(r**.9))**2) for r in Re]); fig.add_trace(go.Scatter(x=Re,y=f,mode='lines',name=f'ε/D={eps:g}'))
    f=64/re if re<2300 else 0.25/(math.log10(rough/3.7+5.74/(re**.9))**2)
    fig.add_trace(go.Scatter(x=[re],y=[f],mode='markers',name='Punto scelto',marker=dict(size=11))); fig.update_xaxes(type='log'); fig.update_yaxes(type='log'); fig.update_layout(xaxis_title='Reynolds',yaxis_title='Darcy friction factor',height=480); return fig,f
def cylinder_plot(u):
    th=np.linspace(0,2*np.pi,100); r=1-2*np.sin(th)**2; fig=go.Figure(); fig.add_trace(go.Scatter(x=np.cos(th),y=np.sin(th),fill='toself',name='Cylinder'))
    for y in np.linspace(-2.5,2.5,13):
        xx=np.linspace(-4,4,200); yy=np.full_like(xx,y); mask=xx**2+yy**2>1.05**2; fig.add_trace(go.Scatter(x=xx[mask],y=yy[mask],mode='lines',line=dict(width=1),showlegend=False,hoverinfo='skip'))
    fig.update_yaxes(scaleanchor='x',scaleratio=1); fig.update_layout(xaxis_title='x/R',yaxis_title='y/R',height=460); return fig
def airfoil_plot(alpha):
    a=np.linspace(-10,20,100); cl=np.clip(0.1*(a+2),-0.8,1.35); cd=.012+.018*cl**2; nowcl=max(-.8,min(1.35,.1*(alpha+2))); nowcd=.012+.018*nowcl**2
    fig=go.Figure(); fig.add_trace(go.Scatter(x=cd,y=cl,mode='lines',name='Polar')); fig.add_trace(go.Scatter(x=[nowcd],y=[nowcl],mode='markers',name='Selected angle',marker=dict(size=12))); fig.update_layout(xaxis_title='CD',yaxis_title='CL',height=440); return fig
