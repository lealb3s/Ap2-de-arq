"""Persistência por sessão: histórico de edição e log de ensaio separados."""
import copy
import uuid
from datetime import datetime,timezone
import streamlit as st
from .dados import registro_vazio


def inicializar():
    defaults={"barco":registro_vazio(),"cargas":[],"cargas_inicio":None,"undo":[],"redo":[],
              "log_alteracoes":[],"leituras":[],"movimentos":[],"pesos_inicio":None,
              "pendulos":[{"id":"P1","comprimento_m":None},{"id":"P2","comprimento_m":None}],
              "configuracoes":[],"erros":{},"dinamica":None,"dinamica_config":None,
              "prova_offset":{},"prova_em_andamento":False}
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=copy.deepcopy(v)


def snapshot():
    return copy.deepcopy({k:st.session_state[k] for k in ("barco","cargas")})


def aplicar(novo_barco=None, novas_cargas=None, descricao="Alteração"):
    anterior=snapshot()
    st.session_state.undo.append(anterior)
    st.session_state.redo=[]
    if novo_barco is not None:st.session_state.barco=copy.deepcopy(novo_barco)
    if novas_cargas is not None:st.session_state.cargas=copy.deepcopy(novas_cargas)
    st.session_state.log_alteracoes.append({"evento":descricao,"id":str(uuid.uuid4()),
        "instante_utc":datetime.now(timezone.utc).isoformat(),"antes":anterior,"depois":snapshot()})


def historico(acao):
    fonte, destino=("undo","redo") if acao=="undo" else ("redo","undo")
    if not st.session_state[fonte]:return False
    anterior=snapshot()
    st.session_state[destino].append(anterior)
    antigo=st.session_state[fonte].pop()
    st.session_state.barco=antigo["barco"]
    st.session_state.cargas=antigo["cargas"]
    st.session_state.log_alteracoes.append({"evento":acao,"id":str(uuid.uuid4()),
        "instante_utc":datetime.now(timezone.utc).isoformat(),"antes":anterior,"depois":snapshot()})
    return True


def restaurar_cargas():
    if st.session_state.cargas_inicio is None:
        raise ValueError("Salve primeiro uma condição inicial na página 02")
    aplicar(novas_cargas=copy.deepcopy(st.session_state.cargas_inicio),descricao="Restaurar cargas iniciais")


def nova_id():return uuid.uuid4().hex[:10]
