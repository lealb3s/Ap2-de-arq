import copy
from datetime import datetime, timezone
from math import atan, degrees, radians, tan
import numpy as np
import pandas as pd
import streamlit as st
from modules.carregamento import calcular
from modules.hidrostatica import consultar
from modules.estabilidade import avaliar
from modules.prova_inclinacao import equilibrio_angulo,avancar_dinamica,estabilizado,G0
from modules.erros_experimentais import perturbar
from utils.estado import inicializar
from utils.dados import csv_bytes
from visualization.inclinacao import secao
from visualization.pendulos import desenhar

inicializar();st.title("06 • Execução virtual da prova de inclinação")
st.write("As cargas inclinantes devem ser cadastradas na página 02. Neste modo só se movimenta Y; massa, X e Z permanecem inalterados. O histórico de medições permanece separado do carregamento original.")
try:
    b=st.session_state.barco;cargas=st.session_state.cargas
    cond=calcular(b,cargas);h=consultar(b,cond["deslocamento_kg"]);e=avaliar(b,cond,h)
    if e["gm_efetivo_m"] is None or e["gm_efetivo_m"]<=0:raise ValueError("Exige KM, KG, superfície livre explícita e GM efetivo > 0")
    if cond["tcg_m"] is None or not np.isclose(cond["tcg_m"],0,rtol=0,atol=1e-9):
        raise ValueError("Para este modelo virtual, a condição inicial deve ter TCG=0. Corrija adernamento inicial ou use dados reais na página 08")
    pend=st.session_state.pendulos
    if len(pend)<2 or any(p["comprimento_m"] is None or p["comprimento_m"]<=0 for p in pend):raise ValueError("Configure pelo menos dois pêndulos na página 05")
    m=cond["deslocamento_kg"];gm=e["gm_efetivo_m"]
except ValueError as ex:st.error("Falta dado obrigatório: "+str(ex));st.stop()

if not st.session_state.prova_em_andamento:
    st.info(f"Condição inicial: Δ = {m:.3f} kg, GM efetivo = {gm:.5f} m. O instrumento registra deflexão relativa ao zero inicial.")
    if st.button("Iniciar prova e congelar condição de carregamento",type="primary"):
        st.session_state.pesos_inicio=copy.deepcopy(cargas)
        st.session_state.prova_y={c["id"]:c["y_m"] for c in cargas}
        st.session_state.leituras=[];st.session_state.movimentos=[];st.session_state.prova_em_andamento=True
        st.session_state.dinamica={"phi_rad":0,"omega_rad_s":0,"tempo_s":0}
        st.rerun()
    st.stop()

ref=st.session_state.pesos_inicio
curr=st.session_state.prova_y
momento=sum(c["massa_kg"]*(curr[c["id"]]-c["y_m"]) for c in ref)
vento=float(st.session_state.erros.get("momento_vento_Nm",0))
mom_real=momento+vento/G0
teorico=equilibrio_angulo(mom_real,m,gm)
col1,col2,col3=st.columns(3)
col1.metric("Momento peso m·d (kg·m)",f"{momento:.6g}")
col2.metric("Equilíbrio previsto (°)",f"{teorico:.5f}")
col3.metric("Leituras registradas",len(st.session_state.leituras))

with st.expander("Modelo transitório opcional — somente com parâmetros fornecidos"):
    ativo=st.checkbox("Habilitar modelo dinâmico linear de rolamento",value=st.session_state.dinamica_config is not None)
    if ativo:
        with st.form("dinamica_configuracao"):
            a=st.text_input("Inércia efetiva Ixx (kg·m²), incluindo efeitos relevantes",value=str((st.session_state.dinamica_config or {}).get("I", "")))
            c=st.text_input("Amortecimento linear c (N·m·s/rad)",value=str((st.session_state.dinamica_config or {}).get("c", "")))
            t1=st.text_input("Tolerância angular de estabilização (°)",value=str((st.session_state.dinamica_config or {}).get("tol_angulo", "")))
            t2=st.text_input("Tolerância de velocidade (°/s)",value=str((st.session_state.dinamica_config or {}).get("tol_vel", "")))
            if st.form_submit_button("Aplicar parâmetros dinâmicos"):
                try:
                    conf={"I":float(a),"c":float(c),"tol_angulo":float(t1),"tol_vel":float(t2)}
                    if conf["I"]<=0 or conf["c"]<0 or conf["tol_angulo"]<=0 or conf["tol_vel"]<=0:raise ValueError("Parâmetros fora da faixa")
                    st.session_state.dinamica_config=conf;st.success("Modelo dinâmico ativado")
                except Exception as ex:st.error(str(ex))
    else:st.session_state.dinamica_config=None

