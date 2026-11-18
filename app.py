"""Simulador independente de prova de inclinação — Streamlit Community Cloud."""
import streamlit as st
from utils.estado import inicializar
from modules.carregamento import calcular
from modules.hidrostatica import consultar
from modules.estabilidade import avaliar

st.set_page_config(page_title="Prova de Inclinação | Engenharia Naval",page_icon="⚓",layout="wide",initial_sidebar_state="expanded")
inicializar()
st.title("⚓ Simulador de prova de inclinação")
st.caption("Engenharia Naval • dados próprios ou resultados importados de AP1.1 / AP1.2 / AP1.3 • SI (kg, m, graus)")
st.info("Aplicativo acadêmico de planejamento e redução de ensaio. Não é certificação de estabilidade nem substitui prova supervisionada. Resultados dependem dos dados de entrada, da documentação do casco e das hipóteses declaradas.")
st.markdown("### Fluxo de trabalho")
st.markdown("**Embarcação → Carregamento → Movimentação → Planejamento → Pêndulos → Ensaio → Erros → Processamento → Relatório.** Use o menu lateral para navegar entre as páginas.")
try:
    cond=calcular(st.session_state.barco,st.session_state.cargas)
    c1,c2,c3=st.columns(3)
    c1.metric("Deslocamento (kg)",f"{cond['deslocamento_kg']:,.3f}")
    c2.metric("KG de carregamento (m)",f"{cond['kg_m']:.4f}" if cond['kg_m'] is not None else "Não calculável")
    c3.metric("TCG (m)",f"{cond['tcg_m']:.4f}" if cond['tcg_m'] is not None else "Não calculável")
    try:
        hidro=consultar(st.session_state.barco,cond["deslocamento_kg"])
        est=avaliar(st.session_state.barco,cond,hidro)
        st.success(f"Fonte KM: {hidro['metodo']}. GM efetivo: " + (f"{est['gm_efetivo_m']:.4f} m" if est['gm_efetivo_m'] is not None else "indeterminado (KG, KM ou FSM ausente)"))
    except ValueError as ex:st.warning(f"Hidrostática pendente: {ex}")
except ValueError as ex:st.warning(f"Carregamento pendente: {ex}")
st.divider()
st.markdown("**Convenção adotada:** X longitudinal da origem escolhida para a proa; Y positivo para boreste; Z positivo acima da linha base. A origem e as cotas reais precisam ser coerentes com os dados importados.")
st.markdown("**Modos:** carregamento permite alterar massa e CG; prova mantém deslocamento e movimenta apenas pesos existentes em Y. Provas virtuais são explicitamente identificadas como tais.")
st.markdown("**Documentação:** consulte `REFERENCIAS.md` e `README.md` no pacote do projeto.")
