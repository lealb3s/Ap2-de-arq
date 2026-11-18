import pandas as pd
import streamlit as st
from modules.pendulos import comparar,deflexao,angulo
from utils.estado import inicializar
from visualization.pendulos import desenhar

inicializar();st.title("05 • Dimensionamento e comparação dos pêndulos")
st.write("Mínimo de dois instrumentos, com posições/leituras independentes. As expressões tan(θ)=x/L pressupõem equilíbrio estático do fio.")
with st.form("pendulo_form"):
    q=st.number_input("Quantidade de pêndulos",min_value=2,max_value=6,value=max(2,len(st.session_state.pendulos)))
    inputs=[]
    for i in range(q):
        known=st.session_state.pendulos[i]["comprimento_m"] if i<len(st.session_state.pendulos) else None
        inputs.append(st.text_input(f"Pêndulo {i+1} — comprimento L (m)",value="" if known is None else str(known),key=f"plen_{i}"))
    res=st.text_input("Resolução linear da escala (m)",key="pend_res")
    ang=st.text_input("Ângulo previsto para comparação (graus; opcional)",key="pend_ang")
    max_alt=st.text_input("Altura disponível (m; opcional)",key="pend_alt")
    if st.form_submit_button("Validar e salvar instrumentos"):
        try:
            pend=[{"id":f"P{i+1}","comprimento_m":float(v)} for i,v in enumerate(inputs)]
            if any(p["comprimento_m"]<=0 for p in pend):raise ValueError("Todos os comprimentos devem ser >0")
            if max_alt.strip() and any(p["comprimento_m"]>float(max_alt) for p in pend):raise ValueError("Comprimento maior que altura disponível")
            st.session_state.pendulos=pend
            st.success("Pêndulos registrados")
        except Exception as ex:st.error(str(ex))
pend=st.session_state.pendulos
if all(p["comprimento_m"] for p in pend):
    if st.session_state.get("pend_res"):
        try:
            tab=comparar([p["comprimento_m"] for p in pend],float(st.session_state.pend_res),float(st.session_state.pend_ang) if st.session_state.pend_ang else None)
            st.dataframe(pd.DataFrame(tab),use_container_width=True,hide_index=True)
        except ValueError as e:st.error(str(e))
    st.plotly_chart(desenhar(pend,{p["id"]:deflexao(p["comprimento_m"],float(st.session_state.pend_ang)) if st.session_state.get("pend_ang") else 0 for p in pend}),use_container_width=True)
st.subheader("Comparar três comprimentos candidatos")
with st.form("comp_pend"):
    cs=st.columns(3)
    compr=[cs[i].text_input(f"Candidato {i+1} (m)",key=f"cpen{i}") for i in range(3)]
    resolu=st.text_input("Resolução de régua para candidatos (m)",key="cpend_res")
    a=st.text_input("Inclinação para avaliar deflexão (°)",key="cpend_angle")
    if st.form_submit_button("Comparar três comprimentos"):
        try:
            if any(not v for v in compr) or not resolu or not a:raise ValueError("Preencha todos os campos")
            result=comparar([float(x) for x in compr],float(resolu),float(a))
            st.dataframe(pd.DataFrame(result),use_container_width=True,hide_index=True)
            st.info("Quanto maior L, menor resolução angular geométrica para a mesma régua; mas maior espaço e potencial de interferência dinâmica. Não é sinônimo de precisão total do ensaio.")
        except ValueError as ex:st.error(str(ex))
