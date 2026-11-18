from utils.navegacao import selecionar_carga
from utils.navegacao import atalho
import copy
import streamlit as st
from modules.carregamento import calcular
from modules.validacao import verificar_carga
from modules.hidrostatica import consultar,trim_estatico
from modules.estabilidade import avaliar,gz_adaptada
from visualization.casco import planta
from visualization.cargas import perfil
from components.cargo_drag import drag
from utils.estado import inicializar,aplicar,historico,restaurar_cargas

def render():
    inicializar();st.title("Movimentação de cargas")
    if st.session_state.prova_em_andamento:
        st.info("A condição está congelada durante a prova. Encerre o ensaio para voltar a editar.")
        atalho("ensaio", "Retomar o ensaio ativo")
        return
    st.write("Confira a distribuição das cargas. Para ajustar uma posição, arraste o marcador na planta ou informe as coordenadas. Se as posições já estiverem corretas, continue para o planejamento.")
    barco=st.session_state.barco;cargas=st.session_state.cargas
    if not cargas:
        st.info("Adicione uma carga para ver sua posição e movimentá-la.")
        atalho("cargas", "Cadastrar carga")
        return
    if not barco.get("L_m") or not barco.get("B_m"):
        st.warning("Informe comprimento L e boca B em Embarcação para habilitar arraste gráfico.")
    else:
        try:
            result=drag([{"id":c["id"],"nome":c["nome"],"x_m":c["x_m"],"y_m":c["y_m"]} for c in cargas],barco["L_m"],barco["B_m"])
            if result and result.get("nonce")!=st.session_state.get("ultimo_drag"):
                st.session_state.ultimo_drag=result.get("nonce")
                new=copy.deepcopy(cargas)
                for c in new:
                    if c["id"]==result["id"]:
                        c["x_m"]=round(float(result["x_m"]),8)
                        c["y_m"]=round(float(result["y_m"]),8)
                        verificar_carga(c,barco)
                        aplicar(novas_cargas=new,descricao="Arrastar "+c["nome"])
                        st.rerun()
        except Exception as ex:st.error("Movimento não autorizado: "+str(ex))
    ids=[c["id"] for c in cargas]
    choice=selecionar_carga("Carga a editar", cargas)
    c=next(c for c in cargas if c["id"]==choice)
    with st.form("ajustar_carga"):
        cols=st.columns(4)
        x=cols[0].number_input("X (m)",value=float(c["x_m"]),format="%.5f")
        y=cols[1].number_input("Y (m)",value=float(c["y_m"]),format="%.5f")
        z=cols[2].number_input("Z (m)",value=float(c["z_m"]),format="%.5f")
        massa=cols[3].number_input("Massa (kg)",value=float(c["massa_kg"]),min_value=0.000001,format="%.5f")
        if st.form_submit_button("Aplicar posição e massa"):
            try:
                novo=copy.deepcopy(cargas)
                for item in novo:
                    if item["id"]==choice:item.update(x_m=x,y_m=y,z_m=z,massa_kg=massa);verificar_carga(item,barco)
                aplicar(novas_cargas=novo,descricao="Mover/alterar massa "+c["nome"])
                st.rerun()
            except ValueError as ex:st.error(str(ex))
    try:
        cond=calcular(barco,cargas)
        a,b,c=st.columns(3)
        a.metric("Δ (kg)",f"{cond['deslocamento_kg']:.3f}")
        b.metric("KG (m)",f"{cond['kg_m']:.4f}" if cond['kg_m'] is not None else "Sem CG base")
        c.metric("TCG (m)",f"{cond['tcg_m']:.4f}" if cond['tcg_m'] is not None else "Sem CG base")
        st.plotly_chart(planta(barco,cargas,cond,choice),width="stretch")
        st.plotly_chart(perfil(barco,cargas,cond),width="stretch")
        try:
            hidro=consultar(barco,cond["deslocamento_kg"])
            est=avaliar(barco,cond,hidro)
            trim=trim_estatico(cond,hidro)
            st.write("Hidrostática consultada:",hidro)
            a,b,c=st.columns(3)
            a.metric("KM atualizado (m)",f"{hidro['km_m']:.4f}" if hidro.get('km_m') is not None else "Sem dados")
            b.metric("GM efetivo (m)",f"{est['gm_efetivo_m']:.4f}" if est['gm_efetivo_m'] is not None else "FSM/KG/KM ausente")
            c.metric("Trim linear estimado (m)",f"{trim['variacao_trim_m']:.4f}" if trim['variacao_trim_m'] is not None else "MCT/LCB ausentes")
            if barco.get("gz_curva"):
                import plotly.express as px
                try:
                    gz=gz_adaptada(barco,cond)
                    st.plotly_chart(px.line(gz,x="angulo_graus",y="gz_m",title="GZ adaptada ao KG (somente mesma condição de Δ, TCG=0 e FSM=0)"),width="stretch")
                except ValueError as ex:st.info("GZ não adaptada: "+str(ex))
        except ValueError as ex:st.warning("Hidrostática não atualizada: "+str(ex))
    except ValueError as ex:st.warning(str(ex))
    c1,c2,c3=st.columns(3)
    if c1.button("Desfazer"):historico("undo");st.rerun()
    if c2.button("Refazer"):historico("redo");st.rerun()
    if c3.button("Restaurar condição inicial",disabled=st.session_state.cargas_inicio is None):restaurar_cargas();st.rerun()


render()
