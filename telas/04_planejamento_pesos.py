from utils.dados import numero_digitado
import pandas as pd
import streamlit as st
from modules.carregamento import calcular
from modules.hidrostatica import consultar
from modules.estabilidade import avaliar
from modules.movimentacao_pesos import comparar
from utils.estado import inicializar

inicializar();st.title("Planejamento de pesos")
st.write("Etapa opcional. Para comparar alternativas, informe pelo menos três configurações de pesos. Se os pesos já estiverem definidos, siga para Pêndulos.")
try:
    c=calcular(st.session_state.barco,st.session_state.cargas)
    h=consultar(st.session_state.barco,c["deslocamento_kg"])
    e=avaliar(st.session_state.barco,c,h)
    delta=c["deslocamento_kg"];gm=e["gm_efetivo_m"]
    st.caption(f"Δ = {delta:g} kg; GM efetivo = {gm if gm is not None else 'desconhecido'} m")
except ValueError as err:
    st.warning("Sem hidrostática adequada: "+str(err));delta=gm=None
st.caption("Sem limites, a configuração não pode ser recomendada. Informar limites NÃO significa que estes sejam normas da IMO.")
limites = st.session_state.get("limites_planejamento", {})
a,b,c,d=st.columns(4)
lim_ang=a.text_input("Limite angular adotado (°)",value=limites.get("lim_ang",""), key="lim_ang")
max_p=b.text_input("Altura disponível para pêndulos (m)",value=limites.get("max_p",""), key="max_p")
res=c.text_input("Resolução da régua (m)",value=limites.get("res_p",""), key="res_p")
lim_massa=d.text_input("Limite por peso (kg)",value=limites.get("lim_massa",""), key="lim_massa")
col=["massa_kg","quantidade","distancia_m","pendulo_m"]
if not st.session_state.configuracoes:
    st.session_state.configuracoes=[dict.fromkeys(col) for _ in range(3)]
st.subheader("Três alternativas")
df=st.data_editor(pd.DataFrame(st.session_state.configuracoes,columns=col,dtype=float),num_rows="dynamic",width="stretch")
if st.button("Comparar configurações",type="primary"):
    try:
        configs=[]
        for item in df.to_dict("records"):
            if any(pd.isna(item.get(k)) or item.get(k) is None for k in col):raise ValueError("Preencha massa, quantidade, distância e pêndulo em cada linha")
            v={k:numero_digitado(item[k]) for k in col}
            if any(v[k]<=0 for k in col):raise ValueError("Valores devem ser positivos")
            if not v["quantidade"].is_integer():raise ValueError("Quantidade precisa ser inteira")
            v["quantidade"]=int(v["quantidade"]);configs.append(v)
        if len(configs)<3:raise ValueError("Cadastre pelo menos 3 configurações")
        ang=numero_digitado(lim_ang) if lim_ang.strip() else None
        altura=numero_digitado(max_p) if max_p.strip() else None
        resol=numero_digitado(res) if res.strip() else None
        massa_max=numero_digitado(lim_massa) if lim_massa.strip() else None
        if any(v is not None and v <= 0 for v in (ang, altura, resol, massa_max)):
            raise ValueError("Os limites de comparação e a resolução devem ser positivos.")
        tabela=comparar(configs,delta,gm,st.session_state.barco.get("B_m"),altura,ang,resol)
        if massa_max is None:
            for r in tabela:
                r["Pendências / violações"]+="; Limite de massa por peso não informado"
                r["Viabilidade"]="Não comprovada"
        else:
            for i,r in enumerate(tabela):
                if configs[i]["massa_kg"]>massa_max:
                    r["Pendências / violações"]+="; Massa individual supera limite informado"
                    r["Viabilidade"]="Não comprovada"
        st.session_state.limites_planejamento = dict(lim_ang=lim_ang, max_p=max_p, res_p=res, lim_massa=lim_massa)
        st.session_state.configuracoes=configs
        st.session_state.tabela_planejamento=tabela
    except Exception as err:st.error(str(err))
if st.session_state.get("tabela_planejamento"):
    tabela=st.session_state.tabela_planejamento
    st.dataframe(pd.DataFrame(tabela),width="stretch",hide_index=True)
    viaveis=[(i,r) for i,r in enumerate(tabela) if r["Viabilidade"].startswith("Atende") and r["Resolução angular (°)"] and r["Inclinação prevista (°)"]]
    if viaveis:
        # Heurística EXPLÍCITA, não critério IMO: maior sinal/résolução angular; empate menor número de pesos.
        i,v=max(viaveis,key=lambda p:(abs(p[1]["Inclinação prevista (°)"])/p[1]["Resolução angular (°)"],-p[1]["Quantidade"]))
        st.success(f"Sugestão acadêmica: configuração {i+1}; maior razão inclinação/resolução angular dentre as que respeitam todos os limites fornecidos. Empate: menos pesos.")
    else: st.warning("Sem recomendação: não há configuração cuja viabilidade esteja comprovada com os dados e limites informados.")
    st.info("A pontuação não avalia resistência da estrutura, segurança de pessoas, forças de atrito, acesso, amarras, vento nem aprovação de autoridade. Verificar estes itens separadamente.")