st.subheader("Mover peso na transversal")
id=st.selectbox("Peso a movimentar",[c["id"] for c in ref],format_func=lambda x:next(c["nome"] for c in ref if c["id"]==x))
q=next(c for c in ref if c["id"]==id)
with st.form("form_mover"):
    y=st.number_input("Nova coordenada Y (m)",value=float(curr[id]),format="%.6f")
    if st.form_submit_button("Movimentar o peso"):
        if b.get("B_m") is not None and abs(y)>b["B_m"]/2:
            st.error("Fora da boca nominal declarada")
        elif q.get("larg_m") is not None and b.get("B_m") is not None and abs(y)+q["larg_m"]/2>b["B_m"]/2:
            st.error("As dimensões da carga não cabem na boca declarada")
        else:
            antes=curr[id]
            st.session_state.prova_y[id]=y
            st.session_state.movimentos.append({"id_carga":id,"nome":q["nome"],"y_anterior_m":antes,"y_novo_m":y,
                "momento_kgm":sum(c["massa_kg"]*(st.session_state.prova_y[c["id"]]-c["y_m"]) for c in ref),
                "instante":datetime.now(timezone.utc).isoformat()})
            st.rerun()

conf=st.session_state.dinamica_config
if conf:
    state=st.session_state.dinamica
    dyn_eq=degrees(mom_real/(m*gm))
    a,b=st.columns(2)
    a.metric("Ângulo dinâmico (°)",f"{degrees(state['phi_rad']):.5f}")
    b.metric("Velocidade angular (°/s)",f"{degrees(state['omega_rad_s']):.5f}")
    dt=st.number_input("Avançar tempo de simulação (s)",min_value=0.01,value=1.,step=0.25)
    if st.button("Avançar dinâmica"):
        st.session_state.dinamica=avancar_dinamica(state,mom_real,m,gm,conf["I"],conf["c"],dt)
        st.rerun()
    ok=estabilizado(state,mom_real,m,gm,conf["tol_angulo"],conf["tol_vel"])
    shown=degrees(state["phi_rad"])
    if ok:st.success("Equilíbrio atingido nas tolerâncias INFORMADAS para o modelo dinâmico")
    else:st.warning("Ainda há movimento transitório relevante: registro estabilizado bloqueado")
    st.caption("Equilíbrio dinâmico linear φ≈M/(Δ·GM) rad. A exibição do ângulo por atan é a aproximação metacêntrica estática; para ângulos grandes nenhum dos dois substitui GZ.")
else:
    ok=True;shown=teorico
    st.info("Modo QUASE ESTÁTICO IDEAL: não há tempo nem oscilações calculados. Uma leitura pode ser registrada como 'equilíbrio teórico', nunca como estabilização dinâmica observada.")

vis=secao(b,shown,cond["kg_m"],h.get("kb_m"),h.get("km_m"))
if vis:st.plotly_chart(vis,use_container_width=True)
st.plotly_chart(desenhar(pend,{p["id"]:p["comprimento_m"]*tan(radians(shown)) for p in pend}),use_container_width=True)
st.write("**Momento inclinado:** inclua influências externas na página 07; se o limite angular admissível for excedido, interrompa o ensaio.")
limite=st.session_state.erros.get("limite_angulo_graus")
limite_ok=limite is not None and abs(shown)<=limite and abs(teorico)<=limite
if limite is None:st.warning("Informe o limite angular de projeto na página 07 para liberar o registro. A IMO recomenda 1° a 4° por bordo em sua aplicação, sujeito à Administração.")
elif not limite_ok:st.error(f"Ângulo excede o limite de {limite}° informado: registro bloqueado.")
if st.button("Registrar condição experimental simulada",disabled=not (ok and limite_ok),type="primary"):
    rng=np.random.default_rng(2026+len(st.session_state.leituras)) # reprodutível
    estimado,leituras=perturbar(momento,pend,shown,st.session_state.erros,rng)
    tangentes=[p["deflexao_m"]/p["comprimento_m"] for p in leituras]
    theta=degrees(atan(float(np.mean(tangentes))))
    angles=[degrees(atan(t)) for t in tangentes]
    item={"numero":len(st.session_state.leituras)+1,"momento_kgm":estimado,"momento_real_kgm":momento,
          "angulo_graus":theta,"tangente":float(np.mean(tangentes)),"desacordo_pendulos_graus":max(angles)-min(angles),
          "estavel":True,"fonte":"simulacao_dinamica" if conf else "equilibrio_teorico",
          "instante":datetime.now(timezone.utc).isoformat(),"pendulos":leituras,
          "posicoes_y":copy.deepcopy(st.session_state.prova_y)}
    st.session_state.leituras.append(item)
    st.success(f"Condição {item['numero']} registrada (resultado simulado)")
if st.button("Retornar pesos às posições iniciais"):
    st.session_state.prova_y={c["id"]:c["y_m"] for c in ref};st.session_state.movimentos.append({"acao":"Retorno a zero"});st.rerun()
st.subheader("Histórico registrado")
if st.session_state.leituras:st.dataframe(pd.DataFrame([{k:v for k,v in row.items() if k not in ("pendulos","posicoes_y")} for row in st.session_state.leituras]),use_container_width=True)
if st.session_state.movimentos:st.dataframe(pd.DataFrame(st.session_state.movimentos),use_container_width=True)
if st.button("Encerrar prova (manter leituras)"):
    st.session_state.prova_em_andamento=False;st.rerun()
