from math import atan,degrees
import pandas as pd
import numpy as np
import streamlit as st
from modules.regressao import processar,sensibilidade
from modules.carregamento import calcular
from modules.hidrostatica import consultar
from modules.erros_experimentais import diagnosticar
from visualization.graficos import ajuste,residuos
from utils.estado import inicializar
from utils.dados import ler,csv_bytes,tabela_para_lista
from utils.ui_importacao import controles_tabela,mapear_campos,aplicar_mapeamento

inicializar();st.title("08 • Processamento experimental de GM e KG")
st.write("Regressão com intercepto: tan θ = a + b·(Σm·d), com GM observado = 1/(Δ·b). KM e momento de superfície livre referem-se à MESMA condição da prova.")
with st.expander("Importar medições reais ou editar manualmente"):
    st.caption("CSV/XLSX/JSON: campos 'momento_kgm', 'tangente', 'estavel' (bool), 'fonte'. Cada linha deve representar leitura com deslocamento constante.")
    up=st.file_uploader("Medições",type=["csv","xlsx","json"],key="up_leituras")
    if up:
        try:
            import hashlib
            uid=hashlib.sha1(up.getvalue()).hexdigest()[:10]
            aba,head,decimal_virgula,sugerido=controles_tabela(up,'ap_medicoes')
            rows=ler(up,'leituras',aba=aba,cabecalho_linha=head,decimal_virgula=decimal_virgula)
            if not rows:raise ValueError('Nenhuma leitura na aba selecionada.')
            st.dataframe(pd.DataFrame(rows).drop(columns=['__linha_origem__'],errors='ignore').head(8),
                         use_container_width=True,hide_index=True)
            if not up.name.lower().endswith('.json'):
                colmap=mapear_campos(rows,'leituras',
                     ['momento_kgm','tangente','estavel','fonte'],
                     ['momento_kgm','tangente'],f'leituras_map_{uid}_{aba}_{head}')
            if st.button("Validar e importar medições (substituir)"):
                if up.name.lower().endswith('.json'):
                    maprows=rows
                else:
                    maprows=aplicar_mapeamento(rows,colmap,['momento_kgm','tangente'])
                clean=tabela_para_lista(maprows,['momento_kgm','tangente'],decimal_virgula=decimal_virgula)
                # Metadados usam as linhas de origem para não perder a ordem.
                if len(clean)!=len(maprows):
                    raise ValueError('Existem linhas com apenas metadados. Remova ou corrija antes de importar.')
                new=[]
                for i,(r,c) in enumerate(zip(maprows,clean),1):
                    if c['momento_kgm'] is None or c['tangente'] is None:
                        raise ValueError(f'Linha {r.get("__linha_origem__",i)}: momento e tangente são obrigatórios.')
                    flag=r.get('estavel')
                    if flag is None:
                        estavel=False
                    else:
                        estavel=str(flag).strip().lower() in ('true','1','sim','yes','verdadeiro')
                    # Na ausência de medição de estabilidade, não declarar leitura estável.
                    new.append({'numero':i,'momento_kgm':c['momento_kgm'],
                                'tangente':c['tangente'],'estavel':estavel,
                                'fonte':r.get('fonte') or 'medicao_importada',
                                'angulo_graus':degrees(atan(c['tangente']))})
                st.session_state.leituras=new
                st.success(f'{len(new)} medições importadas. Sem campo estavel, são marcadas como não estabilizadas.')
        except Exception as ex:st.error('Falha ao importar medições: '+str(ex))
    edit=pd.DataFrame([{k:v for k,v in r.items() if k in ("momento_kgm","tangente","estavel","fonte")} for r in st.session_state.leituras],columns=["momento_kgm","tangente","estavel","fonte"])
    ed=st.data_editor(edit,num_rows="dynamic",use_container_width=True,key="edit_medicoes")
    if st.button("Salvar medições editadas"):
        try:
            new=[]
            for i,r in enumerate(ed.to_dict("records")):
                if pd.isna(r["momento_kgm"]) or pd.isna(r["tangente"]):raise ValueError("Todos os momentos e tangentes devem estar preenchidos")
                tt=float(r["tangente"])
                new.append({"numero":i+1,"momento_kgm":float(r["momento_kgm"]),"tangente":tt,
                            "estavel":r.get("estavel") is True or r.get("estavel")==1,
                            "fonte":r.get("fonte") or "medicao_manual","angulo_graus":degrees(atan(tt))})
            st.session_state.leituras=new;st.success("Leituras salvas")
        except Exception as ex:st.error(str(ex))
try:
    delta=calcular(st.session_state.barco,st.session_state.cargas)["deslocamento_kg"]
