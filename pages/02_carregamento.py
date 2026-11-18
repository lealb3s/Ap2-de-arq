import copy
import pandas as pd
import streamlit as st
from modules.carregamento import calcular, sugestao_xyz
from modules.validacao import verificar_carga
from modules.hidrostatica import consultar, trim_estatico
from modules.estabilidade import avaliar, gz_adaptada
from utils.estado import inicializar, aplicar, historico, restaurar_cargas, nova_id
from utils.dados import ler, tabela_para_lista, COLUNAS_CARGAS, csv_bytes
from visualization.casco import planta
from visualization.cargas import perfil

inicializar(); st.title("02 • Cadastro e distribuição das cargas")
st.caption("Modo carregamento: adicionar/remover altera Δ; reposicionar mantém Δ. As coordenadas são do CG individual, não de um vértice do objeto.")
if st.session_state.prova_em_andamento:st.error("Prova ativa: encerre-a na página 06 para mudar a condição de carregamento.");st.stop()
with st.expander("Importação de cargas AP1.2"):
    f=st.file_uploader("Importar cargas (CSV/XLSX/JSON)",type=["csv","xlsx","json"])
    if f and st.button("Substituir cargas pela importação"):
        try:
            cargas=tabela_para_lista(ler(f,"cargas"),COLUNAS_CARGAS)
            for c in cargas:
                if not c["id"]:c["id"]=nova_id()
                verificar_carga(c,st.session_state.barco)
            if len({c["id"] for c in cargas})!=len(cargas):raise ValueError("IDs duplicados no arquivo")
            aplicar(novas_cargas=cargas,descricao="Importar cargas")
            st.session_state.cargas_inicio=copy.deepcopy(cargas)
            st.success("Cargas importadas")
        except Exception as e:st.error(str(e))
with st.expander("Adicionar nova carga",expanded=True):
    with st.form("add_carga"):
        nome=st.text_input("Nome");categoria=st.text_input("Categoria",value="Carga")
        massastr=st.text_input("Massa (kg)")
        a,b,c=st.columns(3)
        xstr=a.text_input("X (m)");ystr=b.text_input("Y (m)");zstr=c.text_input("Z (m)")
        sugerir=st.checkbox("Usar posição central apenas como sugestão editável")
        d1,d2,d3=st.columns(3)
        comp=d1.text_input("Comprimento da carga (m; opcional)");larg=d2.text_input("Largura (m; opcional)");alt=d3.text_input("Altura (m; opcional)")
        if st.form_submit_button("Adicionar carga"):
            try:
                sug=sugestao_xyz(st.session_state.barco) if sugerir else {}
                new={"id":nova_id(),"nome":nome,"categoria":categoria,"massa_kg":float(massastr),
                    "x_m":float(xstr) if xstr else sug.get("x_m"),
                    "y_m":float(ystr) if ystr else sug.get("y_m"),
                    "z_m":float(zstr) if zstr else sug.get("z_m"),
                    "comp_m":float(comp) if comp else None,"larg_m":float(larg) if larg else None,"alt_m":float(alt) if alt else None,
                    "posicao_sugerida":bool(sugerir)}
                verificar_carga(new,st.session_state.barco)
                cargas=copy.deepcopy(st.session_state.cargas)+[new]
                aplicar(novas_cargas=cargas,descricao="Adicionar "+nome)
                st.success("Carga adicionada")
            except Exception as e:st.error(str(e))
if st.session_state.cargas:
    st.subheader("Editar massas, posições e dimensões")
    df=pd.DataFrame(st.session_state.cargas)
    edit=st.data_editor(df,num_rows="fixed",disabled=["id"],use_container_width=True,key="edit_cargas")
    a,b,c=st.columns(3)
    if a.button("Aplicar alterações na tabela"):
        try:
            cargas=edit.to_dict("records")
            for c in cargas:
                for k in ("massa_kg","x_m","y_m","z_m","comp_m","larg_m","alt_m"):
                    if pd.isna(c.get(k)):c[k]=None
                verificar_carga(c,st.session_state.barco)
            aplicar(novas_cargas=cargas,descricao="Editar cargas")
            st.success("Atualizado")
        except Exception as e:st.error(str(e))
    nomeescolhido=b.selectbox("Selecione uma carga",[c["id"] for c in st.session_state.cargas],format_func=lambda z:next(c["nome"] for c in st.session_state.cargas if c["id"]==z))
    if c.button("Duplicar carga selecionada"):
        cargas=copy.deepcopy(st.session_state.cargas)
        item=next(c for c in cargas if c["id"]==nomeescolhido).copy()
        item["id"]=nova_id();item["nome"]+=" (cópia)"
        cargas.append(item)
        aplicar(novas_cargas=cargas,descricao="Duplicar carga")
        st.success("Cópia criada — Δ aumentou")
    if st.button("Remover carga selecionada"):
        aplicar(novas_cargas=[c for c in st.session_state.cargas if c["id"]!=nomeescolhido],descricao="Remover carga")
        st.success("Carga removida — Δ diminuiu")
buttons=st.columns(4)
if buttons[0].button("Desfazer"):historico("undo");st.rerun()
if buttons[1].button("Refazer"):historico("redo");st.rerun()
if buttons[2].button("Salvar condição inicial"):
    st.session_state.cargas_inicio=copy.deepcopy(st.session_state.cargas);st.success("Condição inicial armazenada")
if buttons[3].button("Restaurar condição inicial",disabled=st.session_state.cargas_inicio is None):
    restaurar_cargas();st.rerun()
try:
    cond=calcular(st.session_state.barco,st.session_state.cargas)
    a,b,c,d=st.columns(4)
    a.metric("Δ (kg)",f"{cond['deslocamento_kg']:.3f}")
    b.metric("LCG (m)","—" if cond["lcg_m"] is None else f"{cond['lcg_m']:.4f}")
    c.metric("TCG (m)","—" if cond["tcg_m"] is None else f"{cond['tcg_m']:.4f}")
    d.metric("KG (m)","—" if cond["kg_m"] is None else f"{cond['kg_m']:.4f}")
    st.plotly_chart(planta(st.session_state.barco,st.session_state.cargas,cond),use_container_width=True)
    st.plotly_chart(perfil(st.session_state.barco,st.session_state.cargas,cond),use_container_width=True)
    try:
        h=consultar(st.session_state.barco,cond["deslocamento_kg"])
        e=avaliar(st.session_state.barco,cond,h); tr=trim_estatico(cond,h)
        st.write("**Estado hidrostático**",{**h,**e,**tr})
    except ValueError as ex:st.warning(f"Sem estado hidrostático aplicável: {ex}")
    if st.session_state.barco.get("gz_curva"):
        import plotly.express as px
        try:
            gz=gz_adaptada(st.session_state.barco,cond)
            st.plotly_chart(px.line(pd.DataFrame(gz),x="angulo_graus",y="gz_m",title="GZ adaptada ao KG (mesmo deslocamento, TCG=0, FSM=0)"),use_container_width=True)
        except ValueError as ex:st.info("Curva GZ não adaptada: "+str(ex))
except ValueError as ex:st.warning(str(ex))
st.download_button("Exportar cargas CSV",csv_bytes(st.session_state.cargas),file_name="cargas.csv")
