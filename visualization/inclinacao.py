"""Rotação gráfica de uma secção nominal para ângulo já calculado.
Nunca calcula equilíbrio hidrostático de casco real.
"""
import numpy as np
import plotly.graph_objects as go

def secao(barco, angulo_graus, kg=None, kb=None, km=None):
    B,D=barco.get("B_m"),barco.get("D_m")
    if B is None or D is None:return None
    pts=np.array([[-B/2,0],[B/2,0],[B/2,D],[-B/2,D],[-B/2,0]],dtype=float)
    rad=np.deg2rad(angulo_graus)
    # Rotação visual no sistema Y-Z; Y boreste positivo.
    rot=np.array([[np.cos(rad),-np.sin(rad)],[np.sin(rad),np.cos(rad)]])
    pts=pts@rot.T
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=pts[:,0],y=pts[:,1],mode="lines",fill="toself",name="Seção retangular ilustrativa"))
    for nome,z,color in (("G",kg,"red"),("B (ref.)",kb,"blue"),("M (ref.)",km,"green")):
        if z is not None:
            coord=np.array([0,z])@rot.T
            fig.add_trace(go.Scatter(x=[coord[0]],y=[coord[1]],mode="markers+text",text=[nome],textposition="top right",marker=dict(color=color,size=12),name=nome))
    if barco.get("calado_m") is not None:
        fig.add_hline(y=barco["calado_m"],line_dash="dash",annotation_text="WL de referência — visual")
    fig.update_yaxes(scaleanchor="x",scaleratio=1)
    fig.update_layout(title=f"Seção esquemática rotacionada: {angulo_graus:.3f}° (NÃO hidrostática)",xaxis_title="Y (m)",yaxis_title="Z (m)",height=380)
    return fig
