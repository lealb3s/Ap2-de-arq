"""Ilustração em planta, sem alegar calcular uma superfície de carena.

Contorno real importado: x,y; senão retângulo nominal com L e B explícitos.
"""
import plotly.graph_objects as go


def planta(barco,cargas,condicao=None,selecionada=None):
    fig=go.Figure()
    outline=barco.get("casco_contorno",[])
    if len(outline)>=3:
        pts=[(p["x_m"],p["y_m"]) for p in outline]
        legenda="Contorno importado (planta)"
    elif barco.get("L_m") and barco.get("B_m"):
        L,B=barco["L_m"],barco["B_m"]
        pts=[(0,-B/2),(L,-B/2),(L,B/2),(0,B/2)]
        legenda="Retângulo nominal ILUSTRATIVO (não é geometria real)"
    else:
        pts=[]
    if pts:
        xs,ys=zip(*(pts+[pts[0]]))
        fig.add_trace(go.Scatter(x=xs,y=ys,fill="toself",mode="lines",name=legenda,
                                 fillcolor="rgba(65,138,188,.13)",line=dict(color="#0e7490",width=2),hoverinfo="name"))
    for c in cargas:
        color="#ef4444" if c["id"]==selecionada else "#f59e0b"
        fig.add_trace(go.Scatter(x=[c["x_m"]],y=[c["y_m"]],mode="markers+text",text=[c["nome"]],
            textposition="top center",marker=dict(size=14,color=color,symbol="square"),name=c["nome"],
            customdata=[c["id"]],hovertemplate=f"{c['nome']}<br>{c['massa_kg']} kg<br>X=%{{x:.3f}} m, Y=%{{y:.3f}} m<extra></extra>"))
    if condicao and condicao.get("lcg_m") is not None and condicao.get("tcg_m") is not None:
        fig.add_trace(go.Scatter(x=[condicao["lcg_m"]],y=[condicao["tcg_m"]],mode="markers+text",
                                 text=["G (planta)"],textposition="bottom right",marker=dict(color="red",size=12,symbol="cross"),name="G"))
    fig.add_hline(y=0,line_dash="dot",line_color="gray",annotation_text="Linha de centro")
    fig.update_layout(title="Vista em planta — Y positivo: boreste",xaxis_title="X longitudinal (m)",yaxis_title="Y transversal (m)",
                      legend=dict(orientation="h"),margin=dict(l=20,r=20,t=60,b=30),height=440)
    fig.update_yaxes(scaleanchor="x",scaleratio=1)
    return fig