except ValueError:delta=None
with st.form("param_reducao"):
    a,b,c=st.columns(3)
    despl=a.text_input("Deslocamento da condição da prova (kg)",value="" if delta is None else str(delta))
    try:
        km_atual=consultar(st.session_state.barco,float(despl))["km_m"] if despl.strip() else None
    except (ValueError, TypeError):km_atual=None
    km=b.text_input("KM dessa condição (m)",value="" if km_atual is None else str(km_atual))
    fsm=c.text_input("FSM efetivo dos tanques (kg·m; zero se inexistente comprovado)",value="" if st.session_state.barco.get("fsm_kgm") is None else str(st.session_state.barco["fsm_kgm"]))
    if st.form_submit_button("Calcular regressão"):
        try:
            d=float(despl)
            if not d>0:raise ValueError("Deslocamento deve ser positivo")
            k=float(km) if km.strip() else None
            f=float(fsm) if fsm.strip() else None
            if f is not None and f<0:raise ValueError("FSM não pode ser negativo")
            r=processar(st.session_state.leituras,d,k,f)
            st.session_state.ultima_regressao=r
            st.session_state.param_regressao={"delta":d,"km":k,"fsm":f}
        except Exception as ex:st.error(str(ex))
if st.session_state.get("param_regressao"):
    par=st.session_state.param_regressao
    try:st.session_state.ultima_regressao=processar(st.session_state.leituras,par["delta"],par["km"],par["fsm"])
    except ValueError:
        st.session_state.ultima_regressao=None
        st.warning("Medições alteradas: regressão anterior invalidada. Corrija dados e calcule novamente.")
if st.session_state.get("ultima_regressao"):
    r=st.session_state.ultima_regressao
    st.caption("Resultados recalculados com as leituras atuais e os últimos parâmetros de redução aplicados. Altere os parâmetros e clique Calcular regressão para confirmá-los.")
    a,b,c,d=st.columns(4)
    a.metric("GM observado (m)",f"{r['gm_observado_m']:.6f}")
    b.metric("KG sólido (m)",f"{r['kg_solido_m']:.6f}" if r["kg_solido_m"] is not None else "Pendente KM/FSM")
    c.metric("R²",f"{r['r2']:.6f}")
    d.metric("n",r["n"])
    st.write(f"**Equação:** tan θ = ({r['a']:.8g}) + ({r['b']:.8g}) × M, onde M em kg·m e b em (kg·m)⁻¹.")
    st.caption(f"Desvio-padrão do estimador da inclinação da reta: {r['stderr_b']:.3g} (kg·m)⁻¹. {r['avaliacao']}. Não é incerteza expandida de GM.")
    st.plotly_chart(ajuste(r),use_container_width=True)
    st.plotly_chart(residuos(r),use_container_width=True)
    st.warning("O KG obtido corresponde à condição ENSAIADA, não ao KG do navio leve. Remoções/adições para condição leve exigem levantamento de pesos e momentos separado.")
if st.session_state.leituras:
    st.subheader("Diagnóstico dos dados")
    warns=diagnosticar(st.session_state.erros,st.session_state.leituras,st.session_state.erros.get("limite_angulo_graus"))
    if warns:st.dataframe(pd.DataFrame(warns,columns=["Diagnóstico","Causa","Verificação","Decisão"]),use_container_width=True)
    else:st.info("Sem alertas automáticos dentro dos critérios fornecidos.")
    st.download_button("Exportar medições CSV",csv_bytes(st.session_state.leituras),file_name="leituras.csv")
with st.expander("Sensibilidade por uma leitura isolada"):
    st.write("Usa GM=m·d·L/(Δ·x), com propagação de erros pequenos, independentes. Não usar x=0, não extrapolar para erros grandes.")
    keys=[("Massa inclinante (kg)","massa"),("Distância medida (m)","dist"),("Deslocamento (kg)","delta"),("Comprimento fio (m)","L"),("Deflexão (m)","x")]
    vals={}
    cols=st.columns(2)
    for i,(label,k) in enumerate(keys):
        vals[k]=cols[i%2].text_input(label,key="sens_v_"+k)
    inc={}
    for i,(label,k) in enumerate(keys):
        inc[k]=cols[i%2].text_input("Incerteza padrão absoluta — "+label,key="sens_i_"+k)
    if st.button("Calcular sensibilidade"):
        try:
            if any(not vals[k] or not inc[k] for _,k in keys):raise ValueError("Preencha medidas e incertezas (0 permitido para incerteza)")
            params={"massa_kg":float(inc["massa"]),"distancia_m":float(inc["dist"]),"deslocamento_kg":float(inc["delta"]),
                    "comprimento_m":float(inc["L"]),"deflexao_m":float(inc["x"])}
            r=sensibilidade(*(float(vals[k]) for _,k in keys),params)
            st.json(r)
        except Exception as ex:st.error(str(ex))
